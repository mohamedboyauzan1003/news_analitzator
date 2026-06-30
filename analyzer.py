"""
analyzer.py
Envía las noticias a Claude AI y obtiene señales geopolíticas de compra/venta
con porcentajes de confianza para NAS100 y XAUUSD.
"""

import os
import logging
from datetime import datetime, timezone
from anthropic import AsyncAnthropic
from news_fetcher import get_all_news

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Prompt del sistema ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un analista geopolítico senior especializado en mercados financieros globales.
Tu función es evaluar el contexto geopolítico y macroeconómico mundial para generar señales de trading.

REGLAS ESTRICTAS:
- Analiza SOLO desde perspectiva geopolítica y macroeconómica global (NO indicadores técnicos)
- Sé específico: cita noticias concretas que justifican cada señal
- Los porcentajes deben reflejar el peso REAL del contexto geopolítico actual
- Si el contexto es muy incierto, refleja eso con porcentajes más bajos o NEUTRAL dominante
- Siempre indica el horizonte temporal más probable de la señal (intraday / 1-3 días / semanal)

CONOCIMIENTO BASE:
NAS100 (Nasdaq 100):
- Sube con: optimismo económico USA, Fed dovish, buenas relaciones EEUU-China, estabilidad geopolítica, ciclo tech alcista
- Baja con: tensiones EEUU-China (semicond.), Fed hawkish, recesión, guerras que afecten suministro energético/chips

XAUUSD (Oro):
- Sube con: incertidumbre geopolítica, guerras, inflación alta, debilidad dólar, compras bancos centrales, crisis bancaria
- Baja con: dólar fuerte, Fed subiendo tipos agresivamente, reducción de riesgo global, estabilidad geopolítica"""

# ── Formato de respuesta requerido ─────────────────────────────────────────────
def build_user_prompt(instruments: list, news_text: str, now: str) -> str:
    instruments_str = " y ".join(instruments)
    return f"""FECHA Y HORA ACTUAL: {now}
TOTAL NOTICIAS ANALIZADAS: incluidas abajo

=== NOTICIAS GEOPOLÍTICAS RECIENTES ===
{news_text}
========================================

Analiza las noticias anteriores y genera señales geopolíticas para: {instruments_str}

Para CADA instrumento usa EXACTAMENTE este formato:

---
📊 **[INSTRUMENTO]**
🎯 **Señal:** COMPRAR / VENDER / NEUTRAL
📈 **% Comprar:** XX%
📉 **% Vender:** XX%
⚖️ **% Neutral:** XX%
_(los tres porcentajes deben sumar 100%)_

🔍 **Factores geopolíticos clave:**
1. [factor 1 con noticia específica]
2. [factor 2 con noticia específica]
3. [factor 3 con noticia específica]

⏱️ **Horizonte:** [intraday / 1-3 días / semanal]
⚠️ **Riesgos a vigilar:** [2-3 riesgos geopolíticos concretos]
---

Responde en español. Sé conciso pero preciso. No añadas disclaimers al final."""

def format_news(articles: list) -> str:
    lines = []
    for i, a in enumerate(articles, 1):
        pub = a.get("published", "")[:16] if a.get("published") else ""
        lines.append(f"{i}. [{a['source']}]{' (' + pub + ')' if pub else ''} {a['title']}")
        if a.get("summary"):
            lines.append(f"   → {a['summary'][:200]}")
    return "\n".join(lines)

def escape_md(text: str) -> str:
    """Escapa caracteres problemáticos para Telegram MarkdownV2."""
    # Para Markdown V1 (parse_mode="Markdown") no se necesita escapar tanto
    return text

# ── Función principal ──────────────────────────────────────────────────────────
async def analyze_geopolitical_signal(instruments: list) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # 1. Obtener noticias frescas
    logger.info("Obteniendo noticias…")
    articles = await get_all_news()

    if not articles:
        return (
            "⚠️ *No se pudieron obtener noticias en este momento.*\n"
            "Verifica la conexión o las API keys. Intenta de nuevo en unos minutos."
        )

    news_text = format_news(articles)
    user_prompt = build_user_prompt(instruments, news_text, now)

    # 2. Llamar a Claude
    logger.info(f"Enviando {len(articles)} noticias a Claude para análisis…")
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    analysis = message.content[0].text.strip()

    # 3. Construir respuesta final
    instruments_label = " + ".join(instruments)
    header = (
        f"🌍 *SEÑAL GEOPOLÍTICA — {instruments_label}*\n"
        f"🕐 {now}\n"
        f"📰 {len(articles)} noticias analizadas en tiempo real\n"
        f"{'─' * 32}\n\n"
    )

    footer = (
        f"\n{'─' * 32}\n"
        f"_⚠️ Señal geopolítica. No es asesoramiento financiero._\n"
        f"_Usa siempre gestión de riesgo._"
    )

    return header + analysis + footer
