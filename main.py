import time
import requests
import arbitragem_bot

print("🟢 Bot de Arbitragem iniciado com sucesso!")

while True:
    try:
        arbitragem_bot.enviar_mensagem("✅ Bot ativo e monitorando oportunidades...")
        time.sleep(60)
    except Exception as e:
        url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
        data = {"chat_id": "1809414360", "text": f"Erro no bot: {e}"}
        requests.post(url, data=data)
        time.sleep(60)
