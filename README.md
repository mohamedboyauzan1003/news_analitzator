# 🌍 GeoSignal Bot — Trading Geopolítico por Telegram

Bot de Telegram que analiza noticias geopolíticas mundiales en tiempo real y genera señales de **compra/venta con porcentaje de confianza** para **NAS100** y **XAUUSD (Oro)**, usando IA (Claude de Anthropic).

> **Señales basadas 100% en contexto geopolítico y macroeconómico**, no en indicadores técnicos.

---

## 🤖 Cómo funciona

```
Tú escribes /signal en Telegram
        ↓
Bot descarga noticias en tiempo real
(Reuters, BBC, Al Jazeera, AP, CNBC, FT, NewsAPI…)
        ↓
Filtra las noticias geopolíticamente relevantes
        ↓
Las envía a Claude AI para análisis profundo
        ↓
Claude genera porcentajes: % Comprar / % Vender / % Neutral
        ↓
Te responde en ~15-20 segundos con la señal completa
```

---

## 📲 Comandos del bot

| Comando | Descripción |
|---------|-------------|
| `/signal` | Señal completa para NAS100 + XAUUSD |
| `/nas100` | Señal solo para Nasdaq 100 |
| `/xauusd` | Señal solo para Oro (XAU/USD) |
| `/news` | Ver las noticias que se están usando |
| `/help` | Ayuda |

---

## 🚀 Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/geosignal-bot.git
cd geosignal-bot
```

### 2. Crear las API Keys necesarias

#### 🤖 Telegram Bot Token
1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Elige un nombre y username para tu bot
4. Copia el token que te da (formato: `123456:ABC-DEF...`)

#### 🧠 Anthropic API Key (Claude)
1. Ve a [console.anthropic.com](https://console.anthropic.com)
2. Crea una cuenta o inicia sesión
3. Ve a **API Keys** → **Create Key**
4. Copia la key (empieza con `sk-ant-...`)

#### 📰 NewsAPI Key (opcional pero recomendada)
1. Ve a [newsapi.org](https://newsapi.org)
2. Regístrate gratis (100 peticiones/día)
3. Copia tu API key

### 3. Configurar variables de entorno

```bash
cp .env.example .env
nano .env   # o edita con tu editor favorito
```

Rellena los valores:
```
TELEGRAM_TOKEN=tu_token_de_botfather
ANTHROPIC_API_KEY=sk-ant-tu_key_aqui
NEWS_API_KEY=tu_newsapi_key  # opcional
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Ejecutar en local

```bash
python bot.py
```

Abre Telegram, busca tu bot por username y escribe `/start`.

---

## ☁️ Deploy en Railway (recomendado — gratis)

Railway mantiene el bot corriendo 24/7 sin que tengas que tener tu ordenador encendido.

### Paso a paso:

1. **Crea cuenta en [railway.app](https://railway.app)** (gratis con GitHub)

2. **Sube tu código a GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/geosignal-bot.git
   git push -u origin main
   ```

3. **En Railway:**
   - Haz clic en **New Project** → **Deploy from GitHub repo**
   - Selecciona tu repositorio `geosignal-bot`
   - Railway detectará el Dockerfile automáticamente

4. **Añadir variables de entorno en Railway:**
   - Ve a tu proyecto → **Variables**
   - Añade una por una:
     ```
     TELEGRAM_TOKEN = tu_token
     ANTHROPIC_API_KEY = tu_key
     NEWS_API_KEY = tu_key  (opcional)
     ```

5. Railway desplegará y tu bot estará online 24/7 ✅

---

## ☁️ Alternativa: Deploy en Render (también gratis)

1. Ve a [render.com](https://render.com) y crea cuenta
2. **New** → **Web Service** → conecta tu GitHub
3. Selecciona el repo → elige tipo **Worker**
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`
6. Añade las variables de entorno en la sección **Environment**
7. Deploy ✅

---

## 📊 Ejemplo de señal

```
🌍 SEÑAL GEOPOLÍTICA — NAS100 + XAUUSD
🕐 2025-10-15 14:32 UTC
📰 38 noticias analizadas en tiempo real
────────────────────────────────

📊 NAS100
🎯 Señal: VENDER
📈 % Comprar: 22%
📉 % Vender: 61%
⚖️ % Neutral: 17%

🔍 Factores geopolíticos clave:
1. Nuevas restricciones de EEUU a exportación de chips a China afectan directamente a semiconductores del índice (NVIDIA, AMD)
2. Fed mantiene tono hawkish tras datos de inflación superiores a lo esperado
3. Tensiones en Taiwán elevan el riesgo de disrupciones en cadena de suministro de semiconductores

⏱️ Horizonte: 1-3 días
⚠️ Riesgos a vigilar: Escalada militar en Taiwán, datos empleo USA el viernes, declaraciones Fed

---

📊 XAUUSD
🎯 Señal: COMPRAR
📈 % Comprar: 74%
📉 % Vender: 11%
⚖️ % Neutral: 15%

🔍 Factores geopolíticos clave:
1. Escalada tensión EEUU-China dispara demanda de activos refugio, oro principal beneficiario
2. Bancos centrales asiáticos acelerando compras de oro como reserva alternativa al dólar
3. Conflicto en Oriente Medio sin resolución eleva la prima de riesgo geopolítico

⏱️ Horizonte: Semanal
⚠️ Riesgos a vigilar: Acuerdo diplomático EEUU-China, fortaleza inesperada del USD, venta masiva de reservas

────────────────────────────────
⚠️ Señal geopolítica. No es asesoramiento financiero.
Usa siempre gestión de riesgo.
```

---

## 🔒 Seguridad: restringir acceso al bot

Para que solo tú (o un grupo concreto) pueda usar el bot, añade tu ID de Telegram:

1. Habla con **@userinfobot** en Telegram → te da tu ID numérico
2. En `.env` o en Railway Variables:
   ```
   ALLOWED_CHAT_IDS=123456789,987654321
   ```

---

## 🛠️ Fuentes de noticias usadas

| Fuente | Tipo |
|--------|------|
| Reuters World & Business | RSS |
| BBC World & Business | RSS |
| Al Jazeera | RSS |
| Associated Press | RSS |
| CNBC World & Finance | RSS |
| Financial Times Markets | RSS |
| Investing.com | RSS |
| NewsAPI.org | API (opcional) |
| GNews.io | API (opcional) |

---

## 📋 Estructura del proyecto

```
geosignal-bot/
├── bot.py           # Bot de Telegram — maneja comandos
├── news_fetcher.py  # Obtiene noticias de RSS + APIs
├── analyzer.py      # Envía noticias a Claude AI y procesa la señal
├── requirements.txt # Dependencias Python
├── Dockerfile       # Para deploy en Railway/Render
├── Procfile         # Para deploy en Heroku
├── railway.json     # Configuración Railway
├── .env.example     # Plantilla de variables de entorno
├── .gitignore       # Excluye .env de Git
└── README.md        # Este archivo
```

---

## ⚠️ Aviso legal

Este bot es una **herramienta de análisis informativo**. Las señales geopolíticas son orientativas y no constituyen asesoramiento financiero. Opera siempre con gestión de riesgo adecuada.
