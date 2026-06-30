"""
news_fetcher.py
Obtiene noticias geopolíticas en tiempo real desde múltiples fuentes:
- RSS feeds de Reuters, BBC, Al Jazeera, AP, FT, CNBC
- NewsAPI (si hay API key configurada)
- GNews API (alternativa gratuita)
"""

import asyncio
import aiohttp
import feedparser
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

# ── RSS Feeds geopolíticos / financieros ──────────────────────────────────────
RSS_FEEDS = [
    ("Reuters World",    "https://feeds.reuters.com/Reuters/worldNews"),
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("BBC World",        "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Business",     "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("Al Jazeera",       "https://www.aljazeera.com/xml/rss/all.xml"),
    ("AP Top News",      "https://rsshub.app/apnews/topics/ap-top-news"),
    ("CNBC World",       "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
    ("CNBC Finance",     "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("FT Markets",       "https://www.ft.com/markets?format=rss"),
    ("Investing.com",    "https://www.investing.com/rss/news_301.rss"),
]

# Palabras clave que filtran noticias con impacto geopolítico/macro
KEYWORDS = [
    # Geopolítica
    "war", "conflict", "military", "sanctions", "NATO", "invasion",
    "nuclear", "missile", "terror", "attack", "coup", "election",
    "geopolit", "diplomacy", "treaty", "embargo", "alliance",
    # Economía macro
    "Fed", "interest rate", "inflation", "recession", "GDP", "tariff",
    "trade war", "supply chain", "central bank", "monetary", "fiscal",
    "debt", "crisis", "default", "currency", "dollar", "treasury", "yield",
    # Países clave para NAS100 y ORO
    "China", "Russia", "Ukraine", "Israel", "Iran", "US", "USA", "America",
    "Europe", "OPEC", "oil", "energy", "commodities",
    # Metales / Nasdaq drivers
    "gold", "safe haven", "risk off", "tech", "semiconductor", "AI",
    "Federal Reserve", "Powell", "Jackson Hole",
]

def _is_geopolitical(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in KEYWORDS)

def _clean(text: str, max_len: int = 350) -> str:
    import re
    text = re.sub(r"<[^>]+>", "", text or "")
    return text.strip()[:max_len]

# ── RSS ───────────────────────────────────────────────────────────────────────
async def _fetch_rss_source(session, name: str, url: str):
    articles = []
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            content = await resp.text()
        feed = feedparser.parse(content)
        for entry in feed.entries[:8]:
            title   = _clean(entry.get("title", ""), 150)
            summary = _clean(entry.get("summary", "") or entry.get("description", ""), 350)
            pub     = entry.get("published", "")
            if title and _is_geopolitical(title, summary):
                articles.append({
                    "source":  name,
                    "title":   title,
                    "summary": summary,
                    "published": pub,
                })
    except Exception as e:
        logger.warning(f"RSS {name} error: {e}")
    return articles

async def fetch_rss_news():
    articles = []
    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_rss_source(session, name, url) for name, url in RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, list):
            articles.extend(r)
    return articles

# ── NewsAPI ───────────────────────────────────────────────────────────────────
async def fetch_newsapi():
    if not NEWS_API_KEY:
        return []
    articles = []
    try:
        params = {
            "apiKey":   NEWS_API_KEY,
            "q":        "geopolitics OR war OR sanctions OR Federal Reserve OR trade war",
            "language": "en",
            "sortBy":   "publishedAt",
            "pageSize": 25,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://newsapi.org/v2/everything",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
        for art in data.get("articles", []):
            title   = _clean(art.get("title", ""), 150)
            summary = _clean(art.get("description", ""), 350)
            if title:
                articles.append({
                    "source":    art.get("source", {}).get("name", "NewsAPI"),
                    "title":     title,
                    "summary":   summary,
                    "published": art.get("publishedAt", ""),
                })
    except Exception as e:
        logger.warning(f"NewsAPI error: {e}")
    return articles

# ── GNews (alternativa gratuita a NewsAPI) ────────────────────────────────────
async def fetch_gnews():
    if not GNEWS_API_KEY:
        return []
    articles = []
    try:
        params = {
            "token":    GNEWS_API_KEY,
            "q":        "geopolitics OR war OR Federal Reserve OR trade sanctions",
            "lang":     "en",
            "max":      20,
            "sortby":   "publishedAt",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://gnews.io/api/v4/search",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
        for art in data.get("articles", []):
            title   = _clean(art.get("title", ""), 150)
            summary = _clean(art.get("description", ""), 350)
            if title:
                articles.append({
                    "source":    art.get("source", {}).get("name", "GNews"),
                    "title":     title,
                    "summary":   summary,
                    "published": art.get("publishedAt", ""),
                })
    except Exception as e:
        logger.warning(f"GNews error: {e}")
    return articles

# ── Función principal ─────────────────────────────────────────────────────────
async def get_all_news():
    rss, newsapi, gnews = await asyncio.gather(
        fetch_rss_news(),
        fetch_newsapi(),
        fetch_gnews(),
        return_exceptions=True
    )

    all_articles = []
    for source in [rss, newsapi, gnews]:
        if isinstance(source, list):
            all_articles.extend(source)

    # Deduplicar por título
    seen, unique = set(), []
    for art in all_articles:
        key = art["title"][:60].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(art)

    logger.info(f"Noticias obtenidas: {len(unique)} (de {len(all_articles)} totales)")
    return unique[:45]  # máximo 45 para no exceder el contexto
