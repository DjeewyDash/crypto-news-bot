import requests

# Remplace ici par ta clé
FINNHUB_KEY = "d669kg1r01qots73pcd0d669kg1r01qots73pcdg"

def test_finnhub():
    print("--- Diagnostic Finnhub ---")
    url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('economicCalendar', [])
            print(f"✅ Connexion réussie (Code 200)")
            print(f"📈 Nombre d'événements reçus : {len(events)}")
            
            if len(events) > 0:
                print("👍 Données bien reçues !")
            else:
                print("⚠️ Connexion OK, mais la liste d'événements est VIDE.")
                print("Cela arrive parfois si Finnhub n'a pas encore chargé le calendrier pour la période actuelle.")
                
        elif response.status_code == 401:
            print("❌ Erreur 401 : Clé invalide. Vérifie qu'il n'y a pas un espace caché.")
        elif response.status_code == 403:
            print("❌ Erreur 403 : Accès refusé. Ta clé n'est peut-être pas autorisée pour cette API.")
        elif response.status_code == 429:
            print("❌ Erreur 429 : Trop de requêtes (Rate limit). Attends 1 minute.")
        else:
            print(f"❓ Erreur inconnue : Code {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"🔥 Erreur de connexion : {e}")

if __name__ == "__main__":
    test_finnhub()
