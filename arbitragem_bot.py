import ccxt
import time
import requests

BITMART_API_KEY = "6130d4bc0778badd1b009cc7884b0c8e6ed6ca1b"
BITMART_SECRET_KEY = "be764e831caea80e4e0e2f259429af37938893e1efebc7e1c04bc668fdd0cd30"
MEXC_API_KEY = "mx0vgldPupiJEgujR5"
MEXC_SECRET_KEY = "e610a1a511014832a3ff152efdd04257"
TELEGRAM_TOKEN = "8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10"
CHAT_ID = "1809414360"
SPREAD_MIN = 3.0

bitmart = ccxt.bitmart({
    'apiKey': BITMART_API_KEY,
    'secret': BITMART_SECRET_KEY
})

mexc = ccxt.mexc({
    'apiKey': MEXC_API_KEY,
    'secret': MEXC_SECRET_KEY
})

bitmart.load_markets()
mexc.load_markets()
PAIRS = list(set(bitmart.symbols) & set(mexc.symbols))

def enviar_mensagem(msg):
    url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
    data = {"chat_id": "1809414360", "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Erro enviar_mensagem: {e}")

while True:
    for par in PAIRS:
        try:
            bm_order = bitmart.fetch_order_book(par)
            mx_order = mexc.fetch_order_book(par)

            bm_ask = bm_order['asks'][0][0] if bm_order['asks'] else None
            bm_bid = bm_order['bids'][0][0] if bm_order['bids'] else None
            mx_ask = mx_order['asks'][0][0] if mx_order['asks'] else None
            mx_bid = mx_order['bids'][0][0] if mx_order['bids'] else None

            if bm_ask and mx_bid:
                spread = ((mx_bid - bm_ask) / bm_ask) * 100
                if spread >= SPREAD_MIN:
                    msg = (
                        f"🟢 COMPRAR na BITMART\n"
                        f"Moeda: {par}\n💰 Preço: {bm_ask:.6f}\n\n"
                        f"➡️ TRANSFERIR para MEXC\n"
                        f"💰 VENDER em: {mx_bid:.6f}\n\n"
                        f"📊 SPREAD ESPERADO: +{spread:.2f}%"
                    )
                    enviar_mensagem(msg)
                else:
                    print(f"⚪ {par} analisado → Spread atual: +{spread:.2f}%")

            if mx_ask and bm_bid:
                spread = ((bm_bid - mx_ask) / mx_ask) * 100
                if spread >= SPREAD_MIN:
                    msg = (
                        f"🟢 COMPRAR na MEXC\n"
                        f"Moeda: {par}\n💰 Preço: {mx_ask:.6f}\n\n"
                        f"➡️ TRANSFERIR para BITMART\n"
                        f"💰 VENDER em: {bm_bid:.6f}\n\n"
                        f"📊 SPREAD ESPERADO: +{spread:.2f}%"
                    )
                    enviar_mensagem(msg)
                else:
                    print(f"⚪ {par} analisado → Spread atual: +{spread:.2f}%")

        except Exception as e:
            print(f"Erro ao processar {par}: {e}")

    time.sleep(2)
