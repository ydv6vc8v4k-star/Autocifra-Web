
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "noticias.json"

FEEDS = [
    ("Coches", "https://news.google.com/rss/search?q=coches+motor+España&hl=es&gl=ES&ceid=ES:es"),
    ("Motos", "https://news.google.com/rss/search?q=motos+motociclismo+España&hl=es&gl=ES&ceid=ES:es"),
    ("Competición", "https://news.google.com/rss/search?q=Fórmula+1+MotoGP+rally&hl=es&gl=ES&ceid=ES:es"),
    ("Tecnología", "https://news.google.com/rss/search?q=coches+eléctricos+tecnología+motor&hl=es&gl=ES&ceid=ES:es"),
]

def clean(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()

def get_text(element, name):
    child = element.find(name)
    return clean(child.text if child is not None else "")

def parse_date(value):
    if not value:
        return ""
    try:
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return date.isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""

def fetch_feed(category, url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AutoCifra/1.0 (news reader)"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        content = response.read()

    root = ET.fromstring(content)
    items = []

    for item in root.findall(".//item"):
        title = get_text(item, "title")
        link = get_text(item, "link")
        pub_date = parse_date(get_text(item, "pubDate"))

        source_element = item.find("source")
        source = clean(source_element.text if source_element is not None else "")
        if not source:
            source = "Google News"

        if not title or not link or not link.startswith(("https://", "http://")):
            continue

        items.append({
            "title": title,
            "link": link,
            "source": source,
            "pubDate": pub_date,
            "category": category,
        })

    return items

def main():
    all_news = []
    successful_feeds = 0

    for category, url in FEEDS:
        try:
            items = fetch_feed(category, url)
            all_news.extend(items)
            successful_feeds += 1
            print(f"{category}: {len(items)} noticias")
        except Exception as error:
            print(f"Error en feed {category}: {error}")

    if successful_feeds == 0:
        raise RuntimeError("No se pudo consultar ninguna fuente RSS.")

    unique = []
    seen = set()

    for item in all_news:
        key = item["link"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    unique.sort(key=lambda item: item["pubDate"], reverse=True)
    unique = unique[:60]

    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(unique),
        "noticias": unique,
    }

    OUTPUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(f"Archivo actualizado: {OUTPUT}")
    print(f"Total de noticias: {len(unique)}")

if __name__ == "__main__":
    main()
