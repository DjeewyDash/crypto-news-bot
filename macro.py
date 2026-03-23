from flask import Flask
import requests
from datetime import datetime, timedelta

API_KEY = "d66bb3pr01qots73vkvgd66bb3pr01qots73vl00"

app = Flask(__name__)

HTML = """
<html>
<head>
<meta http-equiv="refresh" content="120">
<style>
body { background:black; color:lime; font-family:Arial; text-align:center; }
.box { border:1px solid lime; padding:30px; margin:30px; display:inline-block; }
.big { font-size:40px; }
.small { font-size:16px; color:#88ff88; }
</style>
</head>

<body>

<h1>US MACRO LIVE</h1>

<div class="box">
NEXT CPI
<div class="big">{DATE}</div>
<div class="small">{TIME}</div>
</div>

</body>
</html>
"""

def get_next_cpi():

    try:
        # plage des 60 prochains jours
        today = datetime.utcnow().date()
        future = today + timedelta(days=60)

        url = "https://finnhub.io/api/v1/calendar/economic"

        params = {
            "from": today.isoformat(),
            "to": future.isoformat(),
            "token": API_KEY
        }

        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        # s'il n'y a pas d'événements
        if "economicCalendar" not in data:
            return "No data", ""

        # parcourir les événements
        for ev in data["economicCalendar"]:
            # souvent l'événement décrit contient "CPI"
            if ev.get("event") and "CPI" in ev["event"]:
                # timestamp Finnhub -> probablement epoch
                t = ev.get("time")
                if t:
                    dt = datetime.fromtimestamp(int(t))
                    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M UTC")

        return "No upcoming CPI", ""

    except Exception as e:
        return "ERROR", ""

@app.route("/")
def home():
    date, time = get_next_cpi()
    page = HTML.replace("{DATE}", date).replace("{TIME}", time)
    return page

app.run(port=5055)

