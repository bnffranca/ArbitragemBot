import time
import requests
import arbitragem_bot

print("🟢 Bot de Arbitragem Interna (MEXC) iniciado com sucesso!")

while True:
    try:
        arbitragem_bot.run_bot()
    except Exception as e:
        url = f"https://api.telegram.org/bot{arbitragem_bot.TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": arbitragem_bot.CHAT_ID,
            "text": f"❌ Bot crashed: {str(e)}",
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, data=data, timeout=10)
        except:
            pass
        print(f"❌ Error: {e}")
        time.sleep(5)
