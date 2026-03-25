import requests
import feedparser
import re
import json
import os  # Ajouté pour la sécurité

# --- CONFIGURATION ---
# On récupère le Token depuis le "coffre-fort" GitHub (Secret)
GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')
GIST_ID = "03b9b5d1579579f627c06470c1e279e8"

RSS_SOURCES = [
    {"name": "COINTELEGRAPH", "url": "https://cointelegraph.com/rss"},
    {"name": "COINDESK", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "CRYPTOSLATE", "url": "https://cryptoslate.com/feed/"}
]

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
                    
                    # News cliquable
                    news_content = f"<a href='{entry.link}' target='_blank' style='color: #CC6600; text-decoration: none;'>{icon}  {clean_title} 🔗 <u>{source['name']}</u> </a>"
                    
                    news_obj = {"content": news_content}
                    if any(asset in title_lower for asset in assets):
                        filtered_news.append(news_obj)
                    else:
                        fallback_news.append(news_obj)
        except: pass

    final_list = filtered_news[:12] if filtered_news else fallback_news[:8]
    if not final_list:
        return "🗞️  MARKET DATA STABLE "

    return "".join([item['content'] for item in final_list])

def update_gist(content):
    if not GITHUB_TOKEN:
        print("❌ Erreur : Aucun Token trouvé dans les variables d'environnement.")
        return

    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    data = {"files": {"news_crypto.txt": {"content": content}}}
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print("✅ Gist mis à jour avec succès !")
    else:
        print(f"❌ Erreur lors de la mise à jour : {response.status_code}")

if __name__ == "__main__":
    print("Extraction des news en cours...")
    texte_final = get_clean_news()
    update_gist(texte_final)
