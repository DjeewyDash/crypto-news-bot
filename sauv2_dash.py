# --- DASHBOARD CRYPTO PRO - V8.4 - FLÈCHES DE DIRECTION ---
import requests, urllib3
from flask import Flask, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

FRED_API_KEY = "d1879a1777f86e152ea00b15846915fa"

def get_fred_val(series_id, default):
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=13"
        r = requests.get(url, timeout=5).json()
        if series_id == "CPIAUCSL":
            curr = float(r['observations'][0]['value']); prev = float(r['observations'][12]['value'])
            return "{:.2f}".format(((curr - prev) / prev) * 100)
        return "{:.2f}".format(float(r['observations'][0]['value']))
    except: return default

@app.route('/api/macro')
def macro_api():
    return jsonify({
        "fed": get_fred_val("FEDFUNDS", "3.64"), "inf": get_fred_val("CPIAUCSL", "2.31"), "dxy": 118.24, "fg": 9,
        "news_top": "KBC BANK LANCE LE TRADING CRYPTO • BITCOIN SOUS 67,000$ • SCAM ALERT • COINBASE PERTE • ",
        "events": "CALENDRIER : NFP 06/03 • CPI 11/03 • PCE 27/03 • "
    })

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --green: #00fa9a; --red: #ff4d4d; --bg: #000; --price-ivoire: #F5F5DC; --ui-grey: #222; }
        body { background: var(--bg); color: white; font-family: -apple-system, sans-serif; margin: 0; display: flex; justify-content: center; padding: 20px; overflow: hidden; }
        .app { width: 380px; display: flex; flex-direction: column; }
        
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px; }
        .indicators { display: flex; gap: 12px; }
        .ind { display: flex; flex-direction: column; align-items: center; width: 42px; position: relative; }
        .halo { position: absolute; width: 22px; height: 22px; border-radius: 50%; top: -7px; filter: blur(8px); opacity: 0.8; }
        .dot { width: 7px; height: 7px; border-radius: 50%; background: #222; margin-bottom: 6px; z-index: 1; }
        .dot.g { background: var(--green); box-shadow: 0 0 10px var(--green); }
        .dot.r { background: var(--red); box-shadow: 0 0 10px var(--red); }
        .ind span { font-size: 8px; color: #888; font-weight: 900; }
        
        .btn-group { display: flex; gap: 8px; }
        .btn { background: #000; border: 1px solid var(--ui-grey); color: #555; border-radius: 10px; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .btn.active { border-color: #fff !important; color: #fff !important; }
        .btn-a { width: 55px; height: 29px; font-size: 11px; }

        .price-wrap { text-align: center; margin-bottom: 25px; position: relative; }
        #price { font-size: 52px; font-weight: 500; color: var(--price-ivoire); letter-spacing: -1px; }
        .symbol { position: absolute; font-size: 16px; color: #888; font-weight: 800; top: 8px; margin-left: 8px; }
        #change { font-size: 18px; font-weight: 900; margin-top: -2px; display: flex; align-items: center; justify-content: center; gap: 5px; }

        .tabs { display: flex; gap: 8px; margin-bottom: 25px; }
        .tab { flex: 1; height: 38px; font-size: 10px; gap: 6px; }
        
        .c-icon { display: flex; flex-direction: column; align-items: center; width: 6px; color: inherit; }
        .c-wick { width: 1px; height: 2px; background: currentColor; }
        .c-body { width: 4px; height: 6px; border: 1px solid currentColor; }
        .active .c-body { background: currentColor; }

        .chart-container { position: relative; width: 100%; margin-bottom: 10px; }
        .chart-selector { position: absolute; top: -11px; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 10px; background: var(--bg); padding: 0 12px; z-index: 10; }
        .switch { position: relative; display: inline-block; width: 34px; height: 18px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #333; transition: .3s; border-radius: 20px; border: 1px solid #444; }
        .slider:before { position: absolute; content: ""; height: 10px; width: 10px; left: 3px; bottom: 3px; background-color: #fff; transition: .3s; border-radius: 50%; }
        input:checked + .slider:before { transform: translateX(16px); }
        .chart-box { width: 100%; height: 260px; background: #050505; border: 1px solid #222; border-radius: 35px; overflow: hidden; }
        canvas { width: 100%; height: 100%; }

        .pressure-block { margin: 15px 0 25px 0; display: flex; flex-direction: column; gap: 8px; }
        .pressure-labels { display: flex; justify-content: space-between; font-size: 10px; font-weight: 900; color: #444; }
        #pressure-signal { flex-grow: 1; text-align: center; height: 14px; display: flex; align-items: center; justify-content: center; gap: 5px; font-weight: 900; font-size: 11px; }
        .pressure-rail { width: 100%; height: 2px; background: #222; position: relative; }
        .cursor { position: absolute; height: 6px; top: -2px; border-radius: 2px; transform: translateX(-50%); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); min-width: 20px; }
        
        .z-crash { background: repeating-linear-gradient(45deg, #ff4d4d, #ff4d4d 6px, #4d0000 6px, #4d0000 12px); }
        .s-red { background: var(--red); }
        .z-neutre { background: repeating-linear-gradient(45deg, #ff4d4d, #ff4d4d 6px, #00fa9a 6px, #00fa9a 12px); }
        .s-green { background: var(--green); }
        .z-fomo { background: repeating-linear-gradient(45deg, #00fa9a, #00fa9a 6px, #004d30 6px, #004d30 12px); }

        .scroller-wrap { width: 100%; overflow: hidden; height: 14px; margin-bottom: 4px; position: relative; }
        .scroller-text { position: absolute; white-space: nowrap; font-size: 10px; font-weight: 900; left: 0; }
        #n1 { color: #8a7f94; }
        #n2 { color: #9867c9; }

        .macro-card { background: #060606; border: 1px solid #111; border-radius: 35px; padding: 22px; }
        .m-row { display: flex; align-items: center; margin-bottom: 6px; }
        .m-lbl { width: 110px; color: #888; font-size: 11px; font-weight: 800; }
        .m-val { flex-grow: 1; text-align: center; color: #eee; font-size: 14px; font-weight: 700; }
        .m-badge { width: 100px; border: 1px solid; border-radius: 8px; padding: 6px 0; font-size: 10px; font-weight: 900; text-align: center; }
        .brd-r { border-color: var(--red); color: var(--red); }
        .brd-g { border-color: var(--green); color: var(--green); }
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
            <div id="change">0.00%</div>
        </div>
        <div class="tabs">
            <div class="btn tab active" onclick="setTab(this, '1m')">1MN <div class="c-icon"><div class="c-wick"></div><div class="c-body"></div><div class="c-wick"></div></div></div>
            <div class="btn tab" onclick="setTab(this, '15m')">15MN <div class="c-icon"><div class="c-wick"></div><div class="c-body"></div><div class="c-wick"></div></div></div>
            <div class="btn tab" onclick="setTab(this, '1h')">1HRE <div class="c-icon"><div class="c-wick"></div><div class="c-body"></div><div class="c-wick"></div></div></div>
        </div>
        <div class="chart-container">
            <div class="chart-selector">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="3"><path d="M3 17l6-6 4 4 8-8"/></svg>
                <label class="switch"><input type="checkbox" id="chartTypeToggle" onchange="updateChart()"><span class="slider"></span></label>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="3"><path d="M6 5v14M10 3v18M14 6v12M18 4v16"/></svg>
            </div>
            <div class="chart-box"><canvas id="chart"></canvas></div>
        </div>
        <div class="pressure-block">
            <div class="pressure-labels"><span>SURVENTE</span><span id="pressure-signal">MARCHÉ</span><span>SURACHAT</span></div>
            <div class="pressure-rail"><div id="market-cursor" class="cursor z-neutre" style="left: 50%;"></div></div>
        </div>
        <div class="scroller-wrap"><div id="n1" class="scroller-text"></div></div>
        <div class="scroller-wrap"><div id="n2" class="scroller-text"></div></div>
        <div class="macro-card" id="macro-list"></div>
    </div>

    <script>
        const canvas = document.getElementById('chart'), ctx = canvas.getContext('2d');
        let currentSymbol = "ETHUSDT", currentInterval = "1m", pos1 = 0, pos2 = 0;

        function setAsset(el) { document.querySelectorAll('.btn-a').forEach(b => b.classList.remove('active')); el.classList.add('active'); currentSymbol = el.innerText + "USDT"; updateAll(); }
        function setTab(el, interval) { document.querySelectorAll('.tab').forEach(b => b.classList.remove('active')); el.classList.add('active'); currentInterval = interval; updateAll(); }

        function animate() {
            const el1 = document.getElementById('n1'), el2 = document.getElementById('n2');
            if(el1 && el1.offsetWidth > 0) { pos1 -= 0.8; if (Math.abs(pos1) >= el1.offsetWidth / 2) pos1 = 0; el1.style.transform = `translateX(${pos1}px)`; }
            if(el2 && el2.offsetWidth > 0) { pos2 -= 0.6; if (Math.abs(pos2) >= el2.offsetWidth / 2) pos2 = 0; el2.style.transform = `translateX(${pos2}px)`; }
            requestAnimationFrame(animate);
        }

        async function updateIndicators() {
            const periods = ['1m', '15m', '1h'];
            for(let i=0; i<3; i++) {
                try {
                    const r = await fetch(`https://api.binance.com/api/v3/klines?symbol=${currentSymbol}&interval=${periods[i]}&limit=2`);
                    const d = await r.json(); const bull = parseFloat(d[1][4]) >= parseFloat(d[0][4]);
                    document.getElementById(`d${i+1}`).className = bull ? 'dot g' : 'dot r';
                    document.getElementById(`h${i+1}`).style.background = bull ? '#00fa9a' : '#ff4d4d';
                } catch(e){}
            }
        }

        async function updateChart() {
            try {
                const r = await fetch(`https://api.binance.com/api/v3/klines?symbol=${currentSymbol}&interval=${currentInterval}&limit=100`);
                const data = await r.json();
                const candles = data.map(d => ({ t: d[0], o: parseFloat(d[1]), h: parseFloat(d[2]), l: parseFloat(d[3]), c: parseFloat(d[4]) }));
                const last = candles[candles.length-1].c, first = candles[candles.length-60].c, pct = ((last-first)/first)*100;
                document.getElementById('price').innerText = last.toLocaleString('fr-FR', {minimumFractionDigits:2});
                
                // --- LOGIQUE VARIATION AVEC SYMBOLE ---
                const c = document.getElementById('change');
                const arrow = pct >= 0 ? '▲' : '▼';
                c.innerText = `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}% ${arrow}`;
                c.style.color = pct >= 0 ? '#00fa9a' : '#ff4d4d';
                
                draw(candles); updatePressureLogic(pct);
            } catch(e){}
        }

        function updatePressureLogic(pct) {
            const cursor = document.getElementById('market-cursor'), signal = document.getElementById('pressure-signal');
            let cfg = { cls: "z-neutre", msg: "⚖️ ZONE NEUTRE", col: "#444" };
            if (pct <= -1.5) cfg = { cls: "z-crash", msg: "🔴 ALERTE : CRASH IMMINENT", col: "var(--red)" };
            else if (pct <= -0.3) cfg = { cls: "s-red", msg: "🔴 SURVENTE : PRÉPARER ACHAT", col: "var(--red)" };
            else if (pct >= 1.5) cfg = { cls: "z-fomo", msg: "🟢 SURACHAT : PRISES DE PROFITS", col: "var(--green)" };
            else if (pct >= 0.3) cfg = { cls: "s-green", msg: "🟢 PRESSION : ACHAT SUR REPLI", col: "var(--green)" };
            const noise = (Math.random() * 5);
            const sensitiveWidth = Math.min(Math.max(25 + (Math.abs(pct) * 120) + noise, 30), 150);
            cursor.className = `cursor ${cfg.cls}`;
            cursor.style.width = `${sensitiveWidth}px`;
            cursor.style.left = `${Math.min(Math.max(50 + (pct * 35), 15), 85)}%`;
            signal.innerHTML = cfg.msg; signal.style.color = cfg.col;
        }

        function draw(candles) {
            canvas.width = canvas.clientWidth * 2; canvas.height = canvas.clientHeight * 2;
            ctx.scale(2,2); const w = canvas.clientWidth, h = canvas.clientHeight;
            const isCandle = document.getElementById('chartTypeToggle').checked, display = candles.slice(-60);
            let tech = [];
            for(let i=0; i<60; i++) {
                const slice = candles.slice(40+i-20, 40+i).map(d => d.c);
                const ma = slice.reduce((a,b)=>a+b,0)/20, std = Math.sqrt(slice.map(v=>Math.pow(v-ma,2)).reduce((a,b)=>a+b,0)/20);
                tech.push({ ma, up: ma+(std*2), low: ma-(std*2) });
            }
            const allP = [...display.flatMap(d=>[d.h,d.l]), ...tech.flatMap(t=>[t.up,t.low])];
            const min = Math.min(...allP), max = Math.max(...allP), range = max-min;
            const pR=55, pT=30, pB=35, pL=10, cW=w-pR-pL, cH=h-pT-pB;
            const getX = (i) => pL + (i/59)*cW, getY = (p) => pT + cH - ((p-min)/range * cH);
            ctx.clearRect(0,0,w,h); 
            ctx.strokeStyle="#181818"; ctx.lineWidth=1; ctx.font="9px Inter"; ctx.fillStyle="#444";
            for(let i=0; i<=4; i++) {
                let y = pT + (cH*(i/4)); ctx.beginPath(); ctx.moveTo(pL,y); ctx.lineTo(pL+cW,y); ctx.stroke();
                ctx.fillText((max-(range*(i/4))).toFixed(2), pL+cW+8, y+3);
            }
            for(let i=0; i<60; i+=15) {
                let x = getX(i); ctx.beginPath(); ctx.moveTo(x, pT); ctx.lineTo(x, pT+cH); ctx.stroke();
                let d = new Date(display[i].t);
                let time = d.getHours()+":"+String(d.getMinutes()).padStart(2,'0');
                if(currentInterval === '1h') time = d.getDate() + " fév. " + time;
                ctx.fillText(time, x, h-12);
            }
            if(isCandle) {
                ctx.strokeStyle = "rgba(163, 73, 164, 0.7)"; ctx.lineWidth = 1;
                ctx.beginPath(); tech.forEach((t,i)=>i===0?ctx.moveTo(getX(i),getY(t.up)):ctx.lineTo(getX(i),getY(t.up))); ctx.stroke();
                ctx.beginPath(); tech.forEach((t,i)=>i===0?ctx.moveTo(getX(i),getY(t.low)):ctx.lineTo(getX(i),getY(t.low))); ctx.stroke();
                display.forEach((d,i) => {
                    let x=getX(i), yO=getY(d.o), yC=getY(d.c), yH=getY(d.h), yL=getY(d.l), col=d.c>=d.o?'#00fa9a':'#ff4d4d';
                    ctx.strokeStyle=col; ctx.beginPath(); ctx.moveTo(x,yH); ctx.lineTo(x,yL); ctx.stroke();
                    ctx.fillStyle=col; ctx.fillRect(x-2, Math.min(yO,yC), 4, Math.max(Math.abs(yO-yC),1));
                });
            } else {
                display.forEach((d,i) => {
                    let color = d.c >= d.o ? '0, 250, 154' : '255, 77, 77';
                    let x = getX(i); let grad = ctx.createLinearGradient(0, getY(d.c), 0, pT+cH);
                    grad.addColorStop(0, `rgba(${color}, 0.5)`); grad.addColorStop(1, `rgba(${color}, 0)`);
                    ctx.fillStyle = grad; ctx.fillRect(x-2, getY(d.c), 4, (pT+cH) - getY(d.c));
                });
                ctx.lineWidth = 1.2;
                for(let i=1; i<60; i++) {
                    ctx.strokeStyle = display[i].c >= display[i-1].c ? '#00fa9a' : '#ff4d4d';
                    ctx.beginPath(); ctx.moveTo(getX(i-1), getY(display[i-1].c)); ctx.lineTo(getX(i), getY(display[i].c)); ctx.stroke();
                }
            }
            ctx.setLineDash([2, 2]); ctx.strokeStyle = "rgba(255, 255, 0, 0.8)"; ctx.lineWidth = 1.2;
            ctx.beginPath(); tech.forEach((t,i)=>i===0?ctx.moveTo(getX(i),getY(t.ma)):ctx.lineTo(getX(i),getY(t.ma))); ctx.stroke();
            ctx.setLineDash([]);
        }

        async function loadMacro() {
            try {
                const r = await fetch('/api/macro'); const d = await r.json();
                document.getElementById('n1').innerText = (d.news_top).repeat(3);
                document.getElementById('n2').innerText = (d.events).repeat(3);
                document.getElementById('macro-list').innerHTML = `
                    <div class="m-row"><span class="m-lbl">TAUX FED</span><span class="m-val">${d.fed}%</span><div class="m-badge brd-r">RESTRICTIF</div></div>
                    <div class="m-row"><span class="m-lbl">INFLATION</span><span class="m-val">${d.inf}%</span><div class="m-badge brd-r">CIBLE 2%</div></div>
                    <div class="m-row"><span class="m-lbl">INDEX USD</span><span class="m-val">${d.dxy}</span><div class="m-badge brd-g">REPLI</div></div>
                    <div class="m-row"><span class="m-lbl">SENTIMENT</span><span class="m-val">${d.fg}/100</span><div class="m-badge brd-r">PEUR</div></div>`;
            } catch(e){}
        }

        function updateAll() { updateChart(); updateIndicators(); loadMacro(); }
        setInterval(updateAll, 5000); updateAll(); animate();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
