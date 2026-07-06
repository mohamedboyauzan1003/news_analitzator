content = """import os
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
from datetime import datetime, timezone
from news_fetcher import get_all_news

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = "Eres un analista geopolitico senior en mercados financieros. Analiza SOLO desde perspectiva geopolitica. NAS100 sube con optimismo USA/Fed dovish, baja con tensiones EEUU-China/recesion. XAUUSD sube con guerras/inflacion/debilidad dolar, baja con dolar fuerte/Fed hawkish."

def build_prompt(instruments, news_text, now):
    ins = " y ".join(instruments)
    return f"FECHA: {now}\\n\\nNOTICIAS:\\n{news_text}\\n\\nGenera senales para: {ins}\\n\\nPor cada instrumento indica: Senal (COMPRAR/VENDER/NEUTRAL), % Comprar, % Vender, % Neutral (suman 100%), 3 factores geopoliticos concretos, horizonte temporal, riesgos. Responde en espanol."

def format_news(articles):
    return "\\n".join([f"{i}. [{a['source']}] {a['title']}" for i, a in enumerate(articles, 1)])

async def analyze_geopolitical_signal(instruments):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    articles = await get_all_news()
    if not articles:
        return "No se pudieron obtener noticias. Intenta de nuevo."
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(instruments, format_news(articles), now)}
        ],
        max_tokens=1800,
        temperature=0.3,
    )
    analysis = response.choices[0].message.content.strip()
    return f"SENAL GEOPOLITICA - {' + '.join(instruments)}\\n{now}\\n{len(articles)} noticias\\n\\n{analysis}"
"""

with open("analyzer.py", "w", encoding="utf-8") as f:
    f.write(content)
print("analyzer.py actualizado OK")