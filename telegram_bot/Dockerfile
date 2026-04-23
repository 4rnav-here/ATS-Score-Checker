FROM python:3.11-slim

WORKDIR /app

# Copy bot requirements and install (build context is project root)
COPY telegram_bot/requirements-bot.txt .
RUN pip install --no-cache-dir -r requirements-bot.txt

# Copy only the telegram_bot package (not the entire project)
COPY telegram_bot/ telegram_bot/

# No CMD here — docker-compose overrides it per service
