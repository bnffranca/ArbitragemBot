import ccxt
import time
import requests
import math

BITMART_API_KEY = "6130d4bc0778badd1b009cc7884b0c8e6ed6ca1b"
BITMART_SECRET_KEY = "be764e831caea80e4e0e2f259429af37938893e1efebc7e1c04bc668fdd0cd30"
MEXC_API_KEY = "mx0vgldPupiJEgujR5"
MEXC_SECRET_KEY = "e610a1a511014832a3ff152efdd04257"

SPREAD_MIN = 3.0
MIN_24H_VOLUME_USD = 50000.0
SLEEP_SECONDS = 8

bitmart = ccxt.bitmart({
    "apiKey": "6130d4bc0778badd1b009cc7884b0c8e6ed6ca1b",
    "secret": "be764e831caea80e4e0e2f259429af37938893e1efebc7e1c04bc668fdd0cd30",
    "enableRateLimit": True,
    "options": {"defaultType": "spot"},
})

mexc = ccxt.mexc({
    "apiKey": "mx0vgldPupiJEgujR5",
    "secret": "e610a1a511014832a3ff152efdd04257",
    "enableRateLimit": True,
    "options": {"defaultType": "spot"},
})

def enviar_mensagem(msg):
    url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
    data = {"chat_id": "1809414360", "text": msg}
    try:
        requests.post(url, data=data, timeout=15)
    except Exception:
        pass

def safe_ticker(exchange, symbol):
    try:
        return exchange.fetch_ticker(symbol)
    except Exception:
        return None

def has_market(exchange, symbol):
    try:
        return symbol in exchange.symbols
    except Exception:
        return False

def get_24h_quote_volume_usd(ticker):
    if not ticker:
        return 0.0
    qv = ticker.get("quoteVolume")
    if qv:
        try:
            return float(qv)
        except Exception:
            pass
    base_vol = ticker.get("baseVolume") or 0.0
    last = ticker.get("last") or 0.0
    try:
        return float(base_vol) * float(last)
    except Exception:
        return 0.0

def format_pct(x):
    return f"{x:+.2f}%"

def load_markets_safe():
    try:
        bitmart.load_markets()
    except Exception:
        pass
    try:
        mexc.load_markets()
    except Exception:
        pass

def find_common_pay_tokens():
    try:
        bit_symbols = set(bitmart.symbols)
        mex_symbols = set(mexc.symbols)
    except Exception:
        return []
    pay_tokens = set()
    for sym in mex_symbols:
        if sym.endswith("/USDT"):
            token = sym.split("/")[0]
            if any(s.startswith(f"{token}/") for s in bit_symbols) or f"{token}/USDT" in bit_symbols:
                pay_tokens.add(token)
    return sorted(pay_tokens)

def estimate_opportunity(pay_token, candidate_dest, usdt_balance):
    buy_pair_mexc = f"{pay_token}/USDT"
    dest_pair_bitmart = f"{candidate_dest}/{pay_token}"
    dest_usdt_pair_bitmart = f"{candidate_dest}/USDT"

    if not (has_market(mexc, buy_pair_mexc) and has_market(bitmart, dest_pair_bitmart) and has_market(bitmart, dest_usdt_pair_bitmart)):
        return None

    ticker_pay_mexc = safe_ticker(mexc, buy_pair_mexc)
    ticker_dest_pair = safe_ticker(bitmart, dest_pair_bitmart)
    ticker_dest_usdt = safe_ticker(bitmart, dest_usdt_pair_bitmart)

    if not (ticker_pay_mexc and ticker_dest_pair and ticker_dest_usdt):
        return None

    vol_pay_mexc = get_24h_quote_volume_usd(ticker_pay_mexc)
    vol_dest_bitmart = get_24h_quote_volume_usd(ticker_dest_usdt)

    if vol_pay_mexc < MIN_24H_VOLUME_USD or vol_dest_bitmart < MIN_24H_VOLUME_USD:
        return None

    price_pay_buy = ticker_pay_mexc.get("last")
    price_dest_in_pay = ticker_dest_pair.get("last")
    price_dest_usdt_bid = ticker_dest_usdt.get("last")

    if not price_pay_buy or not price_dest_in_pay or not price_dest_usdt_bid:
        return None

    try:
        price_pay_buy = float(price_pay_buy)
        price_dest_in_pay = float(price_dest_in_pay)
        price_dest_usdt_bid = float(price_dest_usdt_bid)
    except Exception:
        return None

    if price_pay_buy <= 0 or price_dest_in_pay <= 0:
        return None

    pay_amount = usdt_balance / price_pay_buy
    dest_amount = pay_amount / price_dest_in_pay
    final_usdt = dest_amount * price_dest_usdt_bid

    spread_pct = ((final_usdt - usdt_balance) / usdt_balance) * 100.0

    return {
        "pay_token": pay_token,
        "dest_token": candidate_dest,
        "price_pay_buy": price_pay_buy,
        "price_dest_in_pay": price_dest_in_pay,
        "price_dest_usdt_bid": price_dest_usdt_bid,
        "vol_pay_mexc": vol_pay_mexc,
        "vol_dest_bitmart": vol_dest_bitmart,
        "final_usdt": final_usdt,
        "spread_pct": spread_pct,
    }

def get_usdt_balance_on_mexc():
    try:
        bal = mexc.fetch_balance()
        free = bal.get("free", {}) or {}
        usdt = free.get("USDT") or free.get("usdt") or 0.0
        return float(usdt)
    except Exception:
        return 0.0

def main_loop():
    load_markets_safe()
    pay_tokens = find_common_pay_tokens()
    if not pay_tokens:
        print("⚠️ Nenhum token pagador comum encontrado.")
    while True:
        try:
            load_markets_safe()
            usdt_balance = get_usdt_balance_on_mexc()
            if usdt_balance <= 0:
                usdt_balance = 100.0

            opportunities_found = 0

            for pay in pay_tokens:
                dest_candidates = [s.split("/")[0] for s in bitmart.symbols if s.endswith(f"/{pay}")]
                for dest in dest_candidates:
                    result = estimate_opportunity(pay, dest, usdt_balance)
                    if not result:
                        continue
                    spread = result["spread_pct"]

                    # Mostrar todas as oportunidades no console
                    print(f"⚪ {result['pay_token']}/{result['dest_token']} → Spread atual: {format_pct(spread)}")

                    if spread >= SPREAD_MIN: # agora é >= e não >
                        opportunities_found += 1
                        est_profit = result["final_usdt"] - usdt_balance
                        msg = (
                            f"🟢 COMPRAR na MEXC\n"
                            f"Moeda pagadora: {result['pay_token']}/USDT\n"
                            f"💰 Preço: {result['price_pay_buy']:.8f}\n\n"
                            f"➡️ PAGAR na BITMART para moeda receptora: {result['dest_token']}/{result['pay_token']}\n"
                            f"💰 Preço destino: {result['price_dest_in_pay']:.8f}\n\n"
                            f"📊 SPREAD ESPERADO: +{spread:.2f}%\n"
                            f"💵 SALDO DISPONÍVEL: {usdt_balance:.2f} USDT\n"
                            f"💰 LUCRO ESTIMADO: +{est_profit:.2f} USDT\n"
                        )
                        enviar_mensagem(msg)

            if opportunities_found == 0:
                print(f"Nenhuma oportunidade ≥ {SPREAD_MIN:.2f}% nesta varredura.")

            time.sleep(SLEEP_SECONDS)

        except Exception as e:
            print(f"Erro no loop principal: {e}")
            time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    print("Iniciando varredura de arbitragem cruzada (MEXC → BitMart)...")
    main_loop()
