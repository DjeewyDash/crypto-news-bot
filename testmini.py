import requests

# ✅ Ta clé API CryptoPanic
API_KEY = "9f639c2dd1f605293683c386db653891cfa53ed4"

# Endpoint CryptoPanic pour les rumeurs (Rumors)
URL = "https://cryptopanic.com/api/v1/posts/"

# Paramètres : type=rumeur, tri par latest
params = {
    "auth_token": API_KEY,
    "filter": "rising",  # "rising" ou "hot" ou "latest"
    "currencies": "BTC,ETH,SOL",  # filtrage par crypto
    "public": "true"  # récupérer uniquement les posts publics
}

try:
    response = requests.get(URL, params=params)
    response.raise_for_status()
    data = response.json()

    posts = data.get("results", [])

    print(f"Nombre de rumeurs filtrées : {len(posts)}\n")

    if not posts:
        print("Pas de rumeurs pour BTC, ETH ou SOL pour le moment.")
    else:
        for post in posts:
            title = post.get("title", "Sans titre")
            link = post.get("url", "#")
            currency_list = [c["code"] for c in post.get("currencies", [])]
            print(f"📰 {title} ({', '.join(currency_list)})")
            print(f"🔗 {link}\n")

except requests.exceptions.RequestException as e:
    print("Erreur lors de la récupération des rumeurs :", e)
