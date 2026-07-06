import asyncio
import aiohttp
import feedparser
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

# MAXIMO de fuentes RSS para conseguir 100+ noticias
RSS_FEEDS = [
    ("Reuters World",       "https://feeds.reuters.com/Reuters/worldNews"),
    ("Reuters Business",    "https://feeds.reuters.com/reuters/businessNews"),
    ("Reuters Markets",     "https://feeds.reuters.com/reuters/companyNews"),
    ("BBC World",           "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Business",        "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("BBC Technology",      "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("Al Jazeera",          "https://www.aljazeera.com/xml/rss/all.xml"),
    ("AP Top News",         "https://rsshub.app/apnews/topics/ap-top-news"),
    ("AP Business",         "https://rsshub.app/apnews/topics/business"),
    ("AP Politics",         "https://rsshub.app/apnews/topics/politics"),
    ("CNBC World",          "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
    ("CNBC Finance",        "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("CNBC Economy",        "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("CNBC Markets",        "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
    ("FT Markets",          "https://www.ft.com/markets?format=rss"),
    ("FT World",            "https://www.ft.com/world?format=rss"),
    ("FT Economics",        "https://www.ft.com/economics?format=rss"),
    ("Investing.com",       "https://www.investing.com/rss/news_301.rss"),
    ("Investing Commodities","https://www.investing.com/rss/news_4.rss"),
    ("Investing Forex",     "https://www.investing.com/rss/news_1.rss"),
    ("MarketWatch",         "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("MarketWatch Economy", "https://feeds.content.dowjones.io/public/rss/mw_economy"),
    ("Bloomberg Markets",   "https://feeds.bloomberg.com/markets/news.rss"),
    ("Bloomberg Politics",  "https://feeds.bloomberg.com/politics/news.rss"),
    ("The Guardian World",  "https://www.theguardian.com/world/rss"),
    ("The Guardian Business","https://www.theguardian.com/business/rss"),
    ("WSJ World",           "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("WSJ Markets",         "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("NYT World",           "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("NYT Economy",         "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml"),
    ("DW News",             "https://rss.dw.com/xml/rss-en-world"),
    ("France24",            "https://www.france24.com/en/rss"),
    ("Euronews",            "https://feeds.feedburner.com/euronews/en/news"),
    ("Zero Hedge",          "https://feeds.feedburner.com/zerohedge/feed"),
    ("Seeking Alpha",       "https://seekingalpha.com/feed.xml"),
]

KEYWORDS = [
    "war","conflict","military","sanctions","NATO","invasion","nuclear","missile",
    "terror","attack","coup","election","geopolit","diplomacy","treaty","embargo",
    "alliance","Fed","interest rate","inflation","recession","GDP","tariff",
    "trade war","supply chain","central bank","monetary","fiscal","debt","crisis",
    "default","currency","dollar","treasury","yield","China","Russia","Ukraine",
    "Israel","Iran","US","USA","America","Europe","OPEC","oil","energy",
    "commodities","gold","safe haven","risk off","tech","semiconductor","AI",
    "Federal Reserve","Powell","market","stocks","rally","selloff","crash",
    "unemployment","jobs","CPI","GDP","earnings","profit","loss","IPO",
    "Middle East","Asia","Pacific","Taiwan","North Korea","India","Pakistan",
    "Biden","Trump","Xi","Putin","Netanyahu","Zelensky","G7","G20","IMF",
    "World Bank","WTO","SWIFT","petrodollar","reserve currency","dedollarization",
]

def _is_relevant(title, summary):
    text = (title + " " + (summary or "")).lower()
    return any(kw.lower() in text for kw in KEYWORDS)

def _clean(text, max_len=300):
    import re
    return re.sub(r"<[^>]+>", "", text or "").strip()[:max_len]

async def _fetch_rss(session, name, url):
    articles = []
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            content = await resp.text()
        feed = feedparser.parse(content)
        for entry in feed.entries[:15]:  # hasta 15 por fuente
            title   = _clean(entry.get("title", ""), 150)
            summary = _clean(entry.get("summary", "") or entry.get("description", ""), 300)
            if title and _is_relevant(title, summary):
                articles.append({
                    "source":    name,
                    "title":     title,
                    "summary":   summary,
                    "published": entry.get("published", ""),
                })
    except Exception as e:
        logger.warning(f"RSS {name}: {e}")
    return articles

async def fetch_rss_news():
    articles = []
    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_rss(session, name, url) for name, url in RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, list):
            articles.extend(r)
    return articles

async def fetch_newsapi():
    if not NEWS_API_KEY:
        return []
    queries = [
        "geopolitics war sanctions",
        "Federal Reserve interest rates inflation",
        "China USA trade war tariffs",
        "gold oil commodities markets",
        "Middle East conflict Israel Iran",
        "Russia Ukraine war Europe",
        "stock market crash rally",
        "NATO military alliance",
    ]
    articles = []
    try:
        async with aiohttp.ClientSession() as session:
            for q in queries:
                params = {
                    "apiKey":   NEWS_API_KEY,
                    "q":        q,
                    "language": "en",
                    "sortBy":   "publishedAt",
                    "pageSize": 20,
                }
                try:
                    async with session.get(
                        "https://newsapi.org/v2/everything",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        data = await resp.json()
                    for art in data.get("articles", []):
                        title   = _clean(art.get("title", ""), 150)
                        summary = _clean(art.get("description", ""), 300)
                        if title:
                            articles.append({
                                "source":    art.get("source", {}).get("name", "NewsAPI"),
                                "title":     title,
                                "summary":   summary,
                                "published": art.get("publishedAt", ""),
                            })
                except:
                    pass
    except Exception as e:
        logger.warning(f"NewsAPI: {e}")
    return articles

async def get_all_news():
    rss, newsapi = await asyncio.gather(
        fetch_rss_news(),
        fetch_newsapi(),
        return_exceptions=True
    )

    all_articles = []
    for source in [rss, newsapi]:
        if isinstance(source, list):
            all_articles.extend(source)

    # Deduplicar
    seen, unique = set(), []
    for art in all_articles:
        key = art["title"][:60].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(art)

    logger.info(f"Total noticias unicas: {len(unique)}")
    # Minimo 100, maximo 150
    return unique[:150]
