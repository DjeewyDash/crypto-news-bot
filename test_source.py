import yfinance as yf
from datetime import datetime

def get_realtime_calendar():
    print(f"--- ANALYSE DYNAMIQUE : {datetime.now().strftime('%H:%M:%S')} ---")
    try:
        # On utilise le ticker macro de référence qui contient le calendrier
        ticker = yf.Ticker("^GSPC") 
        cal = ticker.calendar
        
        # Le calendrier est un dictionnaire dynamique retourné par l'API
        if cal is not None:
            print("Données reçues de la Gateway financière :")
            print(cal)
        else:
            print("Aucune donnée disponible pour le moment via cette source.")
    except Exception as e:
        print(f"Erreur de connexion dynamique : {e}")

if __name__ == "__main__":
    get_realtime_calendar()
