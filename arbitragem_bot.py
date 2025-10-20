BITMART_API_KEY = "6130d4bc0778badd1b009cc7884b0c8e6ed6ca1b"
BITMART_SECRET_KEY = "be764e831caea80e4e0e2f259429af37938893e1efebc7e1c04bc668fdd0cd30"
MEXC_API_KEY = "mx0vgldPupiJEgujR5"
MEXC_SECRET_KEY = "e610a1a511014832a3ff152efdd04257"
TELEGRAM_TOKEN = "8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10"
CHAT_ID = "1809414360"

VOLUME_MIN_USDT = 300000.0
SPREAD_MIN_PERCENT = 3.0
TICKER_TIMESTAMP_MAX_AGE_MS = 60 * 1000
RECEIVER_CHECK_LIMIT = 200
LOOP_SLEEP_SECONDS = 2

bitmart = ccxt.bitmart({
    'apiKey': BITMART_API_KEY,
    'secret': BITMART_SECRET_KEY,
    'enableRateLimit': True,
    'timeout': 20000,
})
mexc = ccxt.mexc({
    'apiKey': MEXC_API_KEY,
    'secret': MEXC_SECRET_KEY,
    'enableRateLimit': True,
    'timeout': 20000,
})

def enviar_mensagem(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Erro enviar_mensagem: {e}")

def carregar_pares():
    bitmart.load_markets()
    mexc.load_markets()
    bit_pairs = [s for s in bitmart.symbols if s.endswith("/USDT")]
    mexc_pairs = [s for s in mexc.symbols if s.endswith("/USDT")]
    payer_candidates = [s for s in mexc_pairs if s in bitmart.symbols]
    return payer_candidates, bit_pairs

def pegar_saldo_usdt_mexc():
    try:
        bal = mexc.fetch_balance()
        usdt = 0.0
        if 'USDT' in bal.get('free', {}):
            usdt = float(bal['free']['USDT'] or 0.0)
        elif 'USDT' in bal.get('total', {}):
            usdt = float(bal['total']['USDT'] or 0.0)
        return usdt
    except Exception as e:
        print(f"Erro ao obter saldo MEXC: {e}")
        return 0.0

def ticker_recente_valido(ticker):
    if not ticker:
        return False
    last = ticker.get('last')
    ts = ticker.get('timestamp')
    if last is None or ts is None:
        return False
    age = abs(int(time.time() * 1000) - int(ts))
    return age <= TICKER_TIMESTAMP_MAX_AGE_MS

def obter_volume_24h_usdt(ticker):
    qv = ticker.get('quoteVolume')
    if qv is None:
        bv = ticker.get('baseVolume')
        last = ticker.get('last') or 0.0
        try:
            return float(bv or 0.0) * float(last or 0.0)
        except:
            return 0.0
    try:
        return float(qv or 0.0)
    except:
        return 0.0

def format_num(n, ndigits=6):
    try:
        return f"{float(n):.{ndigits}f}"
    except:
        return str(n)

def analisar_e_enviar():
    payer_candidates, bit_pairs = carregar_pares()
    print(f"🎯 Payers comuns (MEXC+BitMart): {len(payer_candidates)}")
    print(f"📌 BitMart USDT pares disponíveis: {len(bit_pairs)}")
    bit_ticks = {}
    try:
        bit_ticks = bitmart.fetch_tickers([p for p in bit_pairs[:RECEIVER_CHECK_LIMIT]])
    except Exception:
        for s in bit_pairs[:RECEIVER_CHECK_LIMIT]:
            try:
                bit_ticks[s] = bitmart.fetch_ticker(s)
            except Exception:
                bit_ticks[s] = None

    while True:
        try:
            mexc_balance_usdt = pegar_saldo_usdt_mexc()
            for payer in payer_candidates:
                try:
                    ticker_payer_mexc = mexc.fetch_ticker(payer)
                except Exception as e:
                    print(f"Erro ao buscar ticker MEXC {payer}: {e}")
                    continue

                if not ticker_recente_valido(ticker_payer_mexc):
                    print(f"⚪ {payer} ignorado → preço MEXC não atualizado")
                    continue

                volume_payer = obter_volume_24h_usdt(ticker_payer_mexc)
                if volume_payer < VOLUME_MIN_USDT:
                    print(f"⚪ {payer} ignorado → volume 24h {volume_payer:.2f} < {VOLUME_MIN_USDT:.2f}")
                    continue

                price_payer = float(ticker_payer_mexc.get('last') or 0.0)
                if price_payer == 0:
                    print(f"⚪ {payer} ignorado → preço payer 0")
                    continue

                checked_receivers = 0
                for receiver in bit_pairs:
                    if checked_receivers >= RECEIVER_CHECK_LIMIT:
                        break
                    checked_receivers += 1

                    ticker_receiver = bit_ticks.get(receiver)
                    if ticker_receiver is None:
                        try:
                            ticker_receiver = bitmart.fetch_ticker(receiver)
                            bit_ticks[receiver] = ticker_receiver
                        except Exception as e:
                            print(f"Erro ao buscar ticker BitMart {receiver}: {e}")
                            continue

                    if not ticker_recente_valido(ticker_receiver):
                        continue

                    price_receiver = float(ticker_receiver.get('last') or 0.0)
                    if price_receiver == 0:
                        continue

                    spread = ((price_receiver - price_payer) / price_payer) * 100.0
                    spread_rounded = round(spread, 2)

                    if spread >= SPREAD_MIN_PERCENT:
                        estimated_profit = mexc_balance_usdt * (spread / 100.0)
                        msg = (
                            f"🟢 COMPRAR na MEXC\n"
                            f"Moeda pagadora: {payer}\n"
                            f"💰 Preço: {format_num(price_payer, 6)}\n\n"
                            f"➡️ PAGAR na BITMART para moeda receptora: {receiver}\n"
                            f"💰 Preço destino: {format_num(price_receiver, 6)}\n\n"
                            f"📊 SPREAD ESPERADO: +{spread_rounded:.2f}%\n"
                            f"💵 SALDO DISPONÍVEL: {format_num(mexc_balance_usdt,2)} USDT\n"
                            f"💰 LUCRO ESTIMADO: +{format_num(estimated_profit,2)} USDT"
                        )
                        enviar_mensagem(msg)
                        print(f"🟢 Sinal enviado → {payer} -> {receiver} | Spread {spread_rounded:.2f}%")
                    else:
                        print(f"⚪ {payer} -> {receiver} analisado → Spread atual: {spread_rounded:.2f}%")

                    time.sleep(0.05)

        except Exception as e:
            print(f"Erro principal loop: {e}")

        time.sleep(LOOP_SLEEP_SECONDS)

if __name__ == "__main__":
    print("🟢 Bot de Arbitragem iniciado com sucesso!")
    try:
        analisar_e_enviar()
    except Exception as e:
        print(f"Erro fatal: {e}")
```0
