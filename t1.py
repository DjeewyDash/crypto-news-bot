import requests
import feedparser
import re
import json

# --- CONFIGURATION GITHUB (À REMPLIR) ---
GITHUB_TOKEN = "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"
GIST_ID = "03b9b5d1579579f627c06470c1e279e8"

# --- SOURCES RSS ---
RSS_SOURCES = [
    {"name": "COINTELEGRAPH", "url": "https://cointelegraph.com/rss"},
    {"name": "COINDESK", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "CRYPTOSLATE", "url": "https://cryptoslate.com/feed/"}
]

# Mots-clés stratégiques
assets = ["btc", "eth", "sol", "bitcoin", "ethereum", "solana"]
alerts = ["crash", "surge", "plunge", "breakout", "ath", "sec", "fed", "etf", "pump", "dump", "urgent"]

def get_clean_news():
    filtered_news = []
    fallback_news = []
    
    for source in RSS_SOURCES:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(source["url"], headers=headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    title_original = entry.title
                    title_lower = title_original.lower()
                    clean_title = re.sub(r'<!\[CDATA\[|\]\]>|<.*?>', '', title_original).strip().upper()
                    
                    icon = "🚨" if any(word in title_lower for word in alerts) else "🗞️"
                    news_obj = {
                        "content": f"{icon}  {clean_title} 🔗 <u>{source['name']}</u> "
                    }

                    if any(asset in title_lower for asset in assets):
                        filtered_news.append(news_obj)
                    else:
                        fallback_news.append(news_obj)
        except: pass

    final_list = filtered_news[:12] if filtered_news else fallback_news[:8]
    if not final_list:
        return "🗞️  MARKET DATA STABLE • NO MAJOR VOLATILITY DETECTED "

    return "".join([item['content'] for item in final_list])

def update_gist(content):
    """Envoie le texte défilant vers GitHub Gist"""
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "files": {
            "news_crypto.txt": {"content": content}
        }
    }
    
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print("✅ Gist mis à jour avec succès !")
    else:
        print(f"❌ Erreur lors de la mise à jour : {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Extraction des news en cours...")
    texte_final = get_clean_news()
    
    print("\n--- TEXTE ENVOYÉ ---")
    print(texte_final)
    print("--------------------\n")
    
    update_gist(texte_final)
