import requests

# REMPLACE ICI
CLE_API = "d1879a1777f86e152ea00b15846915fa" 

def test_connexion():
    print("--- Tentative de connexion à la FRED ---")
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={CLE_API}&file_type=json&limit=1"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Statut HTTP : {response.status_code}")
        
        data = response.json()
        if 'observations' in data:
            valeur = data['observations'][0]['value']
            print(f"✅ SUCCÈS ! Taux FED récupéré : {valeur}%")
        else:
            print("❌ ERREUR : La clé semble invalide ou refusée.")
            print("Réponse complète :", data)
            
    except Exception as e:
        print(f"❌ ÉCHEC CRITIQUE : Impossible de contacter le serveur.")
        print(f"Erreur : {e}")

if __name__ == "__main__":
    test_connexion()
