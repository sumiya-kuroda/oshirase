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

# General
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
      }
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
              "mpim:write"
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