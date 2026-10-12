"""Junta titulares fechados sobre el paso desde el RSS de Google News, semana por semana.

Es la evidencia cruda para reconstruir el histórico de cierres (datasets/closures.csv).
Uso: python scripts/harvest_news.py 2021-01-01 2026-10-12 > ../datasets/news_headlines.csv
"""
import csv
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from email.utils import parsedate_to_datetime

import httpx

QUERY = '("Cristo Redentor" OR "Los Libertadores") (paso OR cierre OR cerrado OR habilitado OR reabre)'
RSS = "https://news.google.com/rss/search?"
WINDOW = timedelta(days=7)  # Google devuelve hasta 100 ítems por consulta


def window(client: httpx.Client, start: date, end: date) -> list[dict]:
    q = f"{QUERY} after:{start} before:{end}"
    url = RSS + urllib.parse.urlencode({"q": q, "hl": "es-419", "gl": "AR", "ceid": "AR:es-419"})
    r = client.get(url)
    r.raise_for_status()
    items = ET.fromstring(r.content).findall(".//item")
    if len(items) >= 100:
        print(f"aviso: {start} llegó al tope de 100, pueden faltar titulares", file=sys.stderr)
    return [{
        "published": parsedate_to_datetime(i.findtext("pubDate")).isoformat(),
        "source": i.findtext("source"),
        "title": i.findtext("title"),
        "link": i.findtext("link"),
    } for i in items]


def main(start: date, end: date) -> None:
    seen, rows = set(), []
    with httpx.Client(timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as client:
        d = start
        while d < end:
            for row in window(client, d, min(d + WINDOW, end)):
                if row["title"] not in seen:
                    seen.add(row["title"])
                    rows.append(row)
            d += WINDOW
            time.sleep(1)  # cortesía con Google
    rows.sort(key=lambda r: r["published"])
    w = csv.DictWriter(sys.stdout, fieldnames=["published", "source", "title", "link"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2]))
