"""Fetch RSS feeds and output news.json to stdout."""

import calendar
import json

import feedparser

FEEDS = [
    {"url": "https://money.udn.com/rssfeed/news/1001/5591",                "source": "經濟日報",    "category": "台股"},
    {"url": "https://feeds.feedburner.com/ettoday/finance",                "source": "ETtoday財經", "category": "台股"},
    {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",       "source": "CNBC",        "category": "美股"},
    {"url": "https://feeds.marketwatch.com/marketwatch/topstories",        "source": "MarketWatch", "category": "美股"},
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss",              "source": "CoinDesk",    "category": "加密貨幣"},
    {"url": "https://cointelegraph.com/rss",                               "source": "CoinTelegraph","category": "加密貨幣"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml",                   "source": "Al Jazeera",  "category": "宏觀"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",                 "source": "BBC World",   "category": "宏觀"},
]


def fetch_all() -> list[dict]:
    articles = []
    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:30]:
                published_ts = (
                    calendar.timegm(entry.published_parsed)
                    if getattr(entry, "published_parsed", None)
                    else 0
                )
                articles.append({
                    "title":        entry.get("title", ""),
                    "link":         entry.get("link", ""),
                    "source":       feed_info["source"],
                    "category":     feed_info["category"],
                    "published_ts": published_ts,
                })
        except Exception:
            pass
    articles.sort(key=lambda x: x["published_ts"], reverse=True)
    return articles


if __name__ == "__main__":
    print(json.dumps(fetch_all(), ensure_ascii=False, indent=2))
