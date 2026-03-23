import requests
from datetime import datetime

# Votre clé API
API_KEY = "d1879a1777f86e152ea00b15846915fa"

# Les IDs FRED officiels pour les releases
# 10 = CPI, 53 = FOMC (Fed), 21 = GDP
targets = {"CPI": 10, "FED": 53, "GDP": 21}

def debug_fred_api():
    print(f"--- ANALYSE BRUTE API FRED : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    for name, r_id in targets.items():
        url = f"https://api.stlouisfed.org/fred/release/dates?release_id={r_id}&api_key={API_KEY}&file_type=json"
        
        try:
            print(f"\n[Test] Interrogation {name} (ID: {r_id})...")
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'release_dates' in data:
                # On affiche les 3 prochaines dates trouvées pour voir la réalité des données
                dates = [d['date'] for d in data['release_dates']]
                future = sorted([d for d in dates if datetime.strptime(d, '%Y-%m-%d') >= datetime.now()])
                
                if future:
                    print(f"   Succès : {len(future)} dates futures trouvées.")
                    print(f"   Prochaines dates : {future[:3]}")
                else:
                    print("   Aucune date future trouvée dans la réponse.")
            else:
                print(f"   Erreur structure : {data.get('error_message', 'Pas de donnée')}")
                
        except Exception as e:
            print(f"   Erreur réseau : {e}")

if __name__ == "__main__":
    debug_fred_api()
