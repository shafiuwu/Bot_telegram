import os
from datetime import datetime

from db import (
    crear_tabla,
    migrar_frecuencia,
    agregar_recordatorio,
    obtener_pendientes,
    marcar_enviado,
    cancelar_recordatorio,
    obtener_recordatorio_por_id,
    actualizar_recordatorio
)
from date_parser import parsear_fecha_hora

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

load_dotenv()
token = os.getenv("BOT_TOKEN")


ESPERANDO_TEXTO, ESPERANDO_FECHA, ESPERANDO_FRECUENCIA = range(3)


# ---------- /start ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Bienvenido al botfiu\n Ocupa /help para ver los comandos disponibles .")

# ---------- /help ----------

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📋 *Comandos disponibles*\n\n"
        "🔔 *Recordatorios*\n"
        "/recordar — crear un recordatorio nuevo (te voy preguntando texto, fecha y frecuencia)\n"
        "/recordatorios — ver tus recordatorios pendientes\n"
        "/editar id — editar un recordatorio existente\n"
        "/cancelar id — cancelar un recordatorio\n\n"
        "ℹ️ /help — ver este mensaje"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

# ---------- /recordar (conversación de varios pasos) ----------

async def recordar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¿Qué quieres recordar?")
    return ESPERANDO_TEXTO


async def recibir_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["texto"] = update.message.text
    await update.message.reply_text("¿Cuándo? Formato: DD/MM HH:MM")
    return ESPERANDO_FECHA


async def recibir_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partes = update.message.text.split()

    if len(partes) != 2:
        await update.message.reply_text("Formato inválido. Usa: DD/MM HH:MM")
        return ESPERANDO_FECHA

    try:
        fecha_hora = parsear_fecha_hora(partes[0], partes[1])
    except ValueError:
        await update.message.reply_text("No entendí esa fecha/hora. Intenta de nuevo: DD/MM HH:MM")
        return ESPERANDO_FECHA

    if fecha_hora <= datetime.now():
        await update.message.reply_text("Esa fecha ya pasó. Intenta con una futura: DD/MM HH:MM")
        return ESPERANDO_FECHA

    context.user_data["fecha_hora"] = fecha_hora

    teclado = ReplyKeyboardMarkup(
        [["Única vez", "Diario", "Semanal", "Mensual"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text("¿Con qué frecuencia?", reply_markup=teclado)
    return ESPERANDO_FRECUENCIA


async def recibir_frecuencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opcion = update.message.text.lower()
    mapa = {"única vez": "unica", "diario": "diario", "semanal": "semanal", "mensual": "mensual"}

    if opcion not in mapa:
        await update.message.reply_text("Elige una opción del teclado, por favor.")
        return ESPERANDO_FRECUENCIA

    frecuencia = mapa[opcion]
    texto = context.user_data["texto"]
    fecha_hora = context.user_data["fecha_hora"]
    chat_id = update.effective_chat.id
    fecha_hora_texto = fecha_hora.strftime("%Y-%m-%d %H:%M:%S")

    id_editando = context.user_data.get("editando_id")  # None si es creación nueva

    if id_editando:
        actualizar_recordatorio(id_editando, texto, fecha_hora_texto, frecuencia)

        try:
            scheduler.remove_job(str(id_editando))
        except Exception:
            pass
        programar_job(id_editando, chat_id, texto, fecha_hora, frecuencia)

        mensaje = f"Recordatorio {id_editando} actualizado: '{texto}' — {fecha_hora_texto} ({frecuencia})"
    else:
        id_recordatorio = agregar_recordatorio(chat_id, texto, fecha_hora_texto, frecuencia)
        programar_job(id_recordatorio, chat_id, texto, fecha_hora, frecuencia)
        mensaje = f"Listo, guardado ({frecuencia}): '{texto}' — {fecha_hora_texto}"

    await update.message.reply_text(mensaje, reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


async def cancelar_conversacion(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()
    await update.message.reply_text("Creación de recordatorio cancelada.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ---------- /recordatorios ----------

async def recordatorios_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pendientes = obtener_pendientes()

    if not pendientes:
        await update.message.reply_text("No tienes recordatorios pendientes.")
        return

    lineas = []
    for id_r, chat_id, texto, fecha_hora_texto, frecuencia in pendientes:
        if frecuencia != "unica":
            job = scheduler.get_job(str(id_r))
            if job and job.next_run_time:
                fecha_mostrar = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_mostrar = fecha_hora_texto
        else:
            fecha_mostrar = fecha_hora_texto

        lineas.append(f"{id_r}. {texto} — {fecha_mostrar} ({frecuencia})")

    await update.message.reply_text("\n".join(lineas))


# ---------- Envío del aviso ----------

async def enviar_aviso(chat_id, texto, id_recordatorio, frecuencia):
    await bot_instance.send_message(chat_id=chat_id, text=f"⏰ Recordatorio: {texto}")

    if frecuencia == "unica":
        marcar_enviado(id_recordatorio)



# ---------- Programar en el scheduler según la frecuencia ----------

def programar_job(id_recordatorio, chat_id, texto, fecha_hora, frecuencia):
    args = [chat_id, texto, id_recordatorio, frecuencia]

    if frecuencia == "unica":
        scheduler.add_job(
            enviar_aviso, "date", run_date=fecha_hora, args=args, id=str(id_recordatorio)
        )

    elif frecuencia == "semanal":
        scheduler.add_job(
            enviar_aviso,
            IntervalTrigger(weeks=1, start_date=fecha_hora),
            args=args,
            id=str(id_recordatorio)
        )

    elif frecuencia == "mensual":
        scheduler.add_job(
            enviar_aviso,
            CronTrigger(day=fecha_hora.day, hour=fecha_hora.hour, minute=fecha_hora.minute),
            args=args,
            id=str(id_recordatorio)
        )

    elif frecuencia == "diario":
        scheduler.add_job(
            enviar_aviso,
            IntervalTrigger(days=1, start_date=fecha_hora),
            args=args,
            id=str(id_recordatorio)
        )


# ---------- /cancelar ----------

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Formato: /cancelar id\nEj: /cancelar 3")
        return

    id_texto = context.args[0]

    if not id_texto.isdigit():
        await update.message.reply_text("El id debe ser un número. Usa /recordatorios para ver los ids.")
        return

    id_recordatorio = int(id_texto)
    filas_afectadas = cancelar_recordatorio(id_recordatorio)

    if filas_afectadas == 0:
        await update.message.reply_text("No encontré ese recordatorio (¿ya fue cancelado o enviado?).")
        return

    try:
        scheduler.remove_job(str(id_recordatorio))
    except Exception:
        pass

    await update.message.reply_text(f"Recordatorio {id_recordatorio} cancelado.")

# ---------- /actualizar ----------

async def editar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1 or not context.args[0].isdigit():
        await update.message.reply_text("Formato: /editar id\nEj: /editar 5")
        return ConversationHandler.END

    id_recordatorio = int(context.args[0])
    recordatorio = obtener_recordatorio_por_id(id_recordatorio)

    if recordatorio is None:
        await update.message.reply_text("No encontré ese recordatorio (¿ya fue enviado o cancelado?).")
        return ConversationHandler.END

    chat_id_dueño = recordatorio[0]
    if chat_id_dueño != update.effective_chat.id:

        await update.message.reply_text("Ese recordatorio no existe.")
        return ConversationHandler.END

    context.user_data["editando_id"] = id_recordatorio

    await update.message.reply_text("Editando recordatorio. ¿Cuál es el nuevo texto?")
    return ESPERANDO_TEXTO


# ---------- Recarga al iniciar el bot ----------

async def cargar_recordatorios_pendientes():
    pendientes = obtener_pendientes()
    ahora = datetime.now()

    for id_recordatorio, chat_id, texto, fecha_hora_texto, frecuencia in pendientes:
        fecha_hora = datetime.strptime(fecha_hora_texto, "%Y-%m-%d %H:%M:%S")

        if frecuencia != "unica" or fecha_hora > ahora:

            programar_job(id_recordatorio, chat_id, texto, fecha_hora, frecuencia)
        else:
            await enviar_aviso(chat_id, texto, id_recordatorio, frecuencia)


async def iniciar_scheduler(application):
    scheduler.start()
    await cargar_recordatorios_pendientes()


# ---------- Arranque ----------

crear_tabla()
migrar_frecuencia()
scheduler = AsyncIOScheduler()

app = Application.builder().token(token).post_init(iniciar_scheduler).build()

conversacion_recordar = ConversationHandler(
    entry_points=[CommandHandler("recordar", recordar_inicio)],
    states={
        ESPERANDO_TEXTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_texto)],
        ESPERANDO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha)],
        ESPERANDO_FRECUENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_frecuencia)],
    },
    fallbacks=[CommandHandler("cancelar_recordar", cancelar_conversacion)],
)

conversacion_editar = ConversationHandler(
    entry_points=[CommandHandler("editar", editar_inicio)],
    states={
        ESPERANDO_TEXTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_texto)],
        ESPERANDO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha)],
        ESPERANDO_FRECUENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_frecuencia)],
    },
    fallbacks=[CommandHandler("cancelar_recordar", cancelar_conversacion)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", ayuda))
app.add_handler(conversacion_recordar)
app.add_handler(conversacion_editar)
app.add_handler(CommandHandler("recordatorios", recordatorios_lista))
app.add_handler(CommandHandler("cancelar", cancelar))

bot_instance = app.bot

app.run_polling()