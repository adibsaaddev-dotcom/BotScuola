
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Nome del file di database locale
FILE_COMPITI = "compiti.txt"

# Giorni in cui hai allenamento: Lunedì(0), Martedì(1), Giovedì(3)
GIORNI_ALLENAMENTO = {0, 1, 3} 

def leggi_compiti():
    """Legge i compiti dal file di testo locale."""
    if not os.path.exists(FILE_COMPITI):
        return []
    
    compiti = []
    with open(FILE_COMPITI, "r", encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga:
                # Formato: TIPO | DATA (GG/MM/AAAA) | DESCRIZIONE
                parti = riga.split(" | ")
                if len(parti) >= 3:
                    compiti.append({
                        "tipo": parti[0].strip().upper(),
                        "data_str": parti[1].strip(),
                        "descrizione": parti[2].strip()
                    })
    return compiti

def scrivi_compito(tipo, data_str, descrizione):
    """Aggiunge un compito al file di testo."""
    with open(FILE_COMPITI, "a", encoding="utf-8") as f:
        f.write(f"{tipo} | {data_str} | {descrizione}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = (
        "🤖 **Ciao Adib! Sono il tuo Assistente Scolastico Personale.**\n\n"
        "Comandi:\n"
        "• `/aggiungi [normale/verifica/interrogazione] [GG/MM/AAAA] [descrizione]`\n"
        "• `/Pianifica` - Genera la tua giornata tipo ed esegue i controlli intelligenti"
    )
    await update.message.reply_text(testo, parse_mode="Markdown")

async def aggiungi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ Uso: `/aggiungi verifica 20/11/2026 Matematica pag 45`")
        return
    
    tipo = args[0].upper()
    data_str = args[1]
    descrizione = " ".join(args[2:])
    
    try:
        datetime.strptime(data_str, "%d/%m/%Y")
    except ValueError:
        await update.message.reply_text("❌ Formato data errato! Usa GG/MM/AAAA.")
        return

    scrivi_compito(tipo, data_str, descrizione)
    await update.message.reply_text(f"✅ Registrato: **{tipo}** il {data_str} ({descrizione})", parse_mode="Markdown")

async def pianifica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    compiti = leggi_compiti()
    oggi_dt = datetime.now()
    oggi_date = oggi_dt.date()
    
    # Mappatura rientri e allenamenti
    # 0=Lun, 1=Mar, 2=Mer, 3=Gio, 4=Ven, 5=Sab, 6=Dom
    orari_settimana = {
        0: {"ritorno": 15.0, "allenamento": True},
        1: {"ritorno": 14.0, "allenamento": True},
        2: {"ritorno": 14.0, "allenamento": False},
        3: {"ritorno": 14.0, "allenamento": True},
        4: {"ritorno": 13.0, "allenamento": False},
        5: {"ritorno": 14.0, "allenamento": False},
        6: {"ritorno": 0.0, "allenamento": False}
    }
    
    oggi_info = orari_settimana[oggi_dt.weekday()]
    
    risposta = f"📅 **PIANO OPERATIVO PER OGGI**\n"
    risposta += "-----------------------------------\n"
    
    if oggi_info['ritorno'] == 0.0:
        risposta += "🛋️ Domenica: Mattinata di studio leggero, pomeriggio libero!\n"
    else:
        # Buffer di 1 ora per relax post-scuola
        inizio_studio = oggi_info['ritorno'] + 1.0
        risposta += f"🏫 Rientro scuola: {int(oggi_info['ritorno'])}:00 -> Relax fino alle {int(inizio_studio)}:00\n"
        
        if oggi_info['allenamento']:
            risposta += "⚽ **Allenamento (18:30 - 20:30):** Finisci i compiti veloci prima!\n"
            fine_studio = 18.0
        else:
            risposta += "📚 **Pomeriggio studio:** Sessioni Pomodoro attive.\n"
            fine_studio = 19.30
            
        durata_disponibile = fine_studio - inizio_studio
        sessioni_stimates = max(1, int(durata_disponibile / 0.5))
        risposta += f"⏱️ *Metodo Pomodoro:* Hai circa {durata_disponibile:.1f} ore utili. Pianificate circa {sessioni_stimates} sessioni da 30 min (con pause da 5 e 10 min).\n"

    risposta += "\n🚨 **MONITORAGGIO SCADENZE ED ALLARMI:**\n"
    allarmi = []
    
    if not compiti:
        risposta += "Nessun compito in lista.\n"
    else:
        for c in compiti:
            data_c = datetime.strptime(c["data_str"], "%d/%m/%Y").date()
            diff_giorni = (data_c - oggi_date).days
            
            if 0 <= diff_giorni <= 5 and c["tipo"] in ["VERIFICA", "INTERROGAZIONE"]:
                allarmi.append(f"⚠️ **ATTENZIONE:** Tra {diff_giorni} giorni c'è la {c['tipo'].lower()} di *{c['descrizione']}*.")
                
            giorno_prima = data_c - timedelta(days=1)
            if oggi_date == giorno_prima and giorno_prima.weekday() in GIORNI_ALLENAMENTO and c["tipo"] in ["VERIFICA", "INTERROGAZIONE"]:
                allarmi.append(f"🚨 **ALLARME ROSSO:** Domani hai la {c['tipo'].lower()} (*{c['descrizione']}*) e oggi hai allenamento! Valuta di saltarlo per avere il pomeriggio libero.")

    if allarmi:
        risposta += "\n".join(allarmi)
    else:
        risposta += "Tutto sotto controllo, nessun allarme critico per oggi.\n"
        
    await update.message.reply_text(risposta, parse_mode="Markdown")

def main():
    TOKEN = "9098508549:AAHDXSDBf4mThuSZ7bAVwsyaHF-YrD2cK_0"
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("aggiungi", aggiungi))
    application.add_handler(CommandHandler("Pianifica", pianifica))
    
    print("🤖 Pianificatore totale avviato su Lenovo...")
    application.run_polling()

if __name__ == "__main__":
    main()


