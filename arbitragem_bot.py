import ccxt
import time
import requests

SPREAD_MIN = 3.0
LIQ_MIN_USDT = 10.0
RATE_LIMIT_SECONDS = 1.0
MAGNITUDE_FACTOR_MAX = 100.0
MAGNITUDE_FACTOR_MIN = 0.01

mexc_public = ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'spot', 'fetchCurrencies': False}})
mexc_auth = ccxt.mexc({'apiKey': "mx0vgldPupiJEgujR5", 'secret': "e610a1a511014832a3ff152efdd04257", 'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
bitmart = ccxt.bitmart({'apiKey': "6130d4bc0778badd1b009cc7884b0c8e6ed6ca1b", 'secret': "be764e831caea80e4e0e2f259429af37938893e1efebc7e1c04bc668fdd0cd30", 'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

def enviar_mensagem(msg):
    url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
    data = {"chat_id": "1809414360", "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
        time.sleep(RATE_LIMIT_SECONDS)
    except Exception:
        pass

def ler_saldo_mexc_usdt():
    try:
        bal = mexc_auth.fetch_balance({'recvWindow': 5000})
        return float(bal['total'].get('USDT', 0) or 0)
    except Exception:
        return 0.0

def topo(orderbook, side):
    ob = orderbook.get('asks') if side == 'ask' else orderbook.get('bids')
    if not ob:
        return None, None, None
    try:
        price = float(ob[0][0])
        amount = float(ob[0][1])
    except Exception:
        return None, None, None
    return price, amount, price * amount

def calc_spread_percent(orig, dest):
    if orig is None or dest is None or orig <= 0:
        return None
    return round(((dest - orig) / orig) * 100.0, 2)

def mesma_ordem_mag(preco_origem, preco_destino):
    if preco_origem is None or preco_destino is None or preco_origem <= 0 or preco_destino <= 0:
        return False
    factor = preco_destino / preco_origem
    return MAGNITUDE_FACTOR_MIN <= factor <= MAGNITUDE_FACTOR_MAX

def carregar_listas():
    try:
        mexc_public.load_markets()
    except Exception:
        pass
    try:
        bitmart.load_markets()
    except Exception:
        pass
    mexc_usdt = {s for s in getattr(mexc_public, 'symbols', []) if s.endswith("/USDT")}
    bitmart_usdt = {s for s in getattr(bitmart, 'symbols', []) if s.endswith("/USDT")}
    mexc_bases = {s.split('/')[0] for s in mexc_usdt}
    bitmart_bases = {s.split('/')[0] for s in bitmart_usdt}
    payer_bases = sorted(list(mexc_bases & bitmart_bases))
    bitmart_recipients = sorted(list(bitmart_bases))
    common_pairs = sorted(list(mexc_usdt & bitmart_usdt))
    return payer_bases, bitmart_recipients, common_pairs

payer_bases, bitmart_recipients, common_pairs = carregar_listas()
print("🟢 Bot iniciado.")
print(f"📊 Spread mínimo: {SPREAD_MIN:.2f}% | Liquidez mínima: {LIQ_MIN_USDT:.2f} USDT")

indice_payer = 0
saldo_cache = ler_saldo_mexc_usdt()
last_balance_refresh = time.time()

while True:
    try:
        if time.time() - last_balance_refresh > 30:
            saldo_cache = ler_saldo_mexc_usdt()
            last_balance_refresh = time.time()

        if not payer_bases and not common_pairs:
            payer_bases, bitmart_recipients, common_pairs = carregar_listas()
            time.sleep(2)
            continue

        if payer_bases:
            payer = payer_bases[indice_payer % len(payer_bases)]
            indice_payer += 1
            par_payer = f"{payer}/USDT"
            try:
                book_mx = mexc_public.fetch_order_book(par_payer)
            except Exception:
                time.sleep(0.2)
                continue
            mx_ask, mx_amt, mx_val = topo(book_mx, 'ask')
            if mx_ask is None:
                time.sleep(0.2)
            else:
                for recipient in bitmart_recipients:
                    if recipient == payer:
                        continue
                    par_rec = f"{recipient}/USDT"
                    try:
                        book_bm_rec = bitmart.fetch_order_book(par_rec)
                    except Exception:
                        continue
                    bm_bid_rec, bm_amt_rec, bm_val_rec = topo(book_bm_rec, 'bid')
                    if bm_bid_rec is None:
                        continue
                    if mx_val < LIQ_MIN_USDT or bm_val_rec < LIQ_MIN_USDT:
                        continue
                    if not mesma_ordem_mag(mx_ask, bm_bid_rec):
                        continue
                    spread = calc_spread_percent(mx_ask, bm_bid_rec)
                    if spread is None:
                        continue
                    if spread >= SPREAD_MIN:
                        saldo_usdt = saldo_cache
                        lucro = round((saldo_usdt * spread / 100.0), 2) if saldo_usdt > 0 else 0.0
                        msg = (
                            "🟢 COMPRAR na MEXC\n"
                            f"Moeda pagadora: {par_payer}\n"
                            f"💰 Preço: {mx_ask:.6f}\n\n"
                            f"➡️ PAGAR na BITMART para moeda receptora: {par_rec}\n"
                            f"💰 Preço destino: {bm_bid_rec:.6f}\n\n"
                            f"📊 SPREAD ESPERADO: +{spread:.2f}%\n\n"
                            f"💵 SALDO DISPONÍVEL: {saldo_usdt:.2f} USDT\n"
                            f"💰 LUCRO ESTIMADO: +{lucro:.2f} USDT"
                        )
                        enviar_mensagem(msg)
                        print(f"🟢 CRUZADA {par_payer} -> {par_rec} | Spread: +{spread:.2f}% | Lucro: {lucro:.2f} USDT")
                        break
                time.sleep(0.5)

        for par in common_pairs:
            try:
                book_mx_s = mexc_public.fetch_order_book(par)
            except Exception:
                continue
            try:
                book_bm_s = bitmart.fetch_order_book(par)
            except Exception:
                continue
            mx_ask_s, mx_amt_s, mx_val_s = topo(book_mx_s, 'ask')
            bm_bid_s, bm_amt_s, bm_val_s = topo(book_bm_s, 'bid')
            if mx_ask_s is None or bm_bid_s is None:
                continue
            if mx_val_s < LIQ_MIN_USDT or bm_val_s < LIQ_MIN_USDT:
                continue
            if not mesma_ordem_mag(mx_ask_s, bm_bid_s):
                continue
            spread_s = calc_spread_percent(mx_ask_s, bm_bid_s)
            if spread_s is None:
                continue
            if spread_s >= SPREAD_MIN:
                saldo_usdt = saldo_cache
                lucro = round((saldo_usdt * spread_s / 100.0), 2) if saldo_usdt > 0 else 0.0
                msg = (
                    "🟢 COMPRAR na MEXC\n"
                    f"Moeda: {par}\n"
                    f"💰 Preço: {mx_ask_s:.6f}\n\n"
                    "➡️ VENDER na BITMART\n"
                    f"💰 Preço destino: {bm_bid_s:.6f}\n\n"
                    f"📊 SPREAD ESPERADO: +{spread_s:.2f}%\n\n"
                    f"💵 SALDO DISPONÍVEL: {saldo_usdt:.2f} USDT\n"
                    f"💰 LUCRO ESTIMADO: +{lucro:.2f} USDT"
                )
                enviar_mensagem(msg)
                print(f"🟢 SIMPLES {par} | Spread: +{spread_s:.2f}% | Lucro: {lucro:.2f} USDT")
            else:
                print(f"⚪ {par} analisado → Spread atual: +{spread_s:.2f}%")
            time.sleep(0.2)

        time.sleep(1)

    except Exception as e:
        print(f"Erro geral no loop: {e}")
        time.sleep(2)
