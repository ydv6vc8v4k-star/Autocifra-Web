
import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "noticias.json"
MAX_NEWS = 40

FEEDS = [
    (
        "Google News · Motor España",
        "https://news.google.com/rss/search?q=coches+motos+motor+España&hl=es&gl=ES&ceid=ES:es",
    ),
    (
        "Google News · Coches",
        "https://news.google.com/rss/search?q=novedades+coches+automoción&hl=es&gl=ES&ceid=ES:es",
    ),
    (
        "Google News · Motos",
        "https://news.google.com/rss/search?q=motos+motociclismo+España&hl=es&gl=ES&ceid=ES:es",
    ),
    (
        "Google News · Competición",
        "https://news.google.com/rss/search?q=MotoGP+Fórmula+1+rally&hl=es&gl=ES&ceid=ES:es",
    ),
]

def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def parse_date(value):
    if value:
        try:
            return parsedate_to_datetime(value).astimezone(
                timezone.utc
            ).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
    return datetime.now(timezone.utc).isoformat()

def get_text(item, tag):
    element = item.find(tag)
    return clean(element.text) if element is not None else ""

def read_feed(feed_name, url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AutoCifraNewsBot/1.0 (RSS reader)"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()

    root = ET.fromstring(data)
    entries = []

    for item in root.findall(".//item"):
        title = get_text(item, "title")
        link = get_text(item, "link")
        published = get_text(item, "pubDate")
        source_element = item.find("source")
        source = (
            clean(source_element.text)
            if source_element is not None and source_element.text
            else feed_name
        )

        if not title or not link.startswith("https://"):
            continue

        # No copiamos el texto completo del artículo.
        key = hashlib.sha256(
            (title.casefold()).encode("utf-8")
        ).hexdigest()

        entries.append({
            "id": key,
            "title": title,
            "url": link,
            "source": source,
            "published": parse_date(published),
        })

    return entries

def main():
    news_by_id = {}
    successful_feeds = 0

    for feed_name, feed_url in FEEDS:
        try:
            items = read_feed(feed_name, feed_url)
            successful_feeds += 1
            for item in items:
                news_by_id.setdefault(item["id"], item)
        except Exception as error:
            print(f"No se pudo leer {feed_name}: {error}")

    # Si todas las fuentes fallan, conservamos las noticias anteriores.
    if successful_feeds == 0:
        raise RuntimeError(
            "Todas las fuentes RSS fallaron; no se sobrescriben las noticias."
        )

    articles = list(news_by_id.values())
    articles.sort(key=lambda x: x["published"], reverse=True)
    articles = articles[:MAX_NEWS]

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "news": articles,
    }

    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Actualización completada: {len(articles)} noticias; "
        f"{successful_feeds}/{len(FEEDS)} fuentes consultadas."
    )

if __name__ == "__main__":
    main()
