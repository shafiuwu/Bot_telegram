# 🔔 Asistente de Recordatorios — Bot de Telegram

Bot personal de Telegram para crear y gestionar recordatorios con fecha, hora y frecuencia (única vez, diaria, semanal o mensual), construido en Python.

---

## 📋 Tabla de contenidos

- [Descripción](#-descripción)
- [Funcionalidades](#-funcionalidades)
- [Tecnologías](#️-tecnologías)
- [Decisiones de diseño](#️-decisiones-de-diseño)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Comandos](#-comandos)
- [Instalación y uso local](#-instalación-y-uso-local)

---

## 📌 Descripción

El bot te permite crear recordatorios conversando con él (te pregunta qué quieres recordar, cuándo, y con qué frecuencia), y se encarga de avisarte a la hora exacta — incluso si reinicias el bot entre medio, o si el recordatorio es recurrente.

Pensado para uso personal en un chat privado con el bot (no está diseñado para uso en grupos con múltiples usuarios).

---

## 🧩 Funcionalidades

- Creación de recordatorios mediante una conversación guiada de 3 pasos (texto → fecha/hora → frecuencia)
- 4 tipos de frecuencia: única vez, diario, semanal, mensual
- Listado de recordatorios pendientes, mostrando siempre la **próxima fecha real** en la que se disparará (no la fecha original, en el caso de los recurrentes)
- Edición de un recordatorio existente (mismo flujo de 3 preguntas, sobre uno ya creado)
- Cancelación de un recordatorio antes de que se dispare
- Recuperación automática de recordatorios pendientes si el bot se reinicia — no se pierden aunque el proceso se caiga
- `/help` con la lista de comandos disponibles

---

## ⚙️ Tecnologías

- Python 3
- [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot) (v21+, con soporte async) — maneja la conexión con la API de Telegram
- [`APScheduler`](https://apscheduler.readthedocs.io/) — programa y dispara los avisos en la fecha/hora exacta
- SQLite (vía el módulo `sqlite3` de la librería estándar) — persistencia de los recordatorios
- `python-dotenv` — manejo del token del bot fuera del código fuente

---

## 📁 Estructura del proyecto

```
asistente-telegram/
├── bot.py             # Lógica del bot: handlers de Telegram, scheduler, arranque
├── db.py               # Acceso a la base de datos SQLite (recordatorios)
├── date_parser.py       # Conversión de texto "DD/MM HH:MM" a datetime
├── .env                 # Token del bot (no se sube al repositorio)
├── .gitignore
└── recordatorios.db      # Base de datos SQLite (se genera sola al iniciar)
```

---

## 💬 Comandos

| Comando | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida |
| `/help` | Lista de comandos disponibles |
| `/recordar` | Crea un recordatorio nuevo (conversación guiada) |
| `/recordatorios` | Lista los recordatorios pendientes |
| `/editar <id>` | Edita un recordatorio existente |
| `/cancelar <id>` | Cancela un recordatorio pendiente |

---

## 🛠️ Instalación y uso local

### Requisitos previos
- [Python 3.10+](https://www.python.org/)
- Un bot creado con [@BotFather](https://t.me/BotFather) en Telegram (necesitas el token)

### Pasos

1. Clona el repositorio y entra a la carpeta:
   ```bash
   git clone https://github.com/shafiuwu/Bot_telegram.git
   cd Bot_telegram
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crea un archivo `.env` en la raíz del proyecto:
   ```
   BOT_TOKEN=tu_token_de_botfather
   ```

5. Corre el bot:
   ```bash
   python bot.py
   ```

La base de datos `recordatorios.db` se crea automáticamente la primera vez que el bot arranca.

---
