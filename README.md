# Tkslok Watcher → Discord Notifier

A simple Python watcher that monitors [tkslok.pl/page/7](https://tkslok.pl/page/7/) for specific keywords and sends notifications to a Discord channel via webhook.

## Features
- Scrapes the page and searches for custom keywords (case-insensitive).
- Sends alerts to Discord with page title, link, and matching keywords.
- Avoids spamming: only notifies when new content appears.
- Configurable check interval (default: every 5 minutes).
- Ready to run locally or deploy on [Render.com](https://render.com) as a background worker.

## Requirements
- Python 3.8+
- Dependencies:
  ```
  pip install -r requirements.txt
  ```

## Configuration
1. Create a Discord webhook (Server Settings → Integrations → Webhooks).
2. Set the environment variable DISCORD_WEBHOOK_URL:
```
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxx/yyy"
```
3. Edit the KEYWORDS list in watcher.py to define the words you want to track.

## Usage
- Run locally:
```
python watcher.py
```
- Run in the background on Linux:
```
nohup python watcher.py &
```

## Deployment on Render
1. Push this repository to GitHub/GitLab.
2. Create a Background Worker on Render.
3. Configure:
  - Build Command: ```pip install -r requirements.txt```
  - Start Command: ```python watcher.py```
  - Add an environment variable: ```DISCORD_WEBHOOK_URL```
4. Deploy and monitor logs.

## Example Discord Alert
```
🔔 Keywords found: "match", "announcement"
📄 Tkslok, News
🔗 https://tkslok.pl/
```

## License
MIT – feel free to use, modify and share.