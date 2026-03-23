import requests, urllib3, re, time
from flask import Flask, jsonify
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

FRED_API_KEY = "d1879a1777f86e152ea00b15846915fa"

#=============== FONCTION NEWS GITHUB ==============

def get_github_news():
    url = "https://gist.githubusercontent.com/DjeewyDash/03b9b5d1579579f627c06470c1e279e8/raw/a2fa66f6d4a9a10e00b06ac7894303982ef4036a/news_crypto.txt"
    try:
        r = session.get(url, timeout=5)
        if r.status_code == 200:
            return r.text.strip()
    except:
        pass
    return "Chargement des actualités..."

#=============== DEBUT GITHUB ==============

def get_github_calendar():
    url = "https://gist.githubusercontent.com/DjeewyDash/3e42728124f0011e54b892e582e71e26/raw/5e117d68256e93d2a511a0eef8455dd5230b9ac1/gistfile1.txt"
    try:
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            today = datetime.now()
            def format_date(d_str):
                d = datetime.strptime(d_str, "%d/%m/%Y")
                delta = (d - today).days
                if delta < 0: return None
                if delta == 0: return f"{d.strftime('%d/%m')} (jr J)"
                return f"{d.strftime('%d/%m')} (J-{delta})"
            
            fed_list = sorted([d for d in data['fed'] if datetime.strptime(d, "%d/%m/%Y") >= today], key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            cpi_list = sorted([d for d in data['cpi'] if datetime.strptime(d, "%d/%m/%Y") >= today], key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            
            return {
                "fed": format_date(fed_list[0]) if fed_list else "--",
                "cpi": format_date(cpi_list[0]) if cpi_list else "--"
            }
    except:
        pass
    return {"fed": "--", "cpi": "--"}

#=============== FIN GITHUB ===============

def get_binance_ticker_data():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
        res = session.get(url, params={"symbols": str(symbols).replace("'", '"').replace(" ", "")}, timeout=5)
        if res.status_code == 200:
            items = res.json()
            parts = []
            for it in items:
                sym = it['symbol'].replace("USDT", "")
                price = float(it['lastPrice'])
                change = float(it['priceChangePercent'])
                sign = "+" if change >= 0 else ""
                emoji = "🚀" if change >= 0 else "📉"
                p_str = f"{price:,.2f}" if price >= 1 else f"{price:.4f}"
                parts.append(f"{emoji} {sym}: {p_str} ({sign}{change:.2f}%)")
            return "  •  ".join(parts)
    except: pass
    return "Flux Binance indisponible..."

def get_dynamic_calendar():
    return "📅 PROCHAINS ÉVÉNEMENTS : FED (Taux d'intérêt), CPI (Inflation), Rapport Emploi US... Restez connectés."

def get_metrics():
    try:
        # Liquidity (Proxy M2/DXY simplified)
        m2 = 21000.5
        m2_p = 20950.2
        liq = (m2 / 100) * 1.05
        liq_p = (m2_p / 100) * 1.05
        
        # Fed / Inf
        fed = 5.33
        fed_t = 5.25
        inf = 3.1
        inf_p = 3.4
        
        # DXY / MA200
        dxy = 103.85
        ma2 = 102.50
        
        # Fear & Greed
        fg = 72
        fg_p = 70
        
        return {
            "liq": liq, "liq_prev": liq_p,
            "fed": fed, "fed_target": fed_t,
            "inf_curr": inf, "inf_prev": inf_p,
            "dxy": dxy, "ma200": ma2,
            "fg": fg, "fg_prev": fg_p
        }
    except:
        return None

@app.route('/api/data')
def api_data():
    m = get_metrics()
    if not m: return jsonify({"error": "No data"})
    
    cal = get_github_calendar()
    
    def get_s(curr, prev, inv=False):
        if curr == prev: return {"msg": "STABLE", "cls": "b-stable"}
        cond = (curr < prev) if inv else (curr > prev)
        return {"msg": "HAUSSE", "cls": "b-up"} if cond else {"msg": "BAISSE", "cls": "b-down"}

    liq_s = get_s(m["liq"], m["liq_prev"])
    fed_s = {"msg": "NEUTRE", "cls": "b-stable"} if m["fed"] <= m["fed_target"] else {"msg": "RESTRICTIF", "cls": "b-down"}
    inf_status = get_s(m["inf_curr"], m["inf_prev"], inv=True)
    dxy_status = get_s(m["dxy"], m["ma200"], inv=True)
    fg_s = get_s(m["fg"], m["fg_prev"])
    
    delta_liq = m["liq"] - m["liq_prev"]
    delta_liq_pct = (delta_liq / m["liq_prev"]) * 100
    
    return jsonify({
        "liq": m["liq"], "liq_prev": m["liq_prev"], "liq_status": liq_s, "delta_liq_pct": delta_liq_pct,
        "fed": f"{m['fed']:.2f}%", "fed_target": f"{m['fed_target']:.2f}%", "fed_status": fed_s,
        "inf": f"{m['inf_curr']:.2f}%", "inf_prev": f"{m['inf_prev']:.2f}%", "inf_status": inf_status,
        "dxy": f"{m['dxy']:.2f}", "ma200": f"{m['ma200']:.2f}", "dxy_status": dxy_status,
        "fg": f"{m['fg']}/100", "fg_prev": f"{m['fg_prev']}/100", "fg_status": fg_s,
        "news_top": get_binance_ticker_data(),
        "events": get_dynamic_calendar(),
        "news_github": get_github_news(),
        "fed_date": cal["fed"],
        "cpi_date": cal["cpi"]
    })

@app.route('/')
def index():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>CRYPTO DASHBOARD PRO</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #000; --card: #111; --accent: #ff0000; --text: #eee; --dim: #888; }
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-font-smoothing: antialiased; }
        body { background: var(--bg); font-family: 'Inter', sans-serif; color: var(--text); overflow: hidden; height: 100vh; }
        
        .container { display: flex; flex-direction: column; height: 100vh; padding: 10px; gap: 10px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; padding: 5px 10px; border-bottom: 2px solid var(--accent); }
        .logo { font-weight: 900; font-size: 1.2rem; letter-spacing: -1px; }
        .live-tag { color: var(--accent); font-size: 0.7rem; font-weight: bold; border: 1px solid var(--accent); padding: 2px 6px; border-radius: 3px; }

        .ticker-wrap { background: var(--card); height: 35px; border-radius: 6px; overflow: hidden; display: flex; align-items: center; border: 1px solid #222; }
        .ticker { white-space: nowrap; display: inline-block; animation: scroll 30s linear infinite; font-weight: 700; font-size: 0.85rem; padding-left: 100%; }
        
        .main-grid { flex: 1; display: flex; flex-direction: column; gap: 10px; }
        .m-card { background: var(--card); border-radius: 12px; padding: 15px; border: 1px solid #222; display: flex; flex-direction: column; gap: 12px; position: relative; }
        .m-row { display: flex; justify-content: space-between; align-items: center; }
        .m-lbl { font-size: 0.75rem; color: var(--dim); font-weight: bold; text-transform: uppercase; }
        .m-val-wrap { display: flex; flex-direction: column; align-items: flex-end; }
        .m-val { font-size: 1.2rem; font-weight: 900; }
        .m-comp { font-size: 0.65rem; color: var(--dim); }
        .m-badge { font-size: 0.65rem; font-weight: 900; padding: 4px 8px; border-radius: 4px; min-width: 85px; text-align: center; }
        
        .b-up { background: #003311; color: #00ff66; border: 1px solid #00ff66; }
        .b-down { background: #330000; color: #ff3333; border: 1px solid #ff3333; }
        .b-stable { background: #222; color: #aaa; border: 1px solid #444; }

        .footer-news { background: #1a0000; border: 1px solid var(--accent); border-radius: 8px; height: 45px; display: flex; align-items: center; overflow: hidden; }
        .n-btn { background: var(--accent); color: white; font-size: 0.7rem; font-weight: 900; padding: 0 15px; height: 100%; display: flex; align-items: center; }
        
        @keyframes scroll { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">CRYPTO DASHBOARD <span style="color:var(--accent)">PRO</span></div>
            <div id="clock" class="live-tag">--:--:--</div>
        </div>

        <div class="ticker-wrap"><div id="n1" class="ticker">CHARGEMENT DES PRIX...</div></div>

        <div class="main-grid">
            <div class="m-card">
                <div class="m-row"><span class="m-lbl">LIQUIDITÉ MONDIALE</span><div class="m-val-wrap"><span id="liq" class="m-val">--</span><span id="liq_p" class="m-comp">--</span></div><div id="liq_s" class="m-badge">--</div></div>
                <div class="m-row"><span class="m-lbl">TAUX FED</span><div class="m-val-wrap"><span id="fed" class="m-val">--</span><span id="fed_t" class="m-comp">--</span></div><div id="fed_s" class="m-badge">--</div></div>
                <div class="m-row"><span class="m-lbl">CPI INFLATION</span><div class="m-val-wrap"><span id="inf" class="m-val">--</span><span id="inf_p" class="m-comp">--</span></div><div id="inf_s" class="m-badge">--</div></div>
                <div class="m-row"><span class="m-lbl">INDEX USD (DXY)</span><div class="m-val-wrap"><span id="dxy" class="m-val">--</span><span id="ma200" class="m-comp">--</span></div><div id="dxy_s" class="m-badge">--</div></div>
                <div class="m-row"><span class="m-lbl">SENTIMENT (F&G)</span><div class="m-val-wrap"><span id="fg" class="m-val">--</span><span id="fg_p" class="m-comp">--</span></div><div id="fg_s" class="m-badge">--</div></div>
            </div>
            
            <div class="ticker-wrap" style="height:30px; border-color:var(--accent);"><div id="n2" class="ticker" style="animation-duration:40s; color:var(--accent);">CHARGEMENT DU CALENDRIER...</div></div>
        </div>

        <div class="footer-news">
            <div class="n-btn">COINTELEGRAPH</div>
            <div class="ticker-wrap" style="background:transparent; border:none; flex:1;">
                <div id="n3" class="ticker" style="animation-duration:60s;">CHARGEMENT DES DERNIÈRES NEWS...</div>
            </div>
        </div>
    </div>

    <script>
        let toggle = false;
        setInterval(() => { toggle = !toggle; }, 3000);

        function updateClock() {
            const now = new Date();
            document.getElementById('clock').innerText = now.toLocaleTimeString('fr-FR');
        }
        setInterval(updateClock, 1000);

        async function loadMacro() {
            try {
                const r = await fetch('/api/data');
                const d = await r.json();
                
                document.getElementById('liq').innerText = "$" + d.liq.toFixed(2) + "T";
                document.getElementById('liq_p').innerText = (d.delta_liq_pct >= 0 ? "+" : "") + d.delta_liq_pct.toFixed(2) + "% (Vs M-1)";
                document.getElementById('liq_s').className = "m-badge " + d.liq_status.cls;
                document.getElementById('liq_s').innerText = d.liq_status.msg;

                document.getElementById('fed').innerText = d.fed;
                document.getElementById('fed_t').innerText = "Prévu : " + d.fed_target;
                document.getElementById('fed_s').className = "m-badge " + d.fed_status.cls;
                document.getElementById('fed_s').innerText = toggle ? d.fed_date : d.fed_status.msg;

                document.getElementById('inf').innerText = d.inf;
                document.getElementById('inf_p').innerText = "Vs M-1 : " + d.inf_prev;
                document.getElementById('inf_s').className = "m-badge " + d.inf_status.cls;
                document.getElementById('inf_s').innerText = toggle ? d.cpi_date : d.inf_status.msg;

                document.getElementById('dxy').innerText = d.dxy;
                document.getElementById('ma200').innerText = "MA 200 : " + d.ma200;
                document.getElementById('dxy_s').className = "m-badge " + d.dxy_status.cls;
                document.getElementById('dxy_s').innerText = d.dxy_status.msg;

                document.getElementById('fg').innerText = d.fg;
                document.getElementById('fg_p').innerText = "Vs J-1 : " + d.fg_prev;
                document.getElementById('fg_s').className = "m-badge " + d.fg_status.cls;
                document.getElementById('fg_s').innerText = d.fg_status.msg;

                document.getElementById('n1').innerText = d.news_top + "  •  " + d.news_top;
                document.getElementById('n2').innerText = d.events + "  •  " + d.events;
                document.getElementById('n3').innerText = d.news_github + "  •  " + d.news_github;
                
            } catch (e) { console.log("Erreur:", e); }
        }
        
        setInterval(loadMacro, 5000);
        loadMacro();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
