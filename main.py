import time
import requests
import arbitragem_bot

print("🟢 Bot de Arbitragem Interna (MEXC) iniciado com sucesso!")

while True:
    try:
        arbitragem_bot.iniciar_arbitragem()
    except Exception as e:
        url = "https://api.telegram.org/bot8359395025:AAEq1HihEgoRFl5Fz6pnx2h30lFFLBPov10/sendMessage"
        data = {
            "chat_id": "1809414360",
            "text": f"❌ Bot travou: {str(e)}",
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, data=data, timeout=10)
        except:
            pass
        print(f"❌ Erro: {e}")
        time.sleep(5)
