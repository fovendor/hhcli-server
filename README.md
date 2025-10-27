# hh-cli-server

[![PyPI version](https://img.shields.io/pypi/v/hhcli-server)](https://pypi.org/project/hhcli-server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Безопасный прокси-сервер для [hh-cli](https://github.com/fovendor/hhcli).

## Описание

`hh-cli-server` — это веб-сервис, который выступает в роли посредника между [hh-cli](https://github.com/fovendor/hhcli) и API HeadHunter. Его единственная задача — решить фундаментальную проблему безопасности: **`Client Secret` никогда не должен храниться в клиентском приложении.** Если поместить его в код `hh-cli`, любой сможет его извлечь и скомпрометировать.

> Примечание: Клиент `hh-cli` оперирует только временным кодом авторизации, а сервер проводит рукопожатие и получает токен доступа, `Client Secret` никогда не покидает сервер.

## Развёртывание и разработка

Для развёртывания вам понадобится:

1.  Сервер под управлением Linux (инструкция написана для Debian/Ubuntu).
2.  Доменное имя, делегированное на IP-адрес вашего сервера.
3.  Python 3.9+ и `pip`.
4.  `Client ID` и `Client Secret` от [dev.hh.ru](https://dev.hh.ru/).

### Шаг 1: Клонирование

Подключитесь к серверу по SSH и склонируйте репозиторий:

```bash
git clone https://github.com/fovendor/hhcli-server.git
cd hhcli-server
```

### Шаг 2: Настройка окружения

Установка venv и создание окружения:

```bash
sudo apt update && sudo apt install -y python3-venv
python3 -m venv venv
source venv/bin/activate
```

Установка зависимостей:

```bash
pip install -r <(poetry export -f requirements.txt)
```

### Шаг 3: Файл с ключами

Создайте файл `.env` в корне проекта для хранения ваших API-ключей.

```bash
nano .env
```

Добавьте в него ваши ключи в следующем формате:
```bash
HH_CLIENT_ID="ВАШ_ID_КЛИЕНТА"
HH_CLIENT_SECRET="ВАШ_СЕКРЕТ_КЛИЕНТА"
```
> **Важно:** Этот файл никогда не должен попадать в Git. Он уже добавлен в `.gitignore`.

### Шаг 4: Настройка Systemd для автозапуска

Создайте сервис, который будет автоматически запускать Gunicorn и стартовать приложение.

```bash
sudo nano /etc/systemd/system/hhcli-server.service
```

Создайте конфигурацию, **заменив `your_user` на имя пользователя системы**:
```ini
[Unit]
Description=Gunicorn instance to serve hhcli-server
After=network.target

[Service]
User=your_user
Group=www-data
# ЗАМЕНИТЕ 'your_user'
WorkingDirectory=/home/your_user/hhcli-server
# ЗАМЕНИТЕ 'your_user'
EnvironmentFile=/home/your_user/hhcli-server/.env
# ЗАМЕНИТЕ 'your_user'
ExecStart=/home/your_user/hhcli-server/venv/bin/gunicorn --workers 3 --bind unix:hhcli_server.sock -m 007 hhcli_server.app:app

[Install]
WantedBy=multi-user.target
```

Запустите и включите сервис:
```bash
sudo systemctl start hhcli-server
sudo systemctl enable hhcli-server

# Проверьте статус. Должно быть "active (running)"
sudo systemctl status hhcli-server
```

### Шаг 5: Настройка Nginx

Скопируйте [пример конфигурации](/nginx_config/hhcli-server.conf). Нужно заменить все вхождения `your_domain.com` и `your_user` на реальные значения.

```bash
sudo cp nginx_config/hhcli-server.conf /etc/nginx/sites-available/your_domain.com.conf
sudo nano /etc/nginx/sites-available/your_domain.com.conf
```

Включите сайт и проверьте конфигурацию Nginx:
```bash
# ЗАМЕНИТЕ 'your_domain.com'
sudo ln -s /etc/nginx/sites-available/your_domain.com.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Шаг 6: Настройка HTTPS с Certbot

Это финальный шаг для обеспечения безопасности.

```bash
# Устанавливаем Certbot
sudo apt install certbot python3-certbot-nginx

# ЗАМЕНИТЕ 'your_domain.com'
sudo certbot --nginx -d your_domain.com
```
> Следуйте инструкциям Certbot. Он автоматически получит SSL-сертификат и настроит Nginx для работы по HTTPS.

**Готово!** Ваш прокси-сервер развернут и доступен по адресу `https://your_domain.com/`.

## API Эндпоинты

- `GET /api/get_config`: Возвращает публичный `client_id`.
- `POST /api/exchange_code`: Принимает JSON `{ "code": "..." }` и обменивает его на `access_token`.

## Лицензия

[MIT](LICENSE)
