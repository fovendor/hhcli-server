import os
import logging
from flask import Flask, request, jsonify
import requests

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Загружаем секреты из переменных окружения
CLIENT_ID = os.environ.get("HH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("HH_CLIENT_SECRET")
OAUTH_URL = "https://hh.ru/oauth"
# Этот Redirect URI должен ТОЧНО совпадать с тем, что указан в настройках приложения hh-cli на dev.hh.ru
REDIRECT_URI = "http://127.0.0.1:9037/oauth_callback"


@app.route('/api/get_config', methods=['GET'])
def get_config():
    """Отдает публичный Client ID клиенту hh-cli."""
    if not CLIENT_ID:
        logging.error("Ошибка конфигурации сервера: HH_CLIENT_ID не установлен.")
        return jsonify({"error": "Server configuration error"}), 500
    
    logging.info("Конфигурация (Client ID) успешно отправлена клиенту.")
    return jsonify({"client_id": CLIENT_ID})


@app.route('/api/exchange_code', methods=['POST'])
def exchange_code():
    """Обменивает authorization_code на access_token, используя секреты сервера."""
    if not CLIENT_ID or not CLIENT_SECRET:
        logging.error("Ошибка конфигурации сервера: HH_CLIENT_ID или HH_CLIENT_SECRET не установлены.")
        return jsonify({"error": "Server configuration error"}), 500

    data = request.get_json()
    if not data or "code" not in data:
        logging.warning("Некорректный запрос: отсутствует 'code' в теле запроса.")
        return jsonify({"error": "Authorization code is missing"}), 400

    code = data["code"]
    logging.info("Получен код авторизации, подготовка к обмену на токен.")

    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    try:
        response = requests.post(f"{OAUTH_URL}/token", data=payload)
        response.raise_for_status()
        token_data = response.json()
        logging.info("Код успешно обменен на токен.")
        return jsonify(token_data)
    except requests.RequestException as e:
        error_details = str(e)
        if e.response is not None:
            try:
                error_details = e.response.json()
            except ValueError:
                error_details = e.response.text
        logging.error(f"Не удалось обменять токен через API hh.ru. Детали: {error_details}")
        return jsonify({"error": "Failed to exchange token with upstream API", "details": error_details}), 502
