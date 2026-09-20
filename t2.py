import requests
import feedparser
import json
import os
import random
import html

# --- CONFIGURATION ---
# Récupère le Token depuis le coffre-fort GitHub
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
GIST_ID = "03b9b5d1579579f627c06470c1e279e8"

# --- LIGNE 3 : ACTUALITÉS CRYPTO ---
RSS_CRYPTO = [
    {"name": "COINTELEGRAPH", "url": "https://cointelegraph.com/rss"},
    {"name": "COINDESK", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "CRYPTOSLATE", "url": "https://cryptoslate.com/feed/"}
]

# --- LIGNE 2 : ACTUALITÉS MARCHÉS & MONDE ---
# Google News - édition française
RSS_MARKETS_FR = [
    {
        "name": "GOOGLE NEWS",
        "url": "https://news.google.com/rss/search?q=(march%C3%A9s%20OR%20bourse%20OR%20%C3%A9conomie%20OR%20inflation%20OR%20Fed%20OR%20BCE%20OR%20g%C3%A9opolitique%20OR%20p%C3%A9trole)%20when%3A1h&hl=fr&gl=FR&ceid=FR:fr"
    }
]

# --- GÉNÈRE LA LIGNE 3 ORANGE ---
def get_crypto_news():
    all_news = []

    for source in RSS_CRYPTO:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(source["url"], headers=headers, timeout=5)

            if response.status_code == 200:
                feed = feedparser.parse(response.content)

                for entry in feed.entries[:5]:
                    title = html.escape(entry.title.upper())
                    all_news.append(
                        f"<span style='color: #CC6600;'>🗞️  {title} - {source['name']} </span>"
                    )
        except Exception as e:
            print(f"Erreur crypto {source['name']} : {e}")

    if not all_news:
        return "🗞️ MARKET DATA STABLE"

    random.shuffle(all_news)
    return " ".join(all_news[:15])


# --- GÉNÈRE LA LIGNE 2 VIOLETTE ---
def get_markets_news():
    all_news = []

    for source in RSS_MARKETS_FR:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(source["url"], headers=headers, timeout=5)

            if response.status_code == 200:
                feed = feedparser.parse(response.content)

                for entry in feed.entries[:10]:
                    title = html.escape(entry.title.upper())
                    all_news.append(
                        f"<span style='color: #B56CFF;'>🗞️  {title}</span>"
                    )

        except Exception as e:
            print(f"Erreur marchés : {e}")

    if not all_news:
        return None

    return " ".join(all_news[:10])


# --- MET À JOUR LES DEUX FICHIERS DU GIST ---
def update_gist(crypto_content, markets_content):
    if not GITHUB_TOKEN:
        print("❌ Aucun Token GitHub trouvé.")
        return

    files = {
        "news_crypto.txt": {
            "content": crypto_content
        }
    }

    # Sécurité : si Google News échoue, on conserve
    # le dernier news_markets.txt valide dans le Gist.
    if markets_content:
        files["news_markets.txt"] = {
            "content": markets_content
        }

    url = f"https://api.github.com/gists/{GIST_ID}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {"files": files}

    response = requests.patch(
        url,
        headers=headers,
        data=json.dumps(data),
        timeout=10
    )

    if response.status_code == 200:
        print("✅ Gist mis à jour avec succès.")
    else:
        print(f"❌ Erreur GitHub : {response.status_code}")
        print(response.text)


# --- LANCEMENT ---
if __name__ == "__main__":
    print("Extraction des actualités...")

    crypto = get_crypto_news()
    markets = get_markets_news()

    update_gist(crypto, markets)
