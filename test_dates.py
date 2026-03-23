import requests

def test_json_calendar():
    print("--- TEST API CALENDRIER ÉCONOMIQUE ---")
    # API key gratuite pour test (FMP)
    api_key = "demo" 
    url = f"https://financialmodelingprep.com/api/v3/economic_calendar?apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Filtre les événements FED et CPI
        found = False
        for item in data[:20]: # On regarde les 20 prochains
            event = item.get('event', '').upper()
            if 'FED' in event or 'CPI' in event:
                print(f"Événement : {event} | Date : {item.get('date')}")
                found = True
        
        if not found:
            print("Aucun événement FED/CPI trouvé dans les 20 prochains jours.")
            
    except Exception as e:
        print(f"Erreur lors de la requête : {e}")

if __name__ == "__main__":
    test_json_calendar()
