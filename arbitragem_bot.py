import ccxt
import requests
import time
from datetime import datetime

TELEGRAM_TOKEN = "8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10"
CHAT_ID = "1809414360"
SPREAD_MIN = 1.0
VOLUME_MIN = 10000
DELAY = 5

MEXC_API_KEY = "mx0vgldd1b0f5b30b8cd99a3b5a2c69b8"
MEXC_SECRET_KEY = "b7dd86e6f9c741f1b4e5d3bb5aa604af"

mexc = ccxt.mexc({
    'apiKey': "mx0vgldd1b0f5b30b8cd99a3b5a2c69b8",
    'secret': "b7dd86e6f9c741f1b4e5d3bb5aa604af"
})

def enviar_telegram(mensagem):
    url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
    data = {"chat_id": "1809414360", "text": mensagem, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def obter_precos(exchange):
    precos = {}
    tickers = exchange.fetch_tickers()
    for simbolo, dados in tickers.items():
        if "bid" in dados and "ask" in dados and dados["bid"] and dados["ask"] and dados.get("quoteVolume"):
            precos[simbolo] = {"bid": dados["bid"], "ask": dados["ask"], "volume": dados["quoteVolume"]}
    return precos

def obter_saldo_usdt(exchange):
    try:
        saldo = exchange.fetch_balance()
        return saldo["free"].get("USDT", 0)
    except:
        return 0

def executar_ciclo(exchange, base, quote2, nome_corretora):
    try:
        saldo = obter_saldo_usdt(exchange)
        if saldo <= 0:
            return

        par1 = f"{base}/USDT"
        par2 = f"{base}/{quote2}"
        par3 = f"{quote2}/USDT"

        preco1 = exchange.fetch_ticker(par1)["ask"]
        qtd_base = saldo / preco1
        exchange.create_order(par1, "market", "buy", qtd_base)

        preco2 = exchange.fetch_ticker(par2)["bid"]
        qtd_quote2 = qtd_base * preco2
        exchange.create_order(par2, "market", "sell", qtd_base)

        preco3 = exchange.fetch_ticker(par3)["bid"]
        qtd_usdt_final = qtd_quote2 * preco3
        exchange.create_order(par3, "market", "sell", qtd_quote2)

        lucro = qtd_usdt_final - saldo
        mensagem = (
            f"📢 **ARBITRAGEM EXECUTADA ({nome_corretora})**\n"
            f"💱 **Ciclo:** USDT → {base} → {quote2} → USDT\n"
            f"📊 **Lucro obtido:** +{lucro:.2f} USDT\n"
            f"🏦 **Saldo inicial:** {saldo:.2f} USDT\n"
            f"🏦 **Saldo final estimado:** {qtd_usdt_final:.2f} USDT\n"
            f"🕒 **Horário:** {datetime.now().strftime('%H:%M:%S')}"
        )
        print(mensagem)
        enviar_telegram(mensagem)
    except Exception as e:
        print(f"Erro no ciclo {nome_corretora}: {e}")

def verificar_arbitragem(exchange, nome_corretora):
    precos = obter_precos(exchange)
    usdt_pairs = {s: v for s, v in precos.items() if s.endswith("/USDT")}
    bases = [s.split("/")[0] for s in usdt_pairs.keys()]
    for base in bases:
        par1 = f"{base}/USDT"
        if par1 not in precos or precos[par1]["volume"] < VOLUME_MIN:
            continue
        for par2, v2 in precos.items():
            if par2.startswith(base + "/") and not par2.endswith("/USDT"):
                quote2 = par2.split("/")[1]
                par3 = f"{quote2}/USDT"
                if par3 not in precos:
                    continue
                preco_compra = precos[par1]["ask"]
                preco_intermediario = precos[par2]["bid"]
                preco_venda = precos[par3]["bid"]
                ganho = preco_venda * (preco_intermediario / preco_compra)
                spread = ((ganho - preco_compra) / preco_compra) * 100
                if spread >= SPREAD_MIN:
                    executar_ciclo(exchange, base, quote2, nome_corretora)

def iniciar_arbitragem():
    print("🟢 Bot de Arbitragem Interna (MEXC) Iniciado com Sucesso!\n")
    while True:
        verificar_arbitragem(mexc, "MEXC")
        time.sleep(DELAY)

iniciar_arbitragem()
