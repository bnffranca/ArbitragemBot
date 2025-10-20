import ccxt
import requests
import time
from datetime import datetime, timedelta

TELEGRAM_TOKEN = "8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10"
CHAT_ID = "1809414360"

SPREAD_MIN = 0.35
VOLUME_MIN = 800
DELAY = 5
COOLDOWN = 5
USAR_PCT_SALDO = 1.0
TAXA_TOTAL = 0.003

MEXC_API_KEY = "mx0vgldd1b0f5b30b8cd99a3b5a2c69b8"
MEXC_SECRET_KEY = "b7dd86e6f9c741f1b4e5d3bb5aa604af"

mexc = ccxt.mexc({
    'apiKey': "mx0vgldd1b0f5b30b8cd99a3b5a2c69b8",
    'secret': "b7dd86e6f9c741f1b4e5d3bb5aa604af",
    'options': {'defaultType': 'spot'}
})
mexc.load_markets()

start_ts = time.time()
ciclos = 0
lucro_total_usdt = 0.0
saldo_base_inicial = None

def enviar_telegram(msg):
    try:
        url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
        data = {"chat_id": "1809414360", "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except:
        pass

def saldo_usdt(ex):
    try:
        b = ex.fetch_balance()
        return float(b["free"].get("USDT", 0))
    except:
        return 0.0

def precos(ex, s1, s2, s3):
    t1 = ex.fetch_ticker(s1)
    t2 = ex.fetch_ticker(s2)
    t3 = ex.fetch_ticker(s3)
    return float(t1["ask"]), float(t2["bid"]), float(t3["bid"])

def limites(ex, symbol):
    m = ex.markets.get(symbol, {})
    lim = m.get("limits", {})
    amt = lim.get("amount", {})
    cost = lim.get("cost", {})
    min_amt = float(amt.get("min") or 0)
    min_cost = float(cost.get("min") or 0)
    return min_amt, min_cost

def arredonda(ex, symbol, amount):
    p = ex.markets.get(symbol, {}).get("precision", {}).get("amount")
    if p is None:
        return amount
    return float(ex.amount_to_precision(symbol, amount))

def cls():
    print("\033[2J\033[H", end="")

def fmt_tempo(seg):
    return str(timedelta(seconds=int(seg)))

def render_topo(saldo_atual):
    dur = fmt_tempo(time.time() - start_ts)
    total_pct = 0.0
    if saldo_base_inicial and saldo_base_inicial > 0:
        total_pct = (saldo_atual / saldo_base_inicial - 1.0) * 100.0
    print("========================================")
    print("📊 STATUS GERAL — MEXC Arbitragem")
    print("----------------------------------------")
    print(f"🕒 Tempo ativo: {dur}")
    print(f"🔁 Ciclos concluídos: {ciclos}")
    print(f"💰 Lucro acumulado: {lucro_total_usdt:.4f} USDT ({total_pct:.2f}%)")
    print(f"🏦 Saldo atual estimado: {saldo_atual:.4f} USDT")
    print("========================================")

def avaliar_pernas_liquidas(ex, usdt_disp, base, quote2):
    s1 = f"{base}/USDT"
    s2 = f"{base}/{quote2}"
    s3 = f"{quote2}/USDT"
    try:
        a1, b2, b3 = precos(ex, s1, s2, s3)
    except:
        return None
    usdt_uso = usdt_disp * USAR_PCT_SALDO
    qtd_base = usdt_uso / a1
    min_amt1, min_cost1 = limites(ex, s1)
    min_amt2, min_cost2 = limites(ex, s2)
    min_amt3, min_cost3 = limites(ex, s3)
    if min_amt1 and qtd_base < min_amt1: return None
    if min_cost1 and usdt_uso < min_cost1: return None
    qtd_quote2 = qtd_base * b2
    if min_amt2 and qtd_base < min_amt2: return None
    if min_cost2 and qtd_quote2 < min_cost2: return None
    usdt_final_bruto = qtd_quote2 * b3
    if min_amt3 and qtd_quote2 < min_amt3: return None
    if min_cost3 and usdt_final_bruto < min_cost3: return None
    fator_bruto = (b2 * b3) / a1
    spread_liquido_pct = (fator_bruto - 1 - TAXA_TOTAL) * 100
    qb = arredonda(ex, s1, qtd_base)
    q2 = arredonda(ex, s2, qtd_base)
    q3 = arredonda(ex, s3, qtd_quote2)
    return {
        "spread_liq": spread_liquido_pct,
        "s1": s1, "s2": s2, "s3": s3,
        "a1": a1, "b2": b2, "b3": b3,
        "usdt_uso": usdt_uso,
        "qtd_base": qb,
        "qtd_quote2": q3,
        "base": base, "quote2": quote2
    }

def melhor_oportunidade(ex):
    try:
        ticks = ex.fetch_tickers()
    except:
        return None
    prec = {s: d for s, d in ticks.items() if d.get("bid") and d.get("ask") and d.get("quoteVolume")}
    usdt_pairs = [s for s in prec if s.endswith("/USDT") and prec[s]["quoteVolume"] >= VOLUME_MIN]
    bases = [s.split("/")[0] for s in usdt_pairs]
    s = saldo_usdt(ex)
    if s <= 0:
        return None
    best = None
    printed = 0
    for base in bases:
        for p2 in [x for x in prec if x.startswith(base + "/") and not x.endswith("/USDT")]:
            q2 = p2.split("/")[1]
            p3 = f"{q2}/USDT"
            if p3 not in prec:
                continue
            plano = avaliar_pernas_liquidas(ex, s, base, q2)
            if not plano:
                continue
            if plano["spread_liq"] < SPREAD_MIN:
                if printed < 25:
                    print(f"🔴 USDT → {base} → {q2} → USDT | Spread líquido: {plano['spread_liq']:.2f}%")
                    printed += 1
                continue
            if (best is None) or (plano["spread_liq"] > best["spread_liq"]):
                best = plano
    return best

def order_market(ex, symbol, side, amount):
    return ex.create_order(symbol, "market", side, amount)

def unwind_usdt(ex, base, quote2):
    try:
        s = f"{base}/USDT"
        a = float(ex.fetch_balance()["free"].get(base, 0))
        a = arredonda(ex, s, a)
        if a > 0: order_market(ex, s, "sell", a)
    except:
        pass
    try:
        s = f"{quote2}/USDT"
        a = float(ex.fetch_balance()["free"].get(quote2, 0))
        a = arredonda(ex, s, a)
        if a > 0: order_market(ex, s, "sell", a)
    except:
        pass

def executar_ciclo(ex, plano):
    global ciclos, lucro_total_usdt
    base = plano["base"]
    quote2 = plano["quote2"]
    print(f"🟢 Executando: USDT → {base} → {quote2} → USDT | Spread líquido: {plano['spread_liq']:.2f}%")
    usdt_antes = saldo_usdt(ex)
    try:
        order_market(ex, plano["s1"], "buy", plano["qtd_base"])
        order_market(ex, plano["s2"], "sell", plano["qtd_base"])
        a_q2 = float(ex.fetch_balance()["free"].get(quote2, 0))
        a_q2 = min(a_q2, plano["qtd_quote2"])
        a_q2 = arredonda(ex, plano["s3"], a_q2)
        if a_q2 > 0:
            order_market(ex, plano["s3"], "sell", a_q2)
        usdt_depois = saldo_usdt(ex)
        ganho = usdt_depois - usdt_antes
        ciclos += 1
        lucro_total_usdt += max(0.0, ganho)
        msg = (
            f"📢 *ARBITRAGEM EXECUTADA (MEXC)*\n"
            f"💱 Ciclo: USDT → {base} → {quote2} → USDT\n"
            f"📊 Spread líquido: {plano['spread_liq']:.2f}%\n"
            f"💰 USDT usado: {plano['usdt_uso']:.4f}\n"
            f"💵 Lucro no ciclo: {ganho:.4f} USDT\n"
            f"🏦 USDT atual: {usdt_depois:.4f}\n"
            f"🕒 Horário: {datetime.now().strftime('%H:%M:%S')}"
        )
        print(msg)
        enviar_telegram(msg)
    except:
        unwind_usdt(ex, base, quote2)

def iniciar_arbitragem():
    global saldo_base_inicial
    print("🟢 Bot de Arbitragem Interna (MEXC) Iniciado\n")
    if saldo_base_inicial is None:
        saldo_base_inicial = saldo_usdt(mexc)
    while True:
        cls()
        saldo_atual = saldo_usdt(mexc)
        render_topo(saldo_atual)
        print("Procurando oportunidades...")
        plano = melhor_oportunidade(mexc)
        if plano:
            executar_ciclo(mexc, plano)
            time.sleep(COOLDOWN)
        else:
            time.sleep(DELAY)

iniciar_arbitragem()
