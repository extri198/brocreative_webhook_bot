import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")


# Отправка сообщения в Telegram через requests
def send_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set!")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Ошибка при отправке сообщения в Telegram: {e}")


# Получение метаданных токена из Helius
def get_token_symbol(mint):
    try:
        if mint == "So11111111111111111111111111111111111111112":
            return "SOL"

        url = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"mintAccounts": [mint]}

        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        metadata = res.json()
        if metadata and isinstance(metadata, list):
            return metadata[0].get("symbol") or None
        return None
    except Exception as e:
        print(f"❌ Ошибка при получении метаданных токена {mint}: {e}")
        return None


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Получены данные:", json.dumps(data, indent=2, ensure_ascii=False))

    for tx in data:
        message_lines = []
        description = tx.get("description", "")
        if description:
            message_lines.append(f"<b>{description}</b>")

        transfers = tx.get("tokenTransfers", [])
        for transfer in transfers:
            mint = transfer.get("mint")
            amount = transfer.get("tokenAmount")
            from_user = transfer.get("fromUserAccount")
            to_user = transfer.get("toUserAccount")

            symbol = get_token_symbol(mint)
            if not symbol:
                symbol = "Unknown"

            # Определение направления и форматирование суммы
            try:
                amount_value = float(amount)
            except (TypeError, ValueError):
                amount_value = 0

            if amount_value > 0:
                direction = "🟢"
            elif amount_value < 0:
                direction = "🔴"
            else:
                direction = "🔁"

            amount_formatted = f"<b>{abs(amount_value):.9f}</b>"
            line = f"{direction} {amount_formatted} {symbol}"
            message_lines.append(line)

        if message_lines:
            message_text = "\n".join(message_lines)
            send_message(message_text)

    return "OK"


@app.route("/")
def root():
    return "Бот работает"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
