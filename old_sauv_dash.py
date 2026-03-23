# ==========================================
# NOM DU SCRIPT : CRYPTO DASHBOARD PRO
# VERSION : 18.01 (BOLLINGER CANDLE ONLY)
# TIMESTAMP : 2026-02-25 21:15
# PORT : 8080
# ==========================================

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

def get_dynamic_calendar():
    try:
        now = datetime.now()
        dt_fed = datetime(2026, 3, 18) 
        days_fed = (dt_fed - now).days
        dt_cpi = datetime(2026, 3, 11)
        days_cpi = (dt_cpi - now).days
        
        def format_event(name, date_str, days):
            style = 'class="blink-u"' if 0 <= days <= 7 else ''
            return f"{name} {date_str} <span {style}>({days}j restants)</span>"

        fed_part = format_event("FED", "18/03", days_fed)
        cpi_part = format_event("CPI", "11/03", days_cpi)
        return f"CALENDRIER : {fed_part} • {cpi_part} • PCE 27/03 • "
    except: return "CALENDRIER : DONNÉES EN ATTENTE... • "

def get_fred_macro_data():
    data = {"fed": 0.0, "fed_target": 3.10, "inf_curr": 0.0, "inf_prev": 0.0, "dxy": 0.0, "ma200": 0.0}
    try:
        r_fed = session.get(f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1", timeout=2).json()
        data["fed"] = float(r_fed['observations'][0]['value'])
        r_cpi = session.get(f"https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=14", timeout=2).json()
        obs = r_cpi['observations']
        data["inf_curr"] = ((float(obs[0]['value']) - float(obs[12]['value'])) / float(obs[12]['value'])) * 100
        data["inf_prev"] = ((float(obs[1]['value']) - float(obs[13]['value'])) / float(obs[13]['value'])) * 100
        url_dxy = f"https://api.stlouisfed.org/fred/series/observations?series_id=DTWEXBGS&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=250"
        r_dxy = session.get(url_dxy, timeout=2).json()
        obs_dxy = [float(o['value']) for o in r_dxy['observations'] if o['value'] != '.']
        if obs_dxy:
            data["dxy"] = obs_dxy[0]
            if len(obs_dxy) >= 200:
                data["ma200"] = sum(obs_dxy[:200]) / 200
    except: pass
    return data

def get_binance_ticker_data():
    try:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
        output = []
        for s in symbols:
            r = session.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}", timeout=1).json()
            price = float(r['lastPrice']); change = float(r['priceChangePercent'])
            icon = "🚀" if change >= 0 else "📉"
            display_name = s.replace("USDT", "/USDT")
            output.append(f"{display_name}: {price:,.2f} ({icon} {change:+.2f}%)")
        return " • ".join(output) + " • "
    except: return "FLUX BINANCE EN ATTENTE... • "

@app.route('/api/binance/<symbol>/<interval>')
def binance_proxy(symbol, interval):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=120"
        return jsonify(session.get(url, timeout=2).json())
    except: return jsonify([])

@app.route('/api/macro')
def macro_api():
    macro = get_fred_macro_data()
    try:
        r_fg = session.get("https://api.alternative.me/fng/?limit=2", timeout=2).json()
        fg_now = int(r_fg['data'][0]['value'])
        fg_prev = int(r_fg['data'][1]['value'])
    except: fg_now, fg_prev = 50, 50
    
    if fg_now <= 25: fg_s = {"msg": "EXTRÊME PEUR", "cls": "brd-r"}
    elif fg_now <= 45: fg_s = {"msg": "PEUR", "cls": "brd-r"}
    elif fg_now <= 55: fg_s = {"msg": "NEUTRE", "cls": "brd-w"}
    elif fg_now <= 75: fg_s = {"msg": "AVIDITÉ", "cls": "brd-g"}
    else: fg_s = {"msg": "EXTRÊME AVIDITÉ", "cls": "brd-g"}
    
    delta_inf = macro["inf_curr"] - macro["inf_prev"]
    inf_status = {"msg": "STABLE 〓", "cls": "brd-g"}
    if delta_inf > 0.05: inf_status = {"msg": "ACCÉLÉRATION ▲", "cls": "brd-r"}
    elif delta_inf < -0.05: inf_status = {"msg": "DÉSINFLATION ▼", "cls": "brd-g"}
    
    dxy_val = macro["dxy"]; ma200_ref = macro["ma200"]
    dxy_status = {"msg": "DOLLAR FORT", "cls": "brd-r"} if dxy_val > ma200_ref else {"msg": "DOLLAR FAIBLE", "cls": "brd-g"}
    
    return jsonify({
        "fed": f"{macro['fed']:.2f}%", "fed_target": f"{macro['fed_target']:.2f}%", "fed_status": {"msg": "RESTRICTIF", "cls": "brd-r"},
        "inf": f"{macro['inf_curr']:.2f}%", "inf_prev": f"{macro['inf_prev']:.2f}%", "inf_status": inf_status,
        "dxy": f"{dxy_val:.2f}", "ma200": f"{macro['ma200']:.2f}", "dxy_status": dxy_status,
        "fg": f"{fg_now}/100", "fg_prev": f"{fg_prev}/100", "fg_status": fg_s,
        "news_top": get_binance_ticker_data(),
        "events": get_dynamic_calendar()
    })

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --green: #00fa9a; --red: #ff4d4d; --bg: #000; --price-ivoire: #e6d6bc; --ui-grey: #222; --block-grey: #0a0a0a; --mauve: #bf77ff; --text-grey: #8a7f94; }
        body { background: var(--bg); color: white; font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; display: flex; justify-content: center; padding: 20px; overflow: hidden; }
        .app { width: 380px; display: flex; flex-direction: column; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .indicators { display: flex; gap: 12px; }
        .ind { display: flex; flex-direction: column; align-items: center; width: 42px; position: relative; }
        .halo { position: absolute; width: 22px; height: 22px; border-radius: 50%; top: -7px; filter: blur(8px); opacity: 0.8; }
        .dot { width: 7px; height: 7px; border-radius: 50%; background: #222; margin-bottom: 6px; z-index: 1; }
        .dot.g { background: var(--green); box-shadow: 0 0 10px var(--green); }
        .dot.r { background: var(--red); box-shadow: 0 0 10px var(--red); }
        .ind span { font-size: 8px; color: #888; font-weight: 900; }
        .btn-group { display: flex; gap: 8px; }
        .btn { background: var(--block-grey); border: 1px solid var(--ui-grey); color: #555; border-radius: 10px; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .btn.active { background: #333 !important; border-color: #fff !important; color: #fff !important; }
        .btn-a { width: 55px; height: 29px; font-size: 11px; }
        .price-wrap { text-align: center; margin-bottom: 15px; position: relative; }
        #price { font-size: 52px; font-weight: 500; color: var(--price-ivoire); letter-spacing: -1px; }
        .symbol { position: absolute; font-size: 16px; color: #e6d6bc; font-weight: 800; top: 8px; margin-left: 8px; }
        #change { font-size: 18px; font-weight: 900; margin-top: -2px; display: flex; align-items: center; justify-content: center; gap: 5px; }
        #change span { font-size: 18px; font-weight: 900; margin-left: 2px; }
        .tabs-area { display: flex; flex-direction: column; margin-bottom: 25px; }
        .tabs { display: flex; gap: 8px; }
        .tab { flex: 1; height: 32px; font-size: 10px; gap: 6px; }
        .candle-icon { position: relative; width: 8px; height: 14px; display: flex; align-items: center; justify-content: center; }
        .mèche { position: absolute; width: 1px; height: 100%; background: currentColor; opacity: 0.4; }
        .corps { position: absolute; width: 5px; height: 7px; background: currentColor; border-radius: 1px; z-index: 1; }
        .tabs-vars { display: flex; gap: 8px; margin-top: 5px; }
        .v-mini { flex: 1; text-align: center; font-size: 10px; font-weight: 900; color: #444; }
        .chart-container { position: relative; width: 100%; margin-bottom: 10px; }
        .chart-box { width: 100%; height: 260px; background: var(--block-grey); border: 1px solid #222; border-radius: 35px; overflow: hidden; position: relative; }
        canvas { width: 100%; height: 100%; }
        .chart-legend { position: absolute; bottom: 55px; left: 20px; display: flex; flex-direction: column; gap: 2px; pointer-events: none; z-index: 5; }
        .leg-item { font-size: 8px; font-weight: 800; display: flex; align-items: center; gap: 8px; text-transform: uppercase; color: #888; text-shadow: 1px 1px 1px #000; }
        .leg-dash { width: 16px; height: 2px; background-size: 4px 100%; background-image: linear-gradient(to right, currentColor 50%, rgba(255,255,255,0) 50%); }
        .pressure-block { margin: 15px 0 20px 0; display: flex; flex-direction: column; gap: 8px; }
        .pressure-labels { display: flex; justify-content: space-between; font-size: 10px; font-weight: 900; color: #444; }
        #pressure-signal { flex-grow: 1; text-align: center; height: 14px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 10px; }
        .pressure-rail { width: 100%; height: 2px; background: #222; position: relative; }
        .cursor { position: absolute; height: 6px; top: -2px; border-radius: 4px; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .s-panique { background: repeating-linear-gradient(45deg, var(--red), var(--red) 4px, #000 4px, #000 8px); box-shadow: 0 0 10px var(--red); }
        .s-vente { background: var(--red); }
        .s-neutre { background: repeating-linear-gradient(45deg, var(--green), var(--green) 4px, var(--red) 4px, var(--red) 8px); }
        .s-achat { background: var(--green); }
        .s-euphorie { background: repeating-linear-gradient(45deg, var(--green), var(--green) 4px, #000 4px, #000 8px); box-shadow: 0 0 10px var(--green); }
        @keyframes flash-red { 0%, 100% { color: var(--red); opacity: 1; } 50% { opacity: 0.2; } }
        @keyframes flash-green { 0%, 100% { color: var(--green); opacity: 1; } 50% { opacity: 0.2; } }
        .blink-r { animation: flash-red 0.4s infinite; }
        .blink-g { animation: flash-green 0.4s infinite; }
        .scroller-wrap { width: 100%; overflow: hidden; height: 14px; position: relative; }
        #wrap-n1 { margin-bottom: 8px; }
        #wrap-n2 { margin-bottom: 20px; }
        .scroller-text { position: absolute; white-space: nowrap; font-size: 10px; font-weight: 900; left: 0; }
        #n1 { color: #8a7f94; } #n2 { color: var(--mauve); }
        @keyframes pulse-u { 0%, 100% { border-bottom-color: transparent; } 50% { border-bottom-color: var(--mauve); } }
        .blink-u { border-bottom: 1.5px solid var(--mauve); animation: pulse-u 1s infinite; padding-bottom: 1px; }
        .macro-card { background: var(--block-grey); border: 1px solid #222; border-radius: 35px; padding: 22px 12px; }
        .m-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; height: 30px; }
        .m-lbl { width: 60px; color: #888; font-size: 9px; font-weight: 800; text-transform: uppercase; }
        .m-val-wrap { flex-grow: 1; display: flex; align-items: baseline; gap: 0; white-space: nowrap; overflow: hidden; margin-left: 2px; }
        .m-val { color: #eee; font-size: 14px; font-weight: 700; width: 55px; display: inline-block; flex-shrink: 0; }
        .m-comp { color: #888; font-size: 12px; font-weight: 500; letter-spacing: -0.2px; }
        .m-badge { width: 120px; border: 1px solid; border-radius: 8px; padding: 5px 0; font-size: 9px; font-weight: 900; text-align: center; flex-shrink: 0; }
        .brd-r { border-color: var(--red); color: var(--red); background: rgba(255, 77, 77, 0.15); }
        .brd-g { border-color: var(--green); color: var(--green); background: rgba(0, 250, 154, 0.15); }
        .brd-w { border-color: #fff; color: #fff; background: #333; }
        .chart-selector { position: absolute; top: -11px; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 10px; z-index: 10; }
        .switch { position: relative; display: inline-block; width: 34px; height: 18px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #333; transition: .3s; border-radius: 20px; border: 1px solid #444; }
        .slider:before { position: absolute; content: ""; height: 10px; width: 10px; left: 3px; bottom: 3px; background-color: #fff; transition: .3s; border-radius: 50%; }
        input:checked + .slider:before { transform: translateX(16px); }

        /* ZONE ALERTE V17.96 : BILINGUE & TRIANGLE DROITE */
        #alert-box { position: absolute; top: 11px; left: 0; width: 100%; display: flex; justify-content: center; align-items: center; gap: 4px; z-index: 15; height: 12px; pointer-events: none; }
        .dot-container { position: relative; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; }
        .dot-halo { position: absolute; width: 14px; height: 14px; border-radius: 50%; filter: blur(7px); opacity: 0.95; display: none; }
        #alert-dot { width: 6px; height: 6px; border-radius: 50%; z-index: 2; position: relative; background: #333; }
        #alert-txt { font-size: 8.5px; font-weight: 600; color: var(--text-grey); text-transform: uppercase; letter-spacing: 0.2px; display: flex; align-items: center; gap: 6px; }
        .tri-right { font-size: 10px; margin-left: 2px; }
    </style>
</head>
<body>
    <div class="app">
        <div class="header">
            <div class="indicators">
                <div class="ind"><div class="halo" id="h1"></div><div id="d1" class="dot"></div><span>SCALP</span></div>
                <div class="ind"><div class="halo" id="h2"></div><div id="d2" class="dot"></div><span>TREND</span></div>
                <div class="ind"><div class="halo" id="h3"></div><div id="d3" class="dot"></div><span>SWING</span></div>
            </div>
            <div class="btn-group">
                <div class="btn btn-a active" onclick="setAsset(this)">ETH</div>
                <div class="btn btn-a" onclick="setAsset(this)">BTC</div>
                <div class="btn btn-a" onclick="setAsset(this)">SOL</div>
            </div>
        </div>
        <div class="price-wrap">
            <span id="price">----</span><span class="symbol">(USDT)</span>
            <div id="change">0.00%<span>(24H)</span></div>
        </div>
        <div class="tabs-area">
            <div class="tabs">
                <div class="btn tab active" onclick="setTab(this, '1m')">1MN <div class="candle-icon"><div class="mèche"></div><div class="corps"></div></div></div>
                <div class="btn tab" onclick="setTab(this, '15m')">15MN <div class="candle-icon"><div class="mèche"></div><div class="corps"></div></div></div>
                <div class="btn tab" onclick="setTab(this, '1h')">1HRE <div class="candle-icon"><div class="mèche"></div><div class="corps"></div></div></div>
            </div>
            <div class="tabs-vars">
                <div class="v-mini" id="v-1m">0.00% (1H)</div>
                <div class="v-mini" id="v-15m">0.00% (15H)</div>
                <div class="v-mini" id="v-1h">0.00% (60H)</div>
            </div>
        </div>
        <div class="chart-container">
            <div class="chart-selector">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="3"><path d="M3 17l6-6 4 4 8-8"/></svg>
                <label class="switch"><input type="checkbox" id="chartTypeToggle" onchange="updateChart()"><span class="slider"></span></label>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="3"><path d="M6 5v14M10 3v18M14 6v12M18 4v16"/></svg>
            </div>
            <div id="alert-box">
                <div class="dot-container">
                    <div class="dot-halo" id="alert-halo"></div>
                    <div id="alert-dot"></div>
                </div>
                <div id="alert-txt"></div>
            </div>
            <div class="chart-box">
                <canvas id="chart"></canvas>
                <div class="chart-legend">
                    <div class="leg-item" style="color:rgba(255,255,0,0.8)"><div class="leg-dash"></div> EMA 20</div>
                    <div class="leg-item" style="color:var(--mauve)"><div class="leg-dash"></div> VWAP</div>
                </div>
            </div>
        </div>
        <div class="pressure-block">
            <div class="pressure-labels"><span id="lbl-survente">SURVENTE</span><span id="pressure-signal">SYNCHRONISATION...</span><span id="lbl-surachat">SURACHAT</span></div>
            <div class="pressure-rail"><div id="market-cursor" class="cursor"></div></div>
        </div>
        <div class="scroller-wrap" id="wrap-n1"><div id="n1" class="scroller-text"></div></div>
        <div class="scroller-wrap" id="wrap-n2"><div id="n2" class="scroller-text"></div></div>
        <div class="macro-card" id="macro-content"></div>
    </div>
    <script>
        const canvas = document.getElementById('chart'), ctx = canvas.getContext('2d');
        let currentSymbol = "ETHUSDT", currentInterval = "1m", pos1 = 0, pos2 = 0;
        let lastCandles = [];

        function setAsset(el) { document.querySelectorAll('.btn-a').forEach(b => b.classList.remove('active')); el.classList.add('active'); currentSymbol = el.innerText + "USDT"; updateAll(); }
        function setTab(el, interval) { document.querySelectorAll('.tab').forEach(b => b.classList.remove('active')); el.classList.add('active'); currentInterval = interval; updateAll(); }
        
        function animate() {
            const el1 = document.getElementById('n1'), el2 = document.getElementById('n2');
            if(el1 && el1.offsetWidth > 0) { pos1 -= 0.8; if (Math.abs(pos1) >= el1.offsetWidth / 2) pos1 = 0; el1.style.transform = `translateX(${pos1}px)`; }
            if(el2 && el2.offsetWidth > 0) { pos2 -= 0.6; if (Math.abs(pos2) >= el2.offsetWidth / 2) pos2 = 0; el2.style.transform = `translateX(${pos2}px)`; }
            if(lastCandles.length > 0) draw(lastCandles);
            requestAnimationFrame(animate);
        }

        async function updateVariations() {
            const p = ['1m', '15m', '1h']; const lbls = ['1H', '15H', '60H'];
            for(let i=0; i<3; i++) {
                try {
                    const r = await fetch(`/api/binance/${currentSymbol}/${p[i]}`);
                    const d = await r.json(); if(!d || d.length < 2) continue;
                    const last = parseFloat(d[d.length-1][4]), first = parseFloat(d[0][4]);
                    const pct = ((last - first) / first * 100).toFixed(2);
                    const el = document.getElementById(`v-${p[i]}`);
                    el.innerText = `${pct >= 0 ? '+' : ''}${pct}% ${pct >= 0 ? '▲' : '▼'} (${lbls[i]})`;
                    el.style.color = pct >= 0 ? 'var(--green)' : 'var(--red)';
                    const bull = last >= parseFloat(d[d.length-2][4]);
                    document.getElementById(`d${i+1}`).className = bull ? 'dot g' : 'dot r';
                    document.getElementById(`h${i+1}`).style.background = bull ? '#00fa9a' : '#ff4d4d';
                } catch(e){}
            }
        }

        async function updateChart() {
            try {
                const r = await fetch(`/api/binance/${currentSymbol}/${currentInterval}`);
                const data = await r.json(); if(!data || data.length < 60) return;
                lastCandles = data.map(d => ({ t: d[0], o: parseFloat(d[1]), h: parseFloat(d[2]), l: parseFloat(d[3]), c: parseFloat(d[4]), v: parseFloat(d[5]) }));
                const lastPrice = lastCandles[lastCandles.length-1].c;
                document.getElementById('price').innerText = lastPrice.toLocaleString('fr-FR', {minimumFractionDigits:2});
                const r24 = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${currentSymbol}`);
                const d24 = await r24.json();
                const p24 = parseFloat(d24.priceChangePercent).toFixed(2);
                const c = document.getElementById('change');
                c.innerHTML = `${p24 >= 0 ? '+' : ''}${p24}% ${p24 >= 0 ? '▲' : '▼'}<span>(24H)</span>`;
                c.style.color = p24 >= 0 ? '#00fa9a' : '#ff4d4d';
                updatePressureLogic(lastCandles);
            } catch(e){}
        }

        function updatePressureLogic(candles) {
            const cursor = document.getElementById('market-cursor'), signal = document.getElementById('pressure-signal');
            const lblV = document.getElementById('lbl-survente'), lblA = document.getElementById('lbl-surachat');
            const asset = currentSymbol.replace("USDT", "");
            const last3 = candles.slice(-3);
            const avgChange = last3.reduce((acc, curr, idx, arr) => {
                if(idx === 0) return acc;
                return acc + ((curr.c - arr[idx-1].c) / arr[idx-1].c * 100);
            }, 0) / 2;
            const currentVol = candles[candles.length-1].v;
            const avgVol = candles.slice(-20).reduce((a,b) => a + b.v, 0) / 20;
            const volRatio = currentVol / avgVol;
            let w = 80 + (Math.min(volRatio, 3) * 33);
            w = Math.min(Math.max(w, 80), 180);
            let s1 = 0.02, s2 = 0.10;
            if(currentInterval === '15m') { s1 = 0.15; s2 = 0.40; }
            if(currentInterval === '1h') { s1 = 0.40; s2 = 1.00; }
            let cls = "s-neutre", msg = `⏸️ ${asset} EST NEUTRE`;
            let col = "#444", lvCol = "#444", laCol = "#444", bV = "";
            let bA = "";
            if (avgChange <= -s2) { cls = "s-panique"; msg = `‼️ PANIQUE SUR ${asset}`; col = "var(--red)"; lvCol = "var(--red)"; bV = "blink-r"; }
            else if (avgChange <= -s1) { cls = "s-vente"; msg = "🔴 PRESSION VENDEUSE"; col = "var(--red)"; lvCol = "var(--red)"; }
            else if (avgChange >= s2) { cls = "s-euphorie"; msg = `🔥 EUPHORIE SUR ${asset}`; col = "var(--green)"; laCol = "var(--green)"; bA = "blink-g"; }
            else if (avgChange >= s1) { cls = "s-achat"; msg = "🟢 PRESSION ACHETEUSE"; col = "var(--green)"; laCol = "var(--green)"; }
            const railW = 380;
            let centerPos = (50 + (avgChange * (10/s2) * 5));
            let left = (centerPos / 100 * railW) - (w / 2);
            let finalLeft = Math.max(0, Math.min(left, railW - w));
            cursor.className = `cursor ${cls}`; cursor.style.width = w + 'px'; cursor.style.left = finalLeft + 'px';
            signal.innerHTML = msg; signal.style.color = col; lblV.style.color = lvCol; lblV.className = bV; lblA.style.color = laCol; lblA.className = bA;
        }

        function draw(candles) {
            canvas.width = canvas.clientWidth * 2; canvas.height = canvas.clientHeight * 2;
            ctx.scale(2,2); const w = canvas.clientWidth, h = canvas.clientHeight;
            const isCandle = document.getElementById('chartTypeToggle').checked;
            const display = candles.slice(-60);
            let tech = []; let cumPV = 0, cumV = 0; let currentEMA = display[0].c;
            const alpha = 2 / (20 + 1); 
            for(let i=0; i<60; i++) {
                const c = display[i];
                currentEMA = (c.c - currentEMA) * alpha + currentEMA;
                cumPV += c.c * c.v; cumV += c.v;
                let slice = display.slice(Math.max(0, i-19), i+1);
                let avg = slice.reduce((s,v)=>s+v.c,0)/slice.length;
                let std = Math.sqrt(slice.reduce((s,v)=>s+Math.pow(v.c-avg,2),0)/slice.length);
                tech.push({ ma: currentEMA, vwap: cumV ? cumPV / cumV : c.c, bU: avg+(std*2), bL: avg-(std*2) });
            }
            const allP = display.flatMap(d=>[d.h,d.l]);
            const min = Math.min(...allP), max = Math.max(...allP), range = max-min;
            const pL=20, pR=55, pT=30, pB=48, cW=w-pR-pL, cH=h-pT-pB;
            const getX = (i) => pL + (i/59)*cW, getY = (p) => pT + cH - ((p-min)/range * cH);
            
            ctx.clearRect(0,0,w,h); ctx.font="9px -apple-system, sans-serif";
            
            // Bollinger (Tracé en PREMIER - Seulement si isCandle)
            if(isCandle) {
                ctx.fillStyle = "rgba(191,119,255,0.15)"; ctx.beginPath();
                tech.forEach((t,i) => i===0?ctx.moveTo(getX(i),getY(t.bU)):ctx.lineTo(getX(i),getY(t.bU)));
                for(let i=59; i>=0; i--) ctx.lineTo(getX(i),getY(tech[i].bL)); ctx.fill();
                ctx.strokeStyle = "rgba(191,119,255,0.4)"; ctx.lineWidth = 0.5;
                ctx.beginPath(); tech.forEach((t,i) => i===0?ctx.moveTo(getX(i),getY(t.bU)):ctx.lineTo(getX(i),getY(t.bU))); ctx.stroke();
                ctx.beginPath(); tech.forEach((t,i) => i===0?ctx.moveTo(getX(i),getY(t.bL)):ctx.lineTo(getX(i),getY(t.bL))); ctx.stroke();
                ctx.lineWidth = 1;
            }

            ctx.strokeStyle="#252525"; ctx.strokeRect(pL, pT, cW, cH);
            ctx.fillStyle="#888"; ctx.textAlign="left";
            for(let i=0; i<=4; i++) {
                let y = pT + (cH*(i/4)); ctx.beginPath(); ctx.moveTo(pL,y); ctx.lineTo(pL+cW,y); ctx.stroke();
                ctx.fillText((max-(range*(i/4))).toFixed(2), pL + cW + 5, y+3);
            }
            for(let i=0; i<60; i+=15) {
                let x = getX(i); ctx.beginPath(); ctx.moveTo(x, pT); ctx.lineTo(x, pT+cH); ctx.stroke();
                let d = new Date(display[i].t);
                let tStr = (currentInterval === "1h") ? `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}-${d.getHours()}H` : `${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`;
                ctx.fillText(tStr, x-10, pT + cH + 16); 
            }

            if(isCandle) {
                display.forEach((d,i) => {
                    let x=getX(i), yO=getY(d.o), yC=getY(d.c), col=d.c>=d.o?'#00fa9a':'#ff4d4d';
                    ctx.strokeStyle=col; ctx.beginPath(); ctx.moveTo(x,getY(d.h)); ctx.lineTo(x,getY(d.l)); ctx.stroke();
                    ctx.fillStyle=col; ctx.fillRect(x-2, Math.min(yO,yC), 4, Math.max(Math.abs(yO-yC),1));
                });
            } else {
                display.forEach((d,i) => {
                    let color = d.c >= d.o ? '0, 250, 154' : '255, 77, 77';
                    let grad = ctx.createLinearGradient(0, getY(d.c), 0, pT+cH); grad.addColorStop(0, `rgba(${color}, 0.5)`); grad.addColorStop(1, `rgba(${color}, 0)`);
                    ctx.fillStyle = grad; ctx.fillRect(getX(i)-2, getY(d.c), 4, (pT+cH) - getY(d.c));
                });
                for(let i=1; i<60; i++) {
                    ctx.strokeStyle = display[i].c >= display[i-1].c ? '#00fa9a' : '#ff4d4d';
                    ctx.beginPath(); ctx.moveTo(getX(i-1), getY(display[i-1].c)); ctx.lineTo(getX(i), getY(display[i].c)); ctx.stroke();
                }
            }
            
            ctx.setLineDash([2, 2]); ctx.strokeStyle = "rgba(255, 255, 0, 0.8)"; 
            ctx.beginPath(); tech.forEach((t,i)=>i===0?ctx.moveTo(getX(i),getY(t.ma)):ctx.lineTo(getX(i),getY(t.ma))); ctx.stroke();
            ctx.strokeStyle = "#bf77ff"; ctx.beginPath(); tech.forEach((t,i)=>i===0?ctx.moveTo(getX(i),getY(t.vwap)):ctx.lineTo(getX(i),getY(t.vwap))); ctx.stroke();
            ctx.setLineDash([]); 

            const aT = document.getElementById('alert-txt'), aD = document.getElementById('alert-dot'), aH = document.getElementById('alert-halo');
            const lp = display[59].c, lv = tech[59].vwap, lm = tech[59].ma;
            let status = { msg: "", tri: "", color: "#333", halo: false, spot: false, pulse: false };
            let crossIdx = -1, isUp = false;
            for(let i=59; i>0; i--) {
                if((tech[i-1].ma <= tech[i-1].vwap && tech[i].ma > tech[i].vwap) || (tech[i-1].ma >= tech[i-1].vwap && tech[i].ma < tech[i].vwap)) {
                    crossIdx = 59 - i; isUp = tech[i].ma > tech[i].vwap; break;
                }
            }
            if (Math.abs(lp-lv)/lv*100 > 0.6) { status = { msg: "RISQUE : REPLI (RISK : PULLBACK)", tri: "!", color: "#555", halo: false, spot: false }; }
            else if (Math.abs(lm-lv)/lv*100 < 0.02) { status = { msg: "MARCHÉ : FLAT (MARKET : NEUTRAL)", tri: "≈", color: "#555", halo: false, spot: false }; }
            else if (crossIdx !== -1 && crossIdx < 10) { status = { msg: "SIGNAL: CROISEMENT (SIGNAL: CROSSING)", tri: isUp ? "▲" : "▼", color: isUp ? "var(--green)" : "var(--red)", halo: true, spot: true, pulse: true }; }
            else if (crossIdx !== -1) { status = { msg: isUp ? "FLUX HAUSSIER (FLOW : BULLISH)" : "FLUX BAISSIER (FLOW : BEARISH)", tri: isUp ? "▲" : "▼", color: isUp ? "var(--green)" : "var(--red)", halo: true, spot: false }; }
            if(status.msg) {
                aT.innerHTML = `<span>${status.msg}</span><span class="tri-right" style="color:${status.color}">${status.tri}</span>`;
                aD.style.background = status.color; aH.style.background = status.color; aH.style.display = status.halo ? "block" : "none";
                if(status.pulse) aH.style.animation = "pulse-u 0.6s infinite"; else aH.style.animation = "none";
            }
            if(status.spot && crossIdx !== -1) {
                let idx = 59 - crossIdx; let sX = getX(idx), sY = getY(tech[idx].ma);
                let p = (Math.sin(Date.now() / 150) + 1) / 2;
                let g = ctx.createRadialGradient(sX, sY, 0, sX, sY, 8 + (p*4));
                g.addColorStop(0, 'rgba(255,255,255,0.9)'); g.addColorStop(1, 'rgba(255,255,255,0)');
                ctx.fillStyle = g; ctx.beginPath(); ctx.arc(sX, sY, 12, 0, Math.PI*2); ctx.fill();
            }
        }

        async function loadMacro() {
            try {
                const r = await fetch('/api/macro'); const d = await r.json();
                document.getElementById('n1').innerText = d.news_top + d.news_top;
                document.getElementById('n2').innerHTML = d.events + d.events;
                document.getElementById('macro-content').innerHTML = `<div class="m-row"><span class="m-lbl">TAUX FED</span><div class="m-val-wrap"><span class="m-val">${d.fed}</span><span class="m-comp">(Prévu: ${d.fed_target})</span></div><div class="m-badge ${d.fed_status.cls}">${d.fed_status.msg}</div></div><div class="m-row"><span class="m-lbl">INFLATION</span><div class="m-val-wrap"><span class="m-val">${d.inf}</span><span class="m-comp">(Vs M-1: ${d.inf_prev})</span></div><div class="m-badge ${d.inf_status.cls}">${d.inf_status.msg}</div></div><div class="m-row"><span class="m-lbl">INDEX USD</span><div class="m-val-wrap"><span class="m-val">${d.dxy}</span><span class="m-comp">(MA 200: ${d.ma200})</span></div><div class="m-badge ${d.dxy_status.cls}">${d.dxy_status.msg}</div></div><div class="m-row"><span class="m-lbl">SENTIMENT</span><div class="m-val-wrap"><span class="m-val">${d.fg}</span><span class="m-comp">(J-1: ${d.fg_prev})</span></div><div class="m-badge ${d.fg_status.cls || ''}">${d.fg_status.msg}</div></div>`;
            } catch(e) {}
        }
        function updateAll() { updateChart(); updateVariations(); loadMacro(); }
        setInterval(updateAll, 10000); updateAll(); animate();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

