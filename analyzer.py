import os
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone, timedelta
from news_fetcher import get_all_news

logger = logging.getLogger(__name__)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# openrouter/free = router oficial que elige automaticamente el mejor modelo
# gratuito disponible en cada momento. Nunca da 404.
# Si esta saturado, fallback a modelos especificos actualizados julio 2026
MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-4o-mini:free",
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "cohere/north-mini-code:free",
]

_cache = {}
CACHE_MINUTES = 15

def _get_cache(key):
    if key in _cache:
        entry = _cache[key]
        if datetime.now(timezone.utc) < entry["expires"]:
            remaining = int((entry["expires"] - datetime.now(timezone.utc)).total_seconds() / 60)
            return entry["result"], remaining
    return None, 0

def _set_cache(key, result):
    _cache[key] = {
        "result":  result,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=CACHE_MINUTES),
    }

SYSTEM_PROMPT = """Eres analista geopolitico senior en mercados financieros globales.
Analiza SOLO desde perspectiva geopolitica y macroeconomica. NUNCA uses indicadores tecnicos.
Cita noticias concretas para justificar cada factor.
NAS100: sube con Fed dovish/paz geopolitica/EEUU-China estable/optimismo USA.
Baja con Fed hawkish/tensiones China/recesion/guerras que afecten energia o chips.
XAUUSD: sube con guerras/inflacion/dolar debil/crisis bancaria/bancos centrales comprando.
Baja con dolar fuerte/Fed subiendo tipos/reduccion riesgo global."""

def build_prompt(instruments, news_text, now, count):
    ins = " y ".join(instruments)
    return f"""FECHA: {now} | NOTICIAS ANALIZADAS: {count}

=== TITULARES GEOPOLITICOS GLOBALES ===
{news_text}
=======================================

Genera senales geopoliticas para: {ins}

Por cada instrumento usa ESTE FORMATO EXACTO:

INSTRUMENTO: [nombre]
Senal: COMPRAR / VENDER / NEUTRAL
% Comprar: XX%
% Vender: XX%
% Neutral: XX%
(los tres suman exactamente 100%)

Factores determinantes:
1. [noticia concreta citada]
2. [noticia concreta citada]
3. [noticia concreta citada]

Horizonte: [intraday / 1-3 dias / semanal]
Eventos a vigilar: [3 eventos geopoliticos concretos]
Certeza del analisis: [ALTA / MEDIA / BAJA] porque [razon]

Responde en espanol. Se muy especifico."""

def format_news(articles):
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. [{a['source']}] {a['title']}")
        if a.get("summary"):
            lines.append(f"   {a['summary'][:120]}")
    return "\n".join(lines)

async def call_openrouter(session, model, prompt, attempt=0):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/geosignal-bot",
        "X-Title": "GeoSignal Bot",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens": 1500,
        "temperature": 0.1,
    }
    async with session.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=aiohttp.ClientTimeout(total=90),
    ) as resp:
        data = await resp.json()

        if resp.status == 429 and attempt < 2:
            wait = 20
            try:
                wait = int(data["error"]["metadata"].get("retry_after_seconds", 20)) + 1
            except:
                pass
            logger.info(f"Rate limit {model}, esperando {wait}s...")
            await asyncio.sleep(wait)
            return await call_openrouter(session, model, prompt, attempt + 1)

        if resp.status != 200 or "error" in data:
            raise Exception(data.get("error", {}).get("message", f"HTTP {resp.status}"))

        return data["choices"][0]["message"]["content"].strip(), model

async def analyze_geopolitical_signal(instruments):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cache_key = "_".join(sorted(instruments))

    # 1. Cache
    cached, remaining = _get_cache(cache_key)
    if cached:
        return f"[Cache: actualiza en {remaining} min]\n\n" + cached

    # 2. Noticias
    logger.info("Obteniendo noticias...")
    articles = await get_all_news()
    count = len(articles)
    if count < 5:
        return "Sin noticias disponibles. Intenta en 1 minuto."

    news_text = format_news(articles[:80])
    prompt = build_prompt(instruments, news_text, now, count)

    # 3. Probar modelos en orden
    analysis = None
    used_model = "desconocido"

    async with aiohttp.ClientSession() as session:
        for model in MODELS:
            try:
                logger.info(f"Probando: {model}")
                analysis, used_model = await call_openrouter(session, model, prompt)
                used_model = used_model.split("/")[-1].replace(":free", "")
                logger.info(f"Exito con: {model}")
                break
            except Exception as e:
                logger.warning(f"{model} -> {e}")
                await asyncio.sleep(2)
                continue

    if not analysis:
        return "Modelos temporalmente ocupados. Intenta en 30 segundos."

    label = " + ".join(instruments)
    result = (
        f"SENAL GEOPOLITICA - {label}\n"
        f"{now}\n"
        f"{count} noticias | {used_model}\n"
        f"Valida {CACHE_MINUTES} minutos\n"
        f"{'='*35}\n\n"
        f"{analysis}\n\n"
        f"{'='*35}\n"
        f"Orientativo. No es asesoramiento financiero."
    )

    _set_cache(cache_key, result)
    return result
