import asyncio
import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from analyzer import analyze_geopolitical_signal
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "")  # comma-separated, leave empty = no restriction

def is_allowed(update: Update) -> bool:
    if not ALLOWED_CHAT_IDS.strip():
        return True
    allowed = [int(x.strip()) for x in ALLOWED_CHAT_IDS.split(",") if x.strip()]
    return update.effective_chat.id in allowed

# ──────────────────────────────────────────────
#  /start
# ──────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    text = (
        "🌍 *GeoSignal Bot — Trading Geopolítico*\n\n"
        "Analizo las noticias globales en tiempo real y calculo señales de "
        "compra/venta basadas *solo* en el contexto geopolítico mundial.\n\n"
        "📌 *Comandos:*\n"
        "• `/signal` — Señal completa NAS100 + XAUUSD\n"
        "• `/nas100` — Solo Nasdaq 100\n"
        "• `/xauusd` — Solo Oro (XAU/USD)\n"
        "• `/news` — Titulares geopolíticos usados\n"
        "• `/help` — Ayuda\n\n"
        "⚡ Cada señal se genera en el momento de pedirla con noticias frescas."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ──────────────────────────────────────────────
#  /signal  (ambos instrumentos)
# ──────────────────────────────────────────────
async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    msg = await update.message.reply_text(
        "⏳ Recopilando noticias geopolíticas globales y analizando…\n"
        "_Esto puede tardar ~15-20 segundos_",
        parse_mode="Markdown"
    )
    try:
        result = await analyze_geopolitical_signal(["NAS100", "XAUUSD"])
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error en /signal: {e}")
        await msg.edit_text(f"❌ Error al analizar: {e}")

# ──────────────────────────────────────────────
#  /nas100
# ──────────────────────────────────────────────
async def cmd_nas100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    msg = await update.message.reply_text("⏳ Analizando NAS100 geopolíticamente…")
    try:
        result = await analyze_geopolitical_signal(["NAS100"])
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

# ──────────────────────────────────────────────
#  /xauusd
# ──────────────────────────────────────────────
async def cmd_xauusd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    msg = await update.message.reply_text("⏳ Analizando XAUUSD (Oro) geopolíticamente…")
    try:
        result = await analyze_geopolitical_signal(["XAUUSD"])
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

# ──────────────────────────────────────────────
#  /news  — muestra titulares usados
# ──────────────────────────────────────────────
async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    from news_fetcher import get_all_news
    msg = await update.message.reply_text("⏳ Obteniendo noticias…")
    try:
        articles = await get_all_news()
        lines = [f"📰 *Últimas {len(articles)} noticias geopolíticas analizadas:*\n"]
        for i, a in enumerate(articles[:20], 1):
            lines.append(f"{i}\\. [{a['source']}] {a['title']}")
        text = "\n".join(lines)
        # Telegram limit 4096 chars
        if len(text) > 4000:
            text = text[:4000] + "\n…"
        await msg.edit_text(text, parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

# ──────────────────────────────────────────────
#  /help
# ──────────────────────────────────────────────
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    text = (
        "ℹ️ *GeoSignal Bot — Cómo funciona*\n\n"
        "1️⃣ Al pedir una señal, el bot descarga noticias en tiempo real de:\n"
        "   Reuters, BBC, Al Jazeera, Financial Times, Associated Press y NewsAPI.\n\n"
        "2️⃣ Filtra noticias con relevancia geopolítica y macroeconómica.\n\n"
        "3️⃣ Las envía a Claude AI para análisis geopolítico profundo.\n\n"
        "4️⃣ La IA calcula porcentajes de COMPRAR / VENDER / NEUTRAL para cada instrumento.\n\n"
        "⚠️ *Aviso:* Esta señal es solo orientativa. "
        "No es asesoramiento financiero. Opera siempre con gestión de riesgo."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Falta TELEGRAM_TOKEN en variables de entorno")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("signal", cmd_signal))
    app.add_handler(CommandHandler("nas100", cmd_nas100))
    app.add_handler(CommandHandler("xauusd", cmd_xauusd))
    app.add_handler(CommandHandler("news",   cmd_news))
    app.add_handler(CommandHandler("help",   cmd_help))

    logger.info("🚀 GeoSignal Bot iniciado")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
