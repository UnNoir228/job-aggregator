# Job Aggregator

Система автоматического сбора, фильтрации и AI-оценки вакансий и заказов с разных площадок.

## Что делает

- Парсит вакансии с hh.ru, kwork.ru, Telegram-каналов.
- Приводит к единому формату, дедуплицирует.
- Оценивает через AI (Groq/llama-3.3) по профилю разработчика.
- Отправляет подходящие заказы в Telegram.
- Показывает всё в веб-дашборде с фильтрами.

## Стек

**Backend:** Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, Playwright, aiogram, APScheduler, Groq API.
**Frontend:** Next.js 14, TypeScript, Tailwind.
**Инфра:** Docker, docker-compose.

## Локальный запуск

### 1. Клонируй репозиторий

```bash
git clone https://github.com/UnNoir228/job-aggregator.git
cd job-aggregator