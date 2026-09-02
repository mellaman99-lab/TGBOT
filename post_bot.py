"""
Бот для авто-постинга в Telegram-канал: "кто сейчас в тренде в русском хип-хопе".

- artists.json — база артистов, каждый день бот берёт из неё следующих
  N по кругу (без повторов, пока не пройдёт весь список).
- Картинка на тему хип-хопа подтягивается с Unsplash (бесплатный API).
- Пост отправляется в канал как фото с подписью.
"""

import json
import os
import random
from datetime import date
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
ARTISTS_FILE = BASE_DIR / "artists.json"

ARTISTS_PER_POST = 3

HEADLINES = [
    "🔥 Кто сегодня в тренде в русском хип-хопе",
    "🎧 На радаре сегодня: русский рэп",
    "📈 Го обсудим, кто сейчас жарит в рэпе",
    "🎤 Сегодня слушаем и обсуждаем",
    "🗣 Что происходит в русском хип-хопе прямо сейчас",
]

OUTROS = [
    "Пишите в комментарии, кого слушаете сейчас 👇",
    "А что у вас в плеере на этой неделе? 👇",
    "Согласны с подборкой или есть кто поинтереснее? 👇",
    "Го в комменты — накидайте своих фаворитов 👇",
]

IMAGE_QUERIES = [
    "hip hop concert",
    "rap music",
    "street music culture",
    "hip hop microphone",
    "rap concert crowd",
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
    day_idx = date.today().toordinal()
    headline = HEADLINES[day_idx % len(HEADLINES)]
    outro = OUTROS[day_idx % len(OUTROS)]

    lines = [f"<b>{headline}</b>", ""]
    for artist in selected_artists:
        lines.append(f"🎙 <b>{artist['name']}</b> — <i>{artist['tag']}</i>")
        lines.append(artist["note"])
        lines.append("")

    lines.append(outro)
    return "\n".join(lines).strip()


def get_image_url(unsplash_key):
    if not unsplash_key:
        return None

    query = random.choice(IMAGE_QUERIES)
    url = "https://api.unsplash.com/photos/random"
    params = {"query": query, "orientation": "landscape", "client_id": unsplash_key}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("urls", {}).get("regular")
    except requests.RequestException:
        return None


def send_to_telegram(text, bot_token, channel_id, image_url):
    base = f"https://api.telegram.org/bot{bot_token}"

    if image_url:
        caption = text if len(text) <= 1024 else text[:1000] + "…"
        payload = {
            "chat_id": channel_id,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML",
        }
        response = requests.post(f"{base}/sendPhoto", data=payload, timeout=30)
    else:
        payload = {
            "chat_id": channel_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        response = requests.post(f"{base}/sendMessage", data=payload, timeout=30)

    response.raise_for_status()
    return response.json()


def main():
    bot_token = os.environ.get("BOT_TOKEN")
    channel_id = os.environ.get("CHANNEL_ID")
    unsplash_key = os.environ.get("UNSPLASH_KEY")

    if not bot_token or not channel_id:
        raise SystemExit(
            "Не заданы переменные окружения BOT_TOKEN и/или CHANNEL_ID."
        )

    artists = load_artists()
    selected = pick_today_artists(artists)
    text = build_post_text(selected)
    image_url = get_image_url(unsplash_key)

    result = send_to_telegram(text, bot_token, channel_id, image_url)
    print("Отправлено:", result.get("ok"), "| с картинкой:", bool(image_url))
    print(text)


if __name__ == "__main__":
    main()
