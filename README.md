# Job Aggregator

> AI-powered job aggregator that scrapes Telegram channels and Hacker News, scores each posting against a developer profile using an LLM, and delivers top matches to a Telegram bot.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Docker](https://img.shields.io/badge/Docker-compose-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.x-blue)
![Groq](https://img.shields.io/badge/Groq-gpt--oss--20b-orange)

## The Problem

Finding a junior developer job or freelance gig is a full-time job itself. Hundreds of postings across dozens of channels, and 95% of them are either senior roles, wrong stack, or plain spam. Manual filtering takes hours per day.

**Job Aggregator solves this**: it collects postings from multiple sources, uses an LLM to score each one against a specific developer profile, and sends only the relevant matches to Telegram.

## Features

- **Multi-source parsing** — Telegram channels (RU + Western) and Hacker News "Who is hiring?" threads
- **Split modes** — `western`, `ru`, `all` (with manual trigger via bot)
- **AI scoring (0-100)** — every posting is evaluated by `gpt-oss-20b` with a strict prompt
- **Hard caps for senior roles** — roles with `Senior`/`Staff`/`Lead`/`Founding`/`Manager` in the title automatically get max 25 points, regardless of stack match
- **Auto-filtering** — postings older than 30 days are skipped, duplicates are de-duplicated by `raw_hash`
- **Telegram bot** — manual parse trigger with confirmation flow, job browsing, top-10, statistics
- **Full Docker** — `docker-compose up` and you're running

## Screenshots

### Bot menu
![Bot menu](docs/screenshots/bot-menu.png)

### Job feed
![Job feed](docs/screenshots/bot-jobs.png)

### Top matches
![Top matches](docs/screenshots/bot-top.png)

### Stats
![Stats](docs/screenshots/bot-stats.png)

*(screenshots coming soon — bot is operational, capturing assets)*

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Web framework | FastAPI |
| ORM | SQLAlchemy (async) |
| Database | PostgreSQL 16 |
| Cache / queue | Redis 7 |
| Migrations | Alembic |
| Telegram bot | aiogram 3.x |
| Scraping | tgscraper, httpx, BeautifulSoup |
| LLM | Groq API — `openai/gpt-oss-20b` |
| Scheduler | APScheduler (manual mode) |
| Container | Docker + docker-compose |

## Architecture


