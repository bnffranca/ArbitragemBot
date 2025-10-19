import time
import requests
import arbitragem_bot

print("🟢 Bot de Arbitragem iniciado com sucesso!")

while True:
    try:
        arbitragem_bot.enviar_mensagem("✅ Bot ativo e monitorando oportunidades...")
        time.sleep(60)
    except Exception as e:
        url = f"https://api.telegram.org/bot{arbitragem_bot.TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": arbitragem_bot.CHAT_ID, "text": f"Erro no bot: {e}"}
        requests.post(url, data=data)
        time.sleep(60)
