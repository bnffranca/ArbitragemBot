import ccxt
import requests
import time
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SPREAD_MIN = 0.015
MAX_SINAIS = 2
INTERVALO = 120

MOEDAS = [
    "BTC", "ETH", "USDT", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT",
    "MATIC", "LTC", "SHIB", "AVAX", "LINK", "TRX", "UNI", "CRO", "XLM",
    "ALGO", "ATOM", "VET", "FIL", "ICP", "AAVE", "EOS", "THETA", "SAND",
    "MANA", "GRT", "CHZ", "FTM", "ONE", "NEAR", "XMR", "ZEC", "BAT", "ENJ",
    "WAVES", "KSM", "LUNA", "AR", "CELO", "HBAR", "RUNE", "NEO", "OKB", "HT",
    "FTT", "IOTA", "QTUM", "DCR", "SC", "ZIL", "KNC", "REN", "BAL", "CRV",
    "SNX", "SUSHI", "YFI", "1INCH", "COMP", "MKR", "LRC", "OMG", "STX", "RVN",
    "HNT", "GALA", "MINA", "LSK", "XTZ", "XEM", "KAVA", "ANKR", "OCEAN", "CVC",
    "DGB", "CHR", "STORJ", "ICX", "NANO", "ZRX"
]

mexc = ccxt.mexc({
    "apiKey": os.getenv("MEXC_API_KEY"),
    "secret": os.getenv("MEXC_SECRET_KEY")
})

bitmart = ccxt.bitmart({
    "apiKey": os.getenv("BITMART_API_KEY"),
    "secret": os.getenv("BITMART_SECRET_KEY")
})

def enviar_telegram(exchange_compra, moeda_compra, exchange_venda, moeda_venda, spread):
    mensagem = (
        "☢️ OPORTUNIDADE ENCONTRADA\n\n"
        f"🟢 COMPRAR - {exchange_compra} :\n{moeda_compra}/USDT\n"
        f"🔴 VENDER - {exchange_venda} :\n{moeda_venda}/USDT\n\n"
        f"➡️ SPREAD ESPERADO: {spread:.2f}%"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem}
    requests.post(url, data=data)

def obter_precos(exchange, moedas):
    precos = {}
    for moeda in moedas:
        try:
            ticker = exchange.fetch_ticker(moeda + "/USDT")
            precos[moeda] = ticker["last"]
        except:
            continue
    return precos

def analisar_arbitragem():
    precos_mexc = obter_precos(mexc, MOEDAS)
    precos_bitmart = obter_precos(bitmart, MOEDAS)
    oportunidades = []

    for moeda in MOEDAS:
        if moeda not in precos_mexc or moeda not in precos_bitmart:
            continue
        preco_mexc = precos_mexc[moeda]
        preco_bitmart = precos_bitmart[moeda]

        if preco_mexc > preco_bitmart * (1 + SPREAD_MIN):
            spread = ((preco_mexc / preco_bitmart) - 1) * 100
            oportunidades.append(("BitMart", moeda, "MEXC", moeda, spread))
        elif preco_bitmart > preco_mexc * (1 + SPREAD_MIN):
            spread = ((preco_bitmart / preco_mexc) - 1) * 100
            oportunidades.append(("MEXC", moeda, "BitMart", moeda, spread))

    oportunidades = [op for op in oportunidades if op[4] >= SPREAD_MIN * 100]
    oportunidades.sort(key=lambda x: x[4], reverse=True)

    for op in oportunidades[:MAX_SINAIS]:
        enviar_telegram(*op)

if __name__ == "__main__":
    while True:
        try:
            analisar_arbitragem()
        except Exception as e:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": f"Erro no bot: {e}"})
        time.sleep(INTERVALO)

          
