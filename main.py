import arbitragem_bot
import time
import requests

print("🟢 Bot de Arbitragem iniciado com sucesso!")

while True:
    try:
        arbitragem_bot.analisar_arbitragem()
    except Exception as e:
        url = f"https://api.telegram.org/bot{arbitragem_bot.TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": arbitragem_bot.CHAT_ID, "text": f"Erro no bot: {e}"})
    time.sleep(60)
