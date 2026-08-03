import os
from pathlib import Path
from typing import Optional, Union
import json

from swc_slack.messaging.write import send_message_to_user
from swc_slack.utils import get_client
from slack_sdk import WebClient

# Default values used to seed a brand-new config file. Override via env vars
# (SLACK_BOT_TOKEN_KEY / SLACK_BOT_CHANNEL_ID) or an explicit config file for
# any other Slack workspace/channel.
DEFAULT_CONFIG = {
    "slackbot_auth_token_key": "BOT_ID",
    "channel_id": "C09LT3GFS4T"
}

LEGACY_CONFIG_PATH = Path.home() / ".photon_mosaic" / "slackbot.json"


def _default_config_dir() -> Path:
    env_dir = os.environ.get("SLACK_BOT_CONFIG_DIR")
    return Path(env_dir) if env_dir else Path.home() / ".oshirase"


# config
def ensure_default_config(reset_config=False, config_dir: Optional[Union[str, Path]] = None) -> Path:
    config_dir = Path(config_dir) if config_dir else _default_config_dir()
    config_path = config_dir / "slackbot.json"

    if reset_config or not config_path.exists():
        # Fall back to a pre-existing legacy config (from photon-mosaic-roicat's
        # old ~/.photon_mosaic location) rather than clobbering it with fresh
        # defaults, unless the caller explicitly asked to reset.
        if not reset_config and LEGACY_CONFIG_PATH.exists():
            return LEGACY_CONFIG_PATH

        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Config file written to: {str(config_path)}")

        # Write the dictionary to the JSON file
        with config_path.open('w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f)

    return config_path


def load_and_process_config(config_path: Optional[Union[str, Path]] = None):
    if config_path is None:
        env_path = os.environ.get("SLACK_BOT_CONFIG_PATH")
        config_path = Path(env_path) if env_path else ensure_default_config(reset_config=False)

    with open(config_path, 'r', encoding='utf-8') as f:
        configs = json.load(f)

    return configs

def get_slack_client(configs=None, token=None):
    if token is None:
        token_key = os.environ.get("SLACK_BOT_TOKEN_KEY") or configs["slackbot_auth_token_key"]
        client = get_client(token_key)
    else:
        client = get_client(token)

    return client

def test_write(message=None):
    if message is None:
        message = (
            "Hello World!\nHello People!"
            "\n<https://github.com/sumiya-kuroda/photon-mosaic-roicat|GitHub>"
        )
    notify_slack(message)

def _resolve_channel_id(configs, channel_id=None):
    return channel_id or os.environ.get("SLACK_BOT_CHANNEL_ID") or configs["channel_id"]

def notify_slack(msg=None, channel_id=None, config_path=None):
    if msg is None:
        raise ValueError('Specify message!')

    configs = load_and_process_config(config_path)
    client = get_slack_client(configs=configs)
    channel_id = _resolve_channel_id(configs, channel_id)
    print("Sending notification to Slack ...")
    client.chat_postMessage(
        channel=channel_id, text=msg, unfurl_links=False
    )

def notify_slack_with_file(msg=None, filepath=None, channel_id=None, config_path=None):
    if msg is None:
        raise ValueError('Specify message!')
    if filepath is None:
        raise ValueError('Specify file!')
    configs = load_and_process_config(config_path)
    client = get_slack_client(configs=configs)
    channel_id = _resolve_channel_id(configs, channel_id)
    print("Sending notification to Slack ...")
    client.files_upload_v2(
        channel=channel_id,
        file=filepath,
        filename=os.path.basename(filepath),
        initial_comment=msg
    )


def notify_slack_with_file_many(msg=None, filepaths: list =None, channel_id=None, config_path=None):
    if msg is None:
        raise ValueError('Specify message!')
    if filepaths is None:
        raise ValueError('Specify file!')
    configs = load_and_process_config(config_path)
    client = get_slack_client(configs=configs)
    channel_id = _resolve_channel_id(configs, channel_id)
    print("Sending notification to Slack ...")
    msg_resp = client.chat_postMessage(
        channel=channel_id, text=msg, unfurl_links=False
    )

    thread_ts = msg_resp["ts"]  # timestamp of the root message

    for filepath in filepaths:
        client.files_upload_v2(
            channel=channel_id,
            thread_ts=thread_ts,   # thread ID
            file=filepath,
            filename=os.path.basename(filepath),
        )

if __name__ == '__main__':
    test_write()