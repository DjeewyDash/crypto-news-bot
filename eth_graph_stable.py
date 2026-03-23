import sys
import json
import time
import threading
import websocket
import requests
import feedparser
from collections import deque
from datetime import datetime

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

# ================== CONFIG ==================
DUREE_MICRO = 180
DUREE_LONG = 10800

SEUIL_PENTE_MICRO = 0.006
SEUIL_PENTE_LONG = 0.002
SEUIL_ACCEL_MICRO = 1.15
SEUIL_ACCEL_LONG = 1.05

RSS_FEEDS = ["https://www.federalreserve.gov/feeds/press_all.xml"]

# ================== CONFIG FRED ==================
with open("config.json") as f:
    cfg = json.load(f)

FRED_API_KEY = cfg["FRED_API_KEY"]
FRED_SERIES = {"FED": "FEDFUNDS", "CPI": "CPIAUCSL"}

# ================== MÉMOIRE ==================
prix_memoire = deque()
prix_lock = threading.Lock()

macro_info = ""
rss_info = []
news_ticker_text = ""
ticker_index = 0

mode_trading = "MICRO"
crypto = "ETH"
signal_courant = "ATTENDRE"

# ================== FENÊTRE ==================
app = QtWidgets.QApplication(sys.argv)
win = QtWidgets.QMainWindow()
win.setWindowTitle("Crypto Trader ETH/BTC")
win.resize(1200, 850)

central_widget = QtWidgets.QWidget()
win.setCentralWidget(central_widget)
layout = QtWidgets.QVBoxLayout()
central_widget.setLayout(layout)

# ================== GRAPH ==================
pg.setConfigOptions(antialias=True)
plot_widget = pg.PlotWidget()
layout.addWidget(plot_widget)
plot_widget.showGrid(x=True, y=True, alpha=0.3)
plot_widget.setLabel('left', "Prix (USDT)")
plot_widget.addLegend()

ligne_prix = plot_widget.plot([], [], pen=pg.mkPen('c', width=1.5), name="Prix")
ligne_moy   = plot_widget.plot([], [], pen=pg.mkPen('orange', style=QtCore.Qt.DashLine, width=2), name="Moyenne")

# ================== BLOC TEXTE ==================
text_proxy_layout = pg.GraphicsLayoutWidget()
layout.addWidget(text_proxy_layout)

# LabelItems dans un GraphicsLayout pour éviter l'erreur addWidget
texte_barre = pg.LabelItem(justify='center', size='12pt', bold=True)
texte_macro = pg.LabelItem(justify='center', size='12pt', color='orange', bold=True)
texte_rss   = pg.LabelItem(justify='left', size='9pt', color='lightgray')

text_proxy_layout.addItem(texte_barre)
text_proxy_layout.nextRow()
text_proxy_layout.addItem(texte_macro)
text_proxy_layout.nextRow()
text_proxy_layout.addItem(texte_rss)
text_proxy_layout.nextRow()

# ================== TICKER BLEU ==================
texte_news = pg.LabelItem(justify='left', size='10pt', color='lightblue')
layout.addWidget(texte_news)

# ================== BOUTONS ==================
btn_layout = QtWidgets.QHBoxLayout()
layout.addLayout(btn_layout)
btn_mode = QtWidgets.QPushButton("MICRO-TRAD")
btn_crypto = QtWidgets.QPushButton(crypto)
btn_mode.setStyleSheet("font-weight:bold; background-color:#4B2E2E; color:white")
btn_crypto.setStyleSheet("font-weight:bold; background-color:#8A2BE2; color:white")
btn_layout.addWidget(btn_mode)
btn_layout.addWidget(btn_crypto)

# ================== FLÈCHES ==================
fleche_haut = pg.TextItem("▲", color='gray', anchor=(0.5, 0.5))
fleche_bas  = pg.TextItem("▼", color='gray', anchor=(0.5, 0.5))
plot_widget.addItem(fleche_haut)
plot_widget.addItem(fleche_bas)

# ================== FONCTIONS ==================
def get_duree(): return DUREE_MICRO if mode_trading=="MICRO" else DUREE_LONG
def get_seuil_pente(): return SEUIL_PENTE_MICRO if mode_trading=="MICRO" else SEUIL_PENTE_LONG
def get_seuil_accel(): return SEUIL_ACCEL_MICRO if mode_trading=="MICRO" else SEUIL_ACCEL_LONG

def sma(prixs):
    return [sum(prixs[:i+1])/(i+1) for i in range(len(prixs))]

def ema(prixs, period):
    if len(prixs)<period: return prixs[:]
    ema_vals = [prixs[0]]
    k = 2/(period+1)
    for p in prixs[1:]:
        ema_vals.append(p*k + ema_vals[-1]*(1-k))
    return ema_vals

def moyenne_mobile(prixs):
    if mode_trading=="LONG":
        if len(prixs)>=50:
            indices = [int(i*len(prixs)/50) for i in range(50)]
            sampled = [prixs[i] for i in indices]
            return ema(sampled,50)
        else:
            return prixs
    else:
        return sma(prixs) if mode_trading=="MICRO" else ema(prixs,50)

def pente(moy):
    n = 20 if mode_trading=="MICRO" else 60
    return moy[-1]-moy[-n] if len(moy)>=n else 0

def acceleration(prixs):
    if len(prixs)<100: return 1
    return abs(prixs[-1]-prixs[-20])/max(abs(prixs[-40]-prixs[-80]),0.1)

# ================== MACRO & RSS ==================
def check_macro():
    global macro_info
    infos=[]
    for key, serie in FRED_SERIES.items():
        try:
            r = requests.get(
                f"https://api.stlouisfed.org/fred/series/observations"
                f"?series_id={serie}&api_key={FRED_API_KEY}&file_type=json",
                timeout=5
            )
            val=float(r.json()["observations"][-1]["value"])
            infos.append(f"{key} {val:.2f}%")
        except:
            infos.append(f"{key} indispo")
    macro_info = " | ".join(infos)

def update_rss():
    global rss_info, news_ticker_text
    rss_info=[]
    for feed in RSS_FEEDS:
        try:
            d=feedparser.parse(feed)
            rss_info=[f"{e.published[:16]} {e.title}" for e in d.entries[:3]]
            news_ticker_text = "   |   ".join([e.title for e in d.entries[:5]]) + "   "
        except:
            news_ticker_text = ""

# ================== UPDATE GRAPHIQUE ==================
def update_plot():
    global ticker_index, signal_courant

    with prix_lock:
        data = list(prix_memoire)
    if len(data)<10: 
        QtCore.QTimer.singleShot(100, update_plot)
        return

    temps = [t for t,_ in data]
    prixs = [p for _,p in data]
    moy = moyenne_mobile(prixs)

    ligne_prix.setData(temps, prixs)
    ligne_moy.setData(temps, moy)

    # Signal
    p=pente(moy)
    acc=acceleration(prixs)
    if p>get_seuil_pente() and acc>get_seuil_accel():
        signal_courant="ACHETER"
    elif p<-get_seuil_pente() and acc>get_seuil_accel():
        signal_courant="VENDRE"
    else:
        signal_courant="ATTENDRE"

    variation=(prixs[-1]-prixs[0])/prixs[0]*100
    fleche = "▲" if variation>=0 else "▼"
    couleur = "lime" if signal_courant=="ACHETER" else "red" if signal_courant=="VENDRE" else "white"

    texte_barre.setText(f"{crypto}/USDT {prixs[-1]:.2f}$ ({variation:+.2f}%) {fleche} | {mode_trading} | {signal_courant}")
    texte_barre.setColor(couleur)

    # Macro / RSS
    check_macro()
    texte_macro.setText(macro_info)
    update_rss()
    texte_rss.setText("\n".join(rss_info))

    # Ticker bleu
    if news_ticker_text:
        ticker_index = (ticker_index + 1) % len(news_ticker_text)
        display_text = news_ticker_text[ticker_index:] + news_ticker_text[:ticker_index]
        texte_news.setText(display_text)

    QtCore.QTimer.singleShot(50, update_plot)

# ================== BINANCE ==================
def flux_binance():
    global prix_memoire
    url=f"wss://stream.binance.com:9443/ws/{crypto.lower()}usdt@trade"

    def on_message(ws,msg):
        data=json.loads(msg)
        t=time.time()
        with prix_lock:
            prix_memoire.append((t,float(data["p"])))
            while prix_memoire and t-prix_memoire[0][0]>get_duree():
                prix_memoire.popleft()

    ws=websocket.WebSocketApp(url,on_message=on_message)
    ws.run_forever()

def restart_flux():
    threading.Thread(target=flux_binance, daemon=True).start()

restart_flux()

# ================== BOUTONS ==================
def toggle_mode():
    global mode_trading
    mode_trading = "LONG" if mode_trading=="MICRO" else "MICRO"
    btn_mode.setText("LONG-TRAD" if mode_trading=="LONG" else "MICRO-TRAD")
btn_mode.clicked.connect(toggle_mode)

def toggle_crypto():
    global crypto
    crypto = "BTC" if crypto=="ETH" else "ETH"
    btn_crypto.setText(crypto)
    restart_flux()
btn_crypto.clicked.connect(toggle_crypto)

# ================== LANCEMENT ==================
update_plot()
win.show()
sys.exit(app.exec_())

