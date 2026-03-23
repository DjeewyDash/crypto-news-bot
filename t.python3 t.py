import requests
import feedparser

RSS_SOURCES = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/"
]

keywords = ["btc", "eth", "sol", "bitcoin", "ethereum", "solana"]

all_entries = []

for url in RSS_SOURCES:
    response = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    feed = feedparser.parse(response.content)
    for entry in feed.entries:
        if any(k in entry.title.lower() for k in keywords):
            all_entries.append(entry)

print(f"Articles trouvés : {len(all_entries)}\n")
for e in all_entries[:10]:
    print(f"📰 {e.title}")
    print(f"🔗 {e.link}\n")

