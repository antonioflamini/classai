# Gestione di ClassAI (leggere se sei tu a prenderlo in carico)
**Chi ha le chiavi:** il repository GitHub e i segreti Telegram (`TG_TOKEN`, `TG_CHAT`). Aggiungi come collaboratore almeno un secondo rappresentante, così non dipende da una persona sola (Settings → Collaborators).

## Gestione guidata: `python tools/gestisci.py`
Apre un menu (oppure scrivi direttamente il comando, es. `python tools/gestisci.py classe`). Ogni modifica può essere pubblicata subito su GitHub.

| Situazione | Comando |
|---|---|
| Un rappresentante di **un'altra scuola** ti manda la richiesta dall'app ("La mia scuola non è in elenco") | `scuola` → incolli la richiesta: scuola e classe vengono aggiunte |
| Una **nuova classe** chiede calendario e promemoria (tab Calendario → "Richiedi l'attivazione") | `classe` → incolli la richiesta |
| **Due rappresentanti della stessa classe** vogliono gli avvisi Telegram | crea un gruppo con loro + il bot, scrivi `/start` nel gruppo → `telegram` → "una classe" |
| Una scuola vuole **il suo gruppo** con tutte le novità | `telegram` → "una scuola" |
| Cambi bot o token (es. dopo `/revoke`) | `telegram` → "gestore" |
| Vuoi un **secondo gestore** che possa sostituirti | `collaboratore` → nome utente GitHub (riceve un invito) |
| Un collega vuole **una copia tutta sua** (suo GitHub, suo bot) | `pacchetto` → crea uno zip senza i tuoi dati; lui lancia `python avvia.py` |
| Vedere chi riceve cosa | `elenco` |

**Chi riceve gli avvisi Telegram**
- **Gestore** (chat `TG_CHAT`): avvisi di salute, errori del sito e una copia di tutto. Per non ricevere più la copia delle novità e dei promemoria delle classi che hanno un gruppo: in `config.json` aggiungi `"admin_copy": false`.
- **Gruppo della scuola** (`tg_chat` nella scuola): tutte le novità per famiglie/alunni di quella scuola e i promemoria delle classi senza gruppo proprio.
- **Gruppo della classe** (`tg_chat` nella classe): solo le novità che riguardano quella classe e i suoi promemoria/riepilogo del lunedì.
- Un solo bot va bene per tutti i gruppi. Se una chat diventa "supergruppo" Telegram cambia il suo ID: il log del monitor lo segnala, rifai `telegram` per quella classe.
- Il link d'invito al gruppo (facoltativo) compare nell'app, tab Calendario: "💬 Entra nel gruppo Telegram della classe".

**Due rappresentanti della stessa classe, senza Telegram**: aprono lo stesso link, mettono ciascuno il proprio nome (firma "ClassAI by … · nome"), si iscrivono allo stesso calendario e canale ntfy. I PDF caricati restano sul telefono di chi li carica.

**Cambiare il bot Telegram o il token** (es. dopo `/revoke` in BotFather): scrivi "ciao" al bot, poi nella cartella del progetto `python tools/telegram_setup.py` e incolla il token nuovo: aggiorna da solo i segreti su GitHub e manda un messaggio di prova.

**Controlli automatici:** `monitor.yml` legge il sito ogni 4 ore; `digest.yml` manda i promemoria alle 7:30 circa (2 giorni prima, il giorno stesso, riepilogo del lunedì). Per forzarli: tab Actions → workflow → Run workflow.

**Se non arrivano più novità**
1. Actions → ultimo "ClassAI monitor": è rosso? Apri il log e leggi l'errore.
2. `docs/data/<scuola>.json` ha `"errors"` pieno o `"pages": 0`: il sito è cambiato o ci blocca. Scrivi a chi ha costruito ClassAI incollando il log.
3. Se la scuola cambia dominio: aggiorna `url` in `config.json`.

**Aggiungere una scuola o cambiare classe dei promemoria:** modifica `config.json` (voce in `schools`, campo `digest` con `classe`, `indirizzo`, `alias`). I promemoria sono per UNA classe per scuola; per più classi crea più voci con id diversi.

**Segnalazioni:** compila `repo` ("tuonome/nomerepo") in `config.json`: il pulsante "Segnala errore" aprirà una segnalazione su GitHub già compilata. In alternativa `contact.whatsapp` (numero con prefisso, senza +).

**Regole d'oro:** ClassAI prepara, il rappresentante rilegge e invia. Non caricare mai dati riservati nel repository (è pubblico). Rispetta i termini del sito della scuola: il monitor fa 1 richiesta al secondo.
