import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.database import async_session_maker
from app.models.job import Job
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.telegram_bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


def format_job(job: Job) -> str:
    """Format job for Telegram message."""
    score_emoji = "🟢" if (job.ai_score or 0) >= 80 else "🟡" if (job.ai_score or 0) >= 60 else "🔴"
    budget_str = f"{int(job.budget)} {job.currency}" if job.budget else "не указан"
    stack_str = ", ".join(job.stack) if job.stack else "—"
    title = job.title[:120] + ("..." if len(job.title) > 120 else "")

    return (
        f"{score_emoji} <b>Score: {job.ai_score or 0}/100</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"💰 Бюджет: {budget_str}\n"
        f"🏷 Тип: {job.job_type or '—'}\n"
        f"⚙️ Стек: {stack_str}\n"
        f"📍 {job.location or '—'}\n"
        f"🔗 <a href='{job.source_url}'>Открыть</a>\n\n"
        f"<i>{job.ai_reason or ''}</i>"
    )


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Job Aggregator</b>\n\n"
        "Я собираю вакансии и заказы и оцениваю их под твой профиль.\n\n"
        "🚀 <b>Главная команда:</b>\n"
        "/parse — запустить парсинг (Запад → RU)\n\n"
        "📊 <b>Заказы:</b>\n"
        "/jobs — последние 5\n"
        "/top — топ-10 за неделю\n"
        "/stats — статистика\n"
        "/help — помощь"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 <b>Команды</b>\n\n"
        "<b>Парсинг:</b>\n"
        "/parse — Запад → спросит про RU\n\n"
        "<b>Заказы:</b>\n"
        "/jobs — последние 5\n"
        "/top — топ-10\n"
        "/stats — статистика"
    )


@dp.message(Command("jobs"))
async def cmd_jobs(message: types.Message):
    async with async_session_maker() as db:
        result = await db.execute(
            select(Job)
            .where(Job.ai_score >= settings.min_display_score)
            .order_by(desc(Job.created_at))
            .limit(5)
        )
        jobs = result.scalars().all()

    if not jobs:
        await message.answer("Пока нет подходящих заказов. Жди уведомлений!")
        return

    for job in jobs:
        await message.answer(format_job(job), disable_web_page_preview=True)
        await asyncio.sleep(0.5)


@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    from datetime import datetime, timedelta

    week_ago = datetime.utcnow() - timedelta(days=7)

    async with async_session_maker() as db:
        result = await db.execute(
            select(Job)
            .where(Job.created_at >= week_ago)
            .where(Job.ai_score.isnot(None))
            .order_by(desc(Job.ai_score), desc(Job.created_at))
            .limit(10)
        )
        jobs = result.scalars().all()

    if not jobs:
        await message.answer("Нет заказов за неделю.")
        return

    for job in jobs:
        await message.answer(format_job(job), disable_web_page_preview=True)
        await asyncio.sleep(0.5)


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    from sqlalchemy import func

    async with async_session_maker() as db:
        total = (await db.execute(select(func.count(Job.id)))).scalar() or 0
        high_score = (
            await db.execute(
                select(func.count(Job.id)).where(Job.ai_score >= 80)
            )
        ).scalar() or 0
        avg_score = (
            await db.execute(select(func.avg(Job.ai_score)).where(Job.ai_score.isnot(None)))
        ).scalar()

    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"Всего заказов: {total}\n"
        f"С высоким score (≥80): {high_score}\n"
        f"Средний score: {round(float(avg_score), 1) if avg_score else '—'}"
    )
    await message.answer(text)


async def notify_new_job(job_id: int):
    """Send notification about new high-score job to owner."""
    if not settings.telegram_owner_chat_id:
        return

    async with async_session_maker() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

    if not job or (job.ai_score or 0) < settings.notification_score_threshold:
        return

    try:
        await bot.send_message(
            chat_id=settings.telegram_owner_chat_id,
            text=f"🔥 <b>Новый подходящий заказ!</b>\n\n{format_job(job)}",
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


async def start_bot():
    """Start the Telegram bot (polling)."""
    try:
        logger.info("Starting Telegram bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

@dp.message(Command("parse"))
async def cmd_parse(message: types.Message):
    """Запад → спросить про RU."""
    from app.tasks.scheduler import run_parsers

    await message.answer("🌍 Парсинг <b>западных</b> источников... (VPN включён?)")

    try:
        count_western = await run_parsers(mode="western")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)[:200]}")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, парсить RU", callback_data="parse_ru_yes"),
                InlineKeyboardButton(text="❌ Нет, готово", callback_data="parse_ru_no"),
            ]
        ]
    )

    await message.answer(
        f"✅ Запад собран (<b>{count_western}</b> новых).\n\n"
        f"🇷🇺 <b>Парсить российские источники?</b>\n"
        f"<i>Выключи VPN перед продолжением.</i>",
        reply_markup=keyboard,
    )


@dp.callback_query(F.data == "parse_ru_yes")
async def cb_parse_ru_yes(callback: types.CallbackQuery):
    from app.tasks.scheduler import run_parsers

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("🇷🇺 Парсинг <b>RU</b> источников...")

    try:
        count_ru = await run_parsers(mode="ru")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)[:200]}")
        await callback.answer()
        return

    await callback.message.answer(
        f"✅ RU собран (<b>{count_ru}</b> новых).\n\n"
        f"Смотри /jobs или /top."
    )
    await callback.answer()


@dp.callback_query(F.data == "parse_ru_no")
async def cb_parse_ru_no(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("👌 Ок. Парсинг завершён. Смотри /jobs или /top.")
    await callback.answer()

async def shutdown_bot():
    """Gracefully shutdown bot."""
    await bot.session.close()