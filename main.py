import ccxt
import requests
import time
from datetime import datetime, timedelta

TELEGRAM_TOKEN = "8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10"
CHAT_ID = "1809414360"
MEXC_API_KEY = "mx0vgldd1b0f5b30b8cd99a3b5a2c69b8"
MEXC_SECRET_KEY = "b7dd86e6f9c741f1b4e5d3bb5aa604af"

SPREAD_MIN = 0.5
VOLUME_MIN = 800
DELAY = 0.3
USE_BALANCE_PCT = 1.0
TOTAL_FEE = 0.003

mexc = ccxt.mexc({
    "apiKey": "mx0vgldd1b0f5b30b8cd99a3b5a2c69b8",
    "secret": "b7dd86e6f9c741f1b4e5d3bb5aa604af",
    "enableRateLimit": True,
    "options": {"defaultType": "spot"}
})
mexc.load_markets()

start_ts = time.time()
cycles = 0
total_profit_usdt = 0.0
base_balance_start = None
running_cycle = False

def send_telegram(msg):
    try:
        url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
        data = {"chat_id": "1809414360", "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except:
        pass

def usdt_balance(ex):
    try:
        b = ex.fetch_balance()
        return float(b["free"].get("USDT", 0))
    except:
        return 0.0

def limits(ex, symbol):
    m = ex.markets.get(symbol, {})
    lim = m.get("limits", {})
    amt = lim.get("amount", {})
    cost = lim.get("cost", {})
    min_amt = float(amt.get("min") or 0)
    min_cost = float(cost.get("min") or 0)
    return min_amt, min_cost

def quantize(ex, symbol, amount):
    try:
        return float(ex.amount_to_precision(symbol, amount))
    except:
        return amount

def cls():
    print("\033[2J\033[H", end="")

def fmt_time(sec):
    return str(timedelta(seconds=int(sec)))

def header(current_balance):
    dur = fmt_time(time.time() - start_ts)
    total_pct = 0.0
    if base_balance_start and base_balance_start > 0:
        total_pct = (current_balance / base_balance_start - 1.0) * 100.0
    print("========================================")
    print("📊 STATUS GERAL — MEXC Arbitragem (Spot)")
    print("----------------------------------------")
    print(f"🕒 Tempo ativo: {dur}")
    print(f"🔁 Ciclos concluídos: {cycles}")
    print(f"💰 Lucro acumulado: {total_profit_usdt:.4f} USDT ({total_pct:.2f}%)")
    print(f"🏦 Saldo USDT: {current_balance:.4f} USDT")
    print("========================================")

def plan_from_cache(prices, ex, usdt_avail, base, quote2):
    s1 = f"{base}/USDT"
    s2 = f"{base}/{quote2}"
    s3 = f"{quote2}/USDT"
    t1 = prices.get(s1)
    t2 = prices.get(s2)
    t3 = prices.get(s3)
    if not t1 or not t2 or not t3:
        return None
    if not (t1.get("ask") and t2.get("bid") and t3.get("bid")):
        return None
    a1 = float(t1["ask"])
    b2 = float(t2["bid"])
    b3 = float(t3["bid"])
    if a1 <= 0 or b2 <= 0 or b3 <= 0:
        return None
    usdt_use = usdt_avail * USE_BALANCE_PCT
    if usdt_use <= 0:
        return None
    qty_base = usdt_use / a1
    min_amt1, min_cost1 = limits(ex, s1)
    min_amt2, min_cost2 = limits(ex, s2)
    min_amt3, min_cost3 = limits(ex, s3)
    if min_amt1 and qty_base < min_amt1:
        return None
    if min_cost1 and usdt_use < min_cost1:
        return None
    qty_quote2 = qty_base * b2
    if min_amt2 and qty_base < min_amt2:
        return None
    if min_cost2 and qty_quote2 < min_cost2:
        return None
    usdt_final_gross = qty_quote2 * b3
    if min_amt3 and qty_quote2 < min_amt3:
        return None
    if min_cost3 and usdt_final_gross < min_cost3:
        return None
    gross_factor = (b2 * b3) / a1
    net_spread_pct = (gross_factor - 1 - TOTAL_FEE) * 100
    qb = quantize(ex, s1, qty_base)
    qq2 = quantize(ex, s3, qty_quote2)
    return {"spread_net": net_spread_pct, "s1": s1, "s2": s2, "s3": s3, "a1": a1, "b2": b2, "b3": b3, "usdt_use": usdt_use, "qty_base": qb, "qty_quote2": qq2, "base": base, "quote2": quote2}

def best_opportunity(ex):
    global running_cycle
    if running_cycle:
        return None
    try:
        ticks = ex.fetch_tickers()
    except:
        return None
    prices = {s: d for s, d in ticks.items() if d.get("bid") and d.get("ask") and d.get("quoteVolume")}
    usdt_pairs = [s for s in prices if s.endswith("/USDT") and prices[s]["quoteVolume"] >= VOLUME_MIN]
    coins = [s.split("/")[0] for s in usdt_pairs]
    existing = set(prices.keys())
    s = usdt_balance(ex)
    if s <= 0:
        return None
    best = None
    shown = 0
    for a in coins:
        s1a = f"{a}/USDT"
        if s1a not in prices:
            continue
        for b in coins:
            if b == a:
                continue
            s3b = f"{b}/USDT"
            if s3b not in prices:
                continue
            s2_dir = f"{a}/{b}"
            s2_inv = f"{b}/{a}"
            plan = None
            if s2_dir in existing:
                pd = plan_from_cache(prices, ex, s, a, b)
                if pd:
                    plan = pd
            if s2_inv in existing:
                pi = plan_from_cache(prices, ex, s, b, a)
                if pi and (plan is None or pi["spread_net"] > plan["spread_net"]):
                    plan = pi
            if not plan:
                continue
            if plan["spread_net"] < SPREAD_MIN:
                if shown < 80:
                    print(f"🔴 USDT → {plan['base']} → {plan['quote2']} → USDT | Spread líquido: {plan['spread_net']:.2f}%")
                    shown += 1
                continue
            if best is None or plan["spread_net"] > best["spread_net"]:
                best = plan
    return best

def market_order(ex, symbol, side, amount):
    return ex.create_order(symbol, "market", side, amount)

def unwind_to_usdt(ex, base, quote2):
    for m in [base, quote2]:
        try:
            s = f"{m}/USDT"
            a = float(ex.fetch_balance()["free"].get(m, 0))
            a = quantize(ex, s, a)
            if a > 0:
                market_order(ex, s, "sell", a)
        except:
            pass

def execute_cycle(ex, plan):
    global cycles, total_profit_usdt, running_cycle
    running_cycle = True
    base = plan["base"]
    quote2 = plan["quote2"]
    print(f"🟢 EXECUTANDO: USDT → {base} → {quote2} → USDT | Spread: {plan['spread_net']:.2f}%")
    usdt_before = usdt_balance(ex)
    try:
        market_order(ex, plan["s1"], "buy", plan["qty_base"])
        market_order(ex, plan["s2"], "sell", plan["qty_base"])
        q2_free = float(ex.fetch_balance()["free"].get(quote2, 0))
        q2_free = min(q2_free, plan["qty_quote2"])
        q2_free = quantize(ex, plan["s3"], q2_free)
        if q2_free > 0:
            market_order(ex, plan["s3"], "sell", q2_free)
        usdt_after = usdt_balance(ex)
        gain = usdt_after - usdt_before
        cycles += 1
        total_profit_usdt += max(0.0, gain)
        msg = (
            f"📢 *ARBITRAGEM EXECUTADA (MEXC)*\n"
            f"💱 Ciclo: USDT → {base} → {quote2} → USDT\n"
            f"📊 Spread líquido: {plan['spread_net']:.2f}%\n"
            f"💰 USDT usado: {plan['usdt_use']:.4f}\n"
            f"💵 Lucro no ciclo: {gain:.4f} USDT\n"
            f"🏦 Saldo atual: {usdt_after:.4f}\n"
            f"🕒 Horário: {datetime.now().strftime('%H:%M:%S')}"
        )
        print(msg)
        send_telegram(msg)
    except:
        unwind_to_usdt(ex, base, quote2)
    time.sleep(1.0)
    running_cycle = False

def iniciar_arbitragem():
    global base_balance_start
    if base_balance_start is None:
        base_balance_start = usdt_balance(mexc)
    cls()
    bal = usdt_balance(mexc)
    header(bal)
    print("Procurando oportunidades...")
    plan = best_opportunity(mexc)
    if plan:
        print("🟢 Oportunidade válida encontrada. Executando ciclo...")
        execute_cycle(mexc, plan)
    else:
        time.sleep(DELAY)
