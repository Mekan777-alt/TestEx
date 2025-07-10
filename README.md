# 🎯 Система обработки жалоб клиентов

Автоматизированная система для обработки жалоб клиентов с ИИ-анализом, интеграцией внешних API и автоматизацией через n8n.

## 🚀 Возможности

- **📝 REST API** для создания и управления жалобами
- **🤖 ИИ-категоризация** жалоб через OpenAI GPT-3.5
- **😊 Анализ тональности** через APILayer Sentiment Analysis
- **🌍 Геолокация по IP** с автоматическим определением
- **🛡️ Защита от спама** через API Ninjas
- **📊 Автоматизация** через n8n workflow
- **📱 Telegram уведомления** для технических жалоб
- **📋 Google Sheets интеграция** для жалоб по оплате

## 🔗 Доступные URL

- **API Docs**: https://api.testexcomplaint.ru/docs
- **n8n**: https://n8n.testexcomplaint.ru 

## ⚡ Быстрый запуск

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/Mekan777-alt/TestEx.git
cd TestEx
```

### 2. Настройте переменные окружения
```bash
cp .env.example .env
# Отредактируйте .env файл с API ключами
```

### 3. Запустите систему
```bash
docker-compose up -d
```

## 🔧 Конфигурация

### Обязательные API ключи в .env:
```env
# APILayer Sentiment Analysis
SENTIMENT_API_KEY=your_apilayer_key_here

# OpenAI для категоризации
OPENAI_API_KEY=your_openai_key_here

```

## 📊 API Endpoints

### Создание жалобы
```bash
curl -X POST "https://api.testexcomplaint.ru/complaints/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Не приходит SMS-код для входа в приложение"}'
```

### Получение списка жалоб
```bash
curl "https://api.testexcomplaint.ru/complaints/?status=open&limit=10"
```

### Health Check
```bash
curl "https://api.testexcomplaint.ru/health"
```

## 🤖 Автоматизация n8n

Система автоматически:
1. **Каждый час** проверяет новые жалобы
2. **Технические жалобы** → отправляет в Telegram
3. **Жалобы по оплате** → записывает в Google Sheets
4. **Автоматически закрывает** обработанные жалобы

### Настройка workflow:
1. Зайдите в https://n8n.testexcomplaint.ru
2. Импортируйте файл `My_workflow.json`
3. Настройте credentials для Telegram и Google Sheets


## 🛠️ Технологии

- **Backend**: FastAPI, SQLAlchemy, aiosqlite
- **ИИ**: OpenAI GPT-3.5 Turbo
- **Анализ тональности**: APILayer Sentiment Analysis
- **Автоматизация**: n8n
- **Развертывание**: Docker, Docker Compose, Nginx
- **SSL**: Let's Encrypt (Certbot)


## 🔍 Мониторинг

### Проверка состояния сервисов:
```bash
# Статус контейнеров
docker-compose ps

# Логи API
docker logs -f complaints-api

# Логи n8n
docker logs -f complaints-n8n

# Health check всех сервисов
curl https://api.testexcomplaint.ru/health
```

## 🆘 Поддержка

### Типичные проблемы:

1. **API недоступно** - проверьте docker контейнеры и nginx
2. **Ошибки ИИ** - проверьте API ключи OpenAI и APILayer
3. **n8n workflow не работает** - проверьте credentials в n8n

### Логи и диагностика:
```bash
# Просмотр всех логов
docker-compose logs

# Проверка nginx
sudo nginx -t
sudo systemctl status nginx

# Проверка SSL сертификатов
sudo certbot certificates
```
---
