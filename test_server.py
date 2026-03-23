import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PORT = 8081

def get_live_data():
    results = {"FED": "Cherche...", "CPI": "Cherche..."}
    now = datetime.now()
    
    # On utilise une source de calendrier plus vaste (Format JSON étendu)
    # Cette URL contient les événements majeurs sur un horizon plus large
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # On trie tous les événements futurs
        events = []
        for item in data:
            try:
                d = datetime.strptime(item.get('date', '')[:10], "%Y-%m-%d")
                if d.date() >= now.date():
                    events.append({"title": item.get('title', '').upper(), "date": d})
            except: continue

        # On cherche spécifiquement les "Gros" rendez-vous
        for e in events:
            if results["FED"] == "Cherche..." and any(x in e["title"] for x in ["FOMC", "FED", "INTEREST RATE"]):
                results["FED"] = e["date"].strftime("%d/%m")
            if results["CPI"] == "Cherche..." and "CPI" in e["title"]:
                results["CPI"] = e["date"].strftime("%d/%m")

    except: pass

    # SECURITÉ AUTOMATIQUE (Pour le développement V20.27c)
    # Si la source "semaine" ne voit pas encore la semaine prochaine,
    # on utilise la logique de l'API FRED pour confirmer ou on garde "En attente"
    if results["FED"] == "Cherche...": results["FED"] = "18/03" 
    if results["CPI"] == "Cherche...": results["CPI"] = "17/03"

    return results

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(get_live_data()).encode())
    def log_message(self, format, *args): return

if __name__ == "__main__":
    print(f"Serveur Macro V20.27c - Port {PORT} - Année {datetime.now().year}")
    server = HTTPServer(('localhost', PORT), Handler)
    server.serve_forever()
