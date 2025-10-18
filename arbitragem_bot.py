import ccxt
import requests
import time

TELEGRAM_TOKEN = "8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10"
CHAT_ID = "1809414360"
SPREAD_MIN = 0.04
MOEDAS = [
    "BTC", "ETH", "USDT", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT",
    "MATIC", "LTC", "SHIB", "AVAX", "LINK", "TRX", "UNI", "CRO", "XLM",
    "ALGO", "ATOM", "VET", "FIL", "ICP", "AAVE", "EOS", "THETA", "SAND",
    "MANA", "GRT", "CHZ", "FTM", "ONE", "NEAR", "XMR", "ZEC", "BAT", "ENJ",
    "WAVES", "KSM", "LUNA", "AR", "CELO", "HBAR", "RUNE", "NEO", "OKB", "HT",
    "FTT", "IOTA", "QTUM", "DCR", "SC", "ZIL", "KNC", "REN", "BAL", "CRV",
    "SNX", "SUSHI", "YFI", "1INCH", "COMP", "MKR", "LRC", "OMG", "STX", "RVN",
    "HNT", "GALA", "MINA", "LSK", "XTZ", "XEM", "KAVA", "ANKR", "OCEAN", "CVC",
    "KSM", "DGB", "CHR", "STORJ", "BAT", "ICX", "NANO", "ZRX"
]

mexc = ccxt.mexc({
    "apiKey": "mx0vgldPupiJEgujR5",
    "secret": "e610a1a511014832a3ff152efdd04257"
})

bitmart = ccxt.bitmart({
    "apiKey": "6130d4bc0778badd1b009cc7884b0c8e6ed6ca1b",
    "secret": "be764e831caea80e4e0e2f259429af37938893e1efebc7e1c04bc668fdd0cd30"
})

def enviar_telegram(exchange_compra, moeda_compra, exchange_venda, moeda_venda, spread):
    mensagem = (
        "☢️ OPORTUNIDADE ENCONTRADA\n\n"
        f"🟢 COMPRAR - {exchange_compra} :\n{moeda_compra}/USDT\n"
        f"🔴 VENDER - {exchange_venda} :\n{moeda_venda}/USDT\n\n"
        f"➡️ SPREAD ESPERADO: {spread:.2f}%"
    )
    url = f"https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
    data = {"chat_id": "1809414360", "text": mensagem}
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
    
    for moeda in MOEDAS:
        if moeda in precos_mexc and moeda in precos_bitmart:
            preco_mexc = precos_mexc[moeda]
            preco_bitmart = precos_bitmart[moeda]
            
            if preco_mexc > preco_bitmart * (1 + SPREAD_MIN):
                spread_percent = ((preco_mexc / preco_bitmart) - 1) * 100
                enviar_telegram("BitMart", moeda, "MEXC", moeda, spread_percent)
            elif preco_bitmart > preco_mexc * (1 + SPREAD_MIN):
                spread_percent = ((preco_bitmart / preco_mexc) - 1) * 100
                enviar_telegram("MEXC", moeda, "BitMart", moeda, spread_percent)
            
            for moeda2 in MOEDAS:
                if moeda2 == moeda:
                    continue
                if moeda2 in precos_mexc and moeda2 in precos_bitmart:
                    preco2_mexc = precos_mexc[moeda2]
                    preco2_bitmart = precos_bitmart[moeda2]

                    if preco_bitmart * (1 + SPREAD_MIN) < preco2_mexc:
                        spread_percent = ((preco2_mexc / preco_bitmart) - 1) * 100
                        enviar_telegram("BitMart", moeda, "MEXC", moeda2, spread_percent)
                    if preco_mexc * (1 + SPREAD_MIN) < preco2_bitmart:
                        spread_percent = ((preco2_bitmart / preco_mexc) - 1) * 100
                        enviar_telegram("MEXC", moeda, "BitMart", moeda2, spread_percent)

if __name__ == "__main__":
    while True:
        try:
            analisar_arbitragem()
        except Exception as e:
            url = f"https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
            requests.post(url, data={"chat_id": "1809414360", "text": f"Erro no bot: {e}"})
        time.sleep(60)
