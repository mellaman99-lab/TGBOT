"""
Бот для авто-постинга в Telegram-канал: "кто сейчас в тренде в русском рэпе".
"""

import json
import os
from datetime import date
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
ARTISTS_FILE = BASE_DIR / "artists.json"

ARTISTS_PER_POST = 3

HEADLINES = [
    "🔥 Кто сегодня в тренде в русском хип-хопе",
    "🎧 На радаре сегодня: русский рэп",
    "📈 Тренды русского хип-хопа на сегодня",
    "🎤 Сегодня слушаем и обсуждаем",
]


def load_artists():
    with open(ARTISTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_today_artists(artists, n=ARTISTS_PER_POST):
    if not artists:
        raise ValueError("artists.json пуст — добавь хотя бы одного артиста")

    today_index = date.today().toordinal()
    total = len(artists)
    start = (today_index * n) % total

    selected = []
    for i in range(n):
        selected.append(artists[(start + i) % total])
    return selected


def build_post_text(selected_artists):
    headline = HEADLINES[date.today().toordinal() % len(HEADLINES)]
    lines = [f"<b>{headline}</b>", ""]

    for artist in selected_artists:
        lines.append(f"🎙 <b>{artist['name']}</b> — <i>{artist['tag']}</i>")
        lines.append(artist["note"])
        lines.append("")

    lines.append("Пишите в комментарии, кого слушаете сейчас 👇")
    return "\n".join(lines).strip()


def send_to_telegram(text, bot_token, channel_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    bot_token = os.environ.get("BOT_TOKEN")
    channel_id = os.environ.get("CHANNEL_ID")

    if not bot_token or not channel_id:
        raise SystemExit(
            "Не заданы переменные окружения BOT_TOKEN и/или CHANNEL_ID."
        )

    artists = load_artists()
    selected = pick_today_artists(artists)
    text = build_post_text(selected)

    result = send_to_telegram(text, bot_token, channel_id)
    print("Отправлено:", result.get("ok"))
    print(text)


if __name__ == "__main__":
    main()
