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


#==========DEBUT NEWS=========

def get_clean_news():
    all_news = []
    for source in RSS_SOURCES:
        try:
            # On simule un vrai navigateur pour ne pas être bloqué
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            response = requests.get(source["url"], headers=headers, timeout=5)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                # On prend les 5 plus récentes de CHAQUE source pour garantir le mélange
                for entry in feed.entries[:5]:
                    title_clean = entry.title.replace("'", " ").replace('"', " ").upper()
                    icon = "🗞️"
                    
                    # Version finale : Orange sombre, pas de lien, pas de souligné, pas de symbole chaîne
                    news_content = f"<span style='color: #CC6600;'>{icon}  {title_clean} - {source['name']} </span>"
                    
                    all_news.append(news_content)
        except:
            continue

    if not all_news:
        return "🗞️  MARKET DATA STABLE "

    # On mélange un peu pour ne pas avoir 5 fois le même site d'affilée
    import random
    random.shuffle(all_news)

    return " ".join(all_news[:15]) # On en garde 15 pour le défilement

#=========FIN NEWS==========

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
