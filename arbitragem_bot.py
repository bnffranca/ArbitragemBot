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

def enviar_mensagem(msg):
    url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
    data = {"chat_id": "1809414360", "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception:
        pass

mexc_public = ccxt.mexc({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot', 'fetchCurrencies': False}
})

mexc_auth = ccxt.mexc({
    'apiKey': "mx0vgldPupiJEgujR5",
    'secret': "e610a1a511014832a3ff152efdd04257",
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

bitmart = ccxt.bitmart({
    'apiKey': "6130d4bc0778badd1b009cc7884b0c8e6ed6ca1b",
    'secret': "be764e831caea80e4e0e2f259429af37938893e1efebc7e1c04bc668fdd0cd30",
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def ler_saldo_mexc():
    try:
        mexc_auth.load_time_difference()
        bal = mexc_auth.fetch_balance({'recvWindow': 5000})
        usdt = float(bal['total'].get('USDT', 0) or 0)
        return usdt
    except Exception:
        return 0.0

def topo(orderbook, side):
    ob = orderbook['asks'] if side == 'ask' else orderbook['bids']
    if not ob:
        return None, None, None
    price, amount = ob[0][0], ob[0][1]
    if price is None or amount is None:
        return None, None, None
    value_usdt = float(price) * float(amount)
    return float(price), float(amount), float(value_usdt)

def spread_duas_casas(preco_origem, preco_destino):
    if preco_origem is None or preco_destino is None:
        return None
    if preco_origem <= 0 or preco_destino <= 0:
        return None
    s = ((preco_destino - preco_origem) / preco_origem) * 100.0
    return round(s, 2)

print("🟢 Bot de Arbitragem iniciado com sucesso!")
print("🎯 Modo: Compra na MEXC → PAGAR na BITMART (Spot /USDT)")
print(f"📊 Spread mínimo: {SPREAD_MIN:.2f}%")
print("==================================================")

try:
    mexc_public.load_markets()
    bitmart.load_markets()
except Exception as e:
    print(f"Erro ao carregar mercados: {e}")

mexc_usdt = {s for s in mexc_public.symbols if s.endswith("/USDT")}
bitmart_usdt = {s for s in bitmart.symbols if s.endswith("/USDT")}
mexc_bases = {s.split('/')[0] for s in mexc_usdt}
bitmart_bases = {s.split('/')[0] for s in bitmart_usdt}
bases_comuns = sorted(list(mexc_bases & bitmart_bases))

if not bases_comuns:
    print("⚠️ Nenhuma moeda pagadora em comum encontrada (bases em /USDT).")
else:
    print(f"🎯 Moedas pagadoras em comum (existem na MEXC e na BitMart): {len(bases_comuns)}")

indice = 0
saldo_cache = ler_saldo_mexc()

while True:
    try:
        if indice % 30 == 0:
            saldo_cache = ler_saldo_mexc()

        if not bases_comuns:
            time.sleep(2)
            continue

        base = bases_comuns[indice % len(bases_comuns)]
        indice += 1
        par = f"{base}/USDT"

        try:
            mx_order = mexc_public.fetch_order_book(par)
        except Exception as e:
            print(f"Erro ao obter book MEXC para {par}: {e}")
            time.sleep(0.2)
            continue

        try:
            bm_order = bitmart.fetch_order_book(par)
        except Exception as e:
            print(f"Erro ao obter book BitMart para {par}: {e}")
            time.sleep(0.2)
            continue

        mx_ask, mx_amt, mx_val = topo(mx_order, 'ask')
        bm_bid, bm_amt, bm_val = topo(bm_order, 'bid')

        if mx_ask is None or bm_bid is None:
            print(f"🔴 Livro vazio ou dados inválidos em {par}")
            time.sleep(0.2)
            continue

        if mx_val < 10 or bm_val < 10:
            print(f"🔴 Liquidez insuficiente em {par}")
            time.sleep(0.2)
            continue

        spread = spread_duas_casas(mx_ask, bm_bid)
        if spread is None:
            print(f"🔴 Dados inválidos ao calcular spread em {par}")
            time.sleep(0.2)
            continue

        if spread >= SPREAD_MIN:
            saldo_usdt = saldo_cache
            lucro = round((saldo_usdt * spread / 100.0), 2) if saldo_usdt > 0 else 0.0
            msg = (
                f"🟢 COMPRAR na MEXC\n"
                f"Moeda pagadora: {base}\n"
                f"💰 Preço: {mx_ask:.6f}\n\n"
                f"➡️ PAGAR na BITMART para moeda receptora: {base}\n"
                f"💰 Preço destino: {bm_bid:.6f}\n\n"
                f"📊 SPREAD ESPERADO: +{spread:.2f}%\n"
                f"💵 SALDO DISPONÍVEL: {saldo_usdt:.2f} USDT\n"
                f"💰 LUCRO ESTIMADO: +{lucro:.2f} USDT"
            )
            enviar_mensagem(msg)
            print(f"🟢 {par} → Spread: +{spread:.2f}% | Saldo: {saldo_usdt:.2f} USDT | Lucro: {lucro:.2f} USDT")
        else:
            print(f"⚪ {par} analisado → Spread atual: +{spread:.2f}%")

        time.sleep(2)

    except Exception as loop_err:
        print(f"🔴 Erro no loop: {loop_err}")
        time.sleep(2)
