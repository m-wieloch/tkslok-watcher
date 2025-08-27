#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A simple website watcher that sends a message to Discord (webhook)
if any of the specified words appear on https://tkslok.pl/.

Configuration:
- Set the DISCORD_WEBHOOK_URL environment variable (webhook address from the Discord channel)
- Change KEYWORDS below to the words/phrases you are interested in
- (optional) change CHECK_INTERVAL_SECONDS

Launch:
    pip install requests beautifulsoup4
    DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxx/yyy" python watcher.py
"""


import os
import time
import json
import hashlib
import logging
from typing import Set, Tuple

import requests
from bs4 import BeautifulSoup

# SETTINGS
URL = "https://tkslok.pl/category/aktualnosci/"
# PProvide words/phrases; does not distinguish between upper and lower case letters
KEYWORDS = [
    "uprawnienia",
    "prowadzącego",
    "strzelanie",
    "kurs"
]

CHECK_INTERVAL_SECONDS = 21600  # website check interval in seconds
REQUEST_TIMEOUT = 15  # timeout HTTP in seconds

# LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    logging.warning(
        "DISCORD_WEBHOOK_URL is missing from the environment variables. Set it before running!"
    )


def fetch_page_text(url: str) -> Tuple[str, str]:
    """Retrieves the page and returns a tuple (plain_text, page_title)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; tkslok-watcher/1.0; +https://example.local)"
    }
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Page title (if exists)
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    # Text of the entire page (without scripts/styles)
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text("\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text, title


def find_matches(text: str, keywords: Set[str]) -> Set[str]:
    text_lower = text.lower()
    matched = {kw for kw in keywords if kw.lower() in text_lower}
    return matched


def hash_relevant(text: str, keywords: Set[str]) -> str:
    """We only hash fragments that contain keywords, to make it easier 
    to detect changes related to content of interest."""
    text_lower = text.lower()
    parts = []
    for kw in sorted(keywords):
        kw_l = kw.lower()
        if kw_l in text_lower:
            parts.append(kw_l)
            # For stability: we attach the first 2k characters around the first hit
            idx = text_lower.find(kw_l)
            start = max(0, idx - 1000)
            end = min(len(text_lower), idx + len(kw_l) + 1000)
            parts.append(text_lower[start:end])
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest


def send_discord_notification(webhook_url: str, title: str, url: str, matches: Set[str]):
    content = (
        f"🔔 The following keywords appeared on the website: {', '.join(sorted(matches))}\n"
        f"📄 **{title}**\n"
        f"🔗 {url}"
    )
    payload = {
        "content": content,
        # You can also use embeds:
        "embeds": [
            {
                "title": "Keywords detected",
                "description": f"{', '.join(sorted(matches))}",
                "url": url,
            }
        ],
        "allowed_mentions": {"parse": []},  # do not ping anyone by accident
    }
    r = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=REQUEST_TIMEOUT)
    try:
        r.raise_for_status()
        logging.info("A notification has been sent to Discord.")
    except requests.HTTPError as e:
        logging.error("Error sending to Discord: %s | resposne: %s", e, r.text)


def main():
    if not WEBHOOK_URL:
        logging.error("Interrupted: lack of DISCORD_WEBHOOK_URL.")
        return

    keywords_set = set(KEYWORDS)
    last_digest = None

    logging.info("Start of watcher: %s | keywords: %s", URL, ", ".join(KEYWORDS))
    while True:
        try:
            text, page_title = fetch_page_text(URL)
            matches = find_matches(text, keywords_set)
            if matches:
                digest = hash_relevant(text, keywords_set)
                if digest != last_digest:
                    logging.info("Matches found: %s (new content)", ", ".join(sorted(matches)))
                    send_discord_notification(WEBHOOK_URL, page_title, URL, matches)
                    last_digest = digest
                else:
                    logging.info("No changes to the match, notification skipped")
            else:
                logging.info("No matches found.")
        except Exception as e:
            logging.exception("Error while checking the page: %s", e)

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
