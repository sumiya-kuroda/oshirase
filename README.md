# Oshirase
`oshirase` is a Python library to send notifications via Slack. Expected usage includes: 
- [photon-mosaic-pipeline](https://github.com/photon-mosaic/photon-mosaic-pipeline) 
- [ROICaT](https://github.com/RichieHakim/ROICaT). Heavily adapted from prior work by [Athina Apostolelli **@AthinaApostolelli**](https://www.sainsburywellcome.org/web/people/athina-apostolelli).
- datashuttle


`oshirase` bundles a generic SLURM (via [submitit](https://github.com/facebookincubator/submitit)) + Slack job runner (`oshirase.slurm_helper`, `oshirase.notification.slack_bot`) that works with any Python/CLI job.

## Getting started
1. Install dependencies like below
```sh
conda activate photon-mosaic-pipeline # We will use the same env as photon-mosaic

# General (Every time yoiuu add a new job you have to reinstall this)
pip install -e .

# ROICaT only
pip install -e .[roicat]
pip uninstall torch # because roicat installation will install non-CUDA version of PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

2. First make your own slack app from [here](https://api.slack.com/apps). You should also take a look at [this page](https://api.slack.com/apis/connections/socket) and [some of official examples](https://github.com/slack-samples/bolt-python-starter-template/tree/main) to understand how Slack bots work.

```json
{
  "_metadata": {
      "major_version": 1
  },
  "display_information": {
      "name": "2p-313"
  },
  "features": {
      "app_home": {
          "home_tab_enabled": true,
          "messages_tab_enabled": true,
          "messages_tab_read_only_enabled": true
      },
      "bot_user": {
          "display_name": "2p-313",
          "always_online": true
      },
      "slash_commands": [
          {
              "command": "/oshirase-run",
              "description": "Run an oshirase job",
              "usage_hint": "<job_name>",
              "should_escape": false
          }
      ]
  },
  "oauth_config": {
      "scopes": {
          "bot": [
              "channels:history",
              "chat:write",
              "files:write",
              "channels:join",
              "groups:write",
              "im:write",
              "mpim:write",
              "commands"
          ]
      }
  },
  "settings": {
      "event_subscriptions": {
          "bot_events": [
              "message.channels"
          ]
      },
      "interactivity": {
          "is_enabled": false
      },
      "org_deploy_enabled": true,
      "socket_mode_enabled": true,
      "token_rotation_enabled": false
  }
}
```

3. Create a Slack channel #sumiya-2p and copy its ID. Also add your App **2p-313** (Here is a link to [the app](https://api.slack.com/apps/A09LT1WU9SP). Contact Sumiya if you need access).

3. By default, config (token key + channel ID) is stored at
   `~/.oshirase/slackbot.json`.

4. You can run `python -m oshirase.notification.slack_bot` to send a test message.

5. To let people trigger jobs via `/oshirase-run <job_name>`, generate an
   **app-level token** for Socket Mode: in your Slack app config, go to
   *Basic Information → App-Level Tokens*, create a token with the
   `connections:write` scope, and set it as `SLACK_BOT_APP_TOKEN` in the
   environment the listener runs in (this is separate from the bot token
   used for outbound notifications).

## Running the Slack listener

`/oshirase-run <job_name>` is handled by a long-running process that keeps a
Socket Mode connection open (no public HTTPS endpoint needed, since it's not
reachable from an HPC login node anyway):

```sh
pip install -e .          # pulls in slack_bolt and registers the console script
export SLACK_BOT_APP_TOKEN=xapp-...
oshirase-listen
```

`oshirase-listen` blocks, so keep it alive with either a quick tmux session:

```sh
tmux new -s oshirase-listen 'oshirase-listen'
```

or a `systemd --user` service for something more durable
(`~/.config/systemd/user/oshirase-listen.service`):

```ini
[Unit]
Description=oshirase Slack command listener

[Service]
ExecStart=%h/.conda/envs/photon-mosaic-pipeline/bin/oshirase-listen
Environment=SLACK_BOT_APP_TOKEN=xapp-...
Restart=on-failure

[Install]
WantedBy=default.target
```

```sh
systemctl --user enable --now oshirase-listen
```

**Note:** `/oshirase-run` only accepts one of the job names below (a fixed
allowlist — no arbitrary command/script text is ever run), and there is
currently no per-user authorization check: anyone with access to the Slack
app can trigger any of these jobs.

| Job name | Script | What it runs |
|---|---|---|
| `pm` | `jobs/hpc_jobs/run_pm.py` | Base photon-mosaic pipeline |
| `roicat` | `jobs/hpc_jobs/run_roicat.py` | ROICaT tracking pipeline |
| `pm_roicat` | `jobs/hpc_jobs/run_pm_roicat.py` | photon-mosaic, then ROICaT |
| `pm_holo_ai228` | `jobs/hpc_jobs/run_pm_holo_ai228.py` | photon-mosaic (holo ai228 config) |
| `pm_holo_ai230` | `jobs/hpc_jobs/run_pm_holo_ai230.py` | photon-mosaic (holo ai230 config) |
| `pm_visual_ai228` | `jobs/hpc_jobs/run_pm_visual_ai228.py` | photon-mosaic (visual ai228 config) |
| `pm_visual_ai230` | `jobs/hpc_jobs/run_pm_visual_ai230.py` | photon-mosaic (visual ai230 config) |
| `pm_visual_mesoscan_np2` | `jobs/hpc_jobs/run_pm_visual_mesoscan_np2.py` | photon-mosaic (mesoscan np2 config) |
| `echo` | `jobs/hpc_jobs/run_local_example.py` | No-SLURM smoke test (`cluster="local"`) |

## How to use

When running only photon-mosaic
```sh
cd jobs/hpc_jobs
sbatch _run_wrapper.sh run_pm.py
```

When running ROICaT
```sh
cd jobs/hpc_jobs
sbatch _run_wrapper.sh run_roicat.py
```

When running photon-mosaic + ROICaT
```sh
cd jobs/hpc_jobs
sbatch _run_wrapper.sh run_pm_roicat.py
```

```sh
python jobs/hpc_jobs/run_local_example.py
```