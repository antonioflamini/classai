# ClassAI Monitor v2 (gratis)
Legge l'intero sito della scuola (pagine + PDF, con OCR per le scansioni), trova le comunicazioni per studenti e famiglie, ti avvisa su Telegram e, nell'app con assistente vocale, prepara la bozza WhatsApp verificata.

## Messa online (circa 15 minuti)
1. Crea un account GitHub e un repository **pubblico**; carica tutti i file di questa cartella (anche `.github`).
2. Apri `config.json` (la scuola di prova è già inserita): scrivi il tuo nome in `owner` (comparirà come "ClassAI by ...") e, per ogni scuola, `id` (senza spazi), `name` e `url` (home del sito). Per altre scuole aggiungi altre voci in `schools`.
3. Settings → Pages → Branch `main`, cartella `/docs`. Il link `https://TUONOME.github.io/REPO/` è quello da dare agli altri rappresentanti.
4. Telegram: @BotFather → /newbot → copia il token; scrivi al tuo bot e apri `https://api.telegram.org/bot<TOKEN>/getUpdates` per leggere `chat.id`. In GitHub: Settings → Secrets → Actions → `TG_TOKEN` e `TG_CHAT`.
5. Actions → "ClassAI monitor" → Run workflow. Il primo giro legge tutto il sito senza notifiche; poi ogni 4 ore avvisa solo sulle novità.

## Primo accesso e prova (3AS, indirizzo Operatore socio sanitario, dal 15/10/2026)
Al primo accesso l'app chiede nome, ruolo, scuola (o "La mia scuola non è in elenco": nome + sito, e prepara la richiesta da inviare a chi gestisce ClassAI), classe, indirizzo, eventuali altri nomi della classe (es. "3 A SS") e la data da cui mostrare le comunicazioni. In `config.json` la scuola di prova (IIS Apicio Colonna Gatti, sito già impostato, adattatore `pvw` per i siti Spaggiari) ha `"since": "2026-10-15"`; in `docs/data` ci sono già le 24 circolari reali lette il 29/10/2026, così l'app mostra subito qualcosa prima del primo controllo automatico. Le impostazioni si riaprono dicendo o scrivendo "impostazioni".

## Per gli altri rappresentanti
Aprono il link, scelgono scuola, classe (es. 3A) e indirizzo, mettono il proprio nome: l'app mostra solo ciò che li riguarda e firma "ClassAI by <tuo nome> · <loro nome>". Scuola non in elenco? Aggiungila in `config.json` (basta il sito).
Installazione: iPhone Safari → Condividi → Aggiungi a Home; Android Chrome → Installa app.

## Voce
Tocca "Parla" e di': novità, scadenze, prossima, riassumi, prepara il messaggio, copia, apri whatsapp, aggiorna, silenzio, aiuto. Funziona su Chrome e Safari; altrove usa la casella di testo. Nota privacy: il riconoscimento vocale è del browser (su Chrome l'audio passa dai server Google).

## Limiti noti
Aree con login (registro elettronico) non leggibili; siti che bloccano i robot (robots.txt) vengono rispettati; l'OCR può sbagliare (l'app lo segnala); le regole non sono IA: controlla sempre il messaggio.

## Novità v3
- **Promemoria Telegram** (`tools/digest.py`, workflow `digest.yml`): 2 giorni prima e il giorno stesso di scadenze/eventi della classe in `config.json` → `digest`, più riepilogo del lunedì. Prova locale: `python tools/digest.py --dry --today 2026-10-28`.
- **Calendario** nell'app: scadenze ⏰ ed eventi 📅 (anche a voce: "calendario").
- **Rettifiche**: collega "Rettifica/Integrazione" alla comunicazione originale e avvisa che è stata aggiornata.
- **Segnala errore** sotto ogni bozza. Vedi `GESTIONE.md` e `GUIDA_COLLEGHI.md`.

## Novità v4: calendario e notifiche per classe
- `digest` in `config.json` può essere una **lista**: una voce per classe (`classe`, `indirizzo`, `alias`). Per ognuna ClassAI genera `docs/cal/<scuola>-<classe>.ics` e un canale **ntfy** (app gratuita, senza account).
- **Calendario che si aggiorna da solo:** nel tab *Calendario* il rappresentante/genitore tocca "Iscriviti" (iPhone/Android) o copia il link in Google Calendar ("Da URL"). Le scadenze hanno anche un avviso il giorno prima.
- **Notifiche:** installa l'app *ntfy* e iscriviti al canale mostrato nel tab Calendario; arrivano le novità della tua classe, i promemoria e il riepilogo del lunedì. I nomi dei canali sono "difficili da indovinare" ma non segreti: contengono solo circolari già pubbliche. Cambia `salt` in `config.json` se vuoi nuovi nomi.
- **Aggiungere una classe:** dal tab Calendario, "Richiedi l'attivazione" prepara la voce da incollare in `config.json`.

## Verifica dell'8/11/2026 (correzioni)
- Windows: gli script ora leggono e scrivono in UTF-8 (prima `digest.py --dry` si bloccava sui caratteri accentati e sulle emoji) e accettano un `config.json` salvato col Blocco note.
- **Limite importante per l'IIS Apicio:** il server Spaggiari (`web.spaggiari.eu`) risponde *403 Forbidden* ai programmi automatici, quindi gli allegati PDF non si scaricano: ClassAI vede numero, titolo, data e destinatari di ogni comunicazione, ma non il testo. L'app lo segnala ("N allegati non scaricabili") e la bozza WhatsApp include il link alla circolare ufficiale. Il blocco è voluto dal sito: va rispettato, non aggirato. Il sunto AI e le scadenze dal testo funzionano solo sulle scuole che pubblicano i PDF in chiaro.
- Bozza: oggetto completo (non più tagliato a 60 caratteri), niente "In breve" duplicato, "a.s." non spezza più le frasi, l'oggetto non sconfina nella riga successiva.
- Prova in locale: `python -m http.server 8790 --directory docs` e apri `http://localhost:8790`.
- **Carica PDF** (sezione "Bozza manuale"): scegli il PDF della circolare, l'app ne estrae il testo sul telefono (pdf.js) e prepara subito la bozza. Le scansioni senza testo vengono segnalate.
- **Circolari non lette**: se ClassAI non riesce a leggere una nuova circolare per famiglie/alunni (allegato bloccato, scansione, testo assente), l'avviso Telegram/ntfy lo dice e contiene il link `…/?carica=<id>`: apre l'app sul caricamento di quella circolare. Basta scaricare il PDF dall'originale e caricarlo: la bozza esce con date, scadenze e il link ufficiale. Nell'app le schede non lette hanno il pulsante "📄 Carica PDF".
- **Caricamento in 2 tocchi**: il link Telegram apre in cima all'app il pannello "① Apri la circolare / ② Carica il PDF scaricato". Ovunque carichi un PDF (pulsante "📄 carica circolare", comando vocale, trascinamento dal computer, **Condividi → ClassAI** su Android con l'app installata) ClassAI riconosce il numero della comunicazione, la collega alla scheda e la ricorda sul telefono ("📄 caricata da te"), così non va ricaricata.
- **Riassunto AI a parte**: sotto la bozza c'è il riquadro "🧠 Riassunto AI", separato dal messaggio (lo inserisci solo se premi "Usa nel messaggio"). Per le circolari lette dal sito mostra il sunto già verificato dal controllo automatico; per PDF caricati o testi incollati lo scrive l'app con una **chiave AI personale** (Impostazioni), che resta solo sul telefono e non viene mai pubblicata. Stessa doppia verifica del server: regole (numeri, date, mesi, classi, scadenze) + secondo controllo AI; se non passa non viene mostrato. A voce: "riassunto AI".
- **Avviso di salute**: ogni mattina, se il controllo del sito non aggiorna i dati da più di 24 ore, non raggiunge il sito o legge 0 pagine, arriva un messaggio Telegram.
- **Orario stabile**: i promemoria arrivano alle 7:30 ora italiana tutto l'anno (il workflow parte alle 5:30 e alle 6:30 UTC, lo script invia una sola volta). Tutti gli orari salvati sono in ora italiana.
- **Modello AI**: `gemini-2.5-flash` viene dismesso il 1/12/2026. Ora il modello è `gemini-3.5-flash-lite`, con riserve `gemini-3.8-flash` e `gemini-2.5-flash-lite` in `ai.fallback`: se un modello sparisce, ClassAI passa al successivo da solo.

## Novità v5: sunto con AI e verifica
- `tools/ai.py` scrive il sunto di ogni circolare con un modello gratuito (Gemini di default; qualsiasi servizio compatibile OpenAI via `ai.provider: "openai"`, `base_url`, `model`) usando il segreto `AI_API_KEY`.
- **Verifica in due livelli prima di pubblicarlo**: (1) regole: ogni numero, data, ora, importo, mese e classe del sunto deve comparire nel testo originale e ogni scadenza del testo deve comparire nel sunto; (2) un secondo passaggio AI confronta sunto e circolare. Se c'è un problema il sunto viene riscritto una volta; se fallisce ancora, **non viene pubblicato** e l'app usa il sunto a regole.
- Se il secondo controllo AI non è raggiungibile ma le regole passano, il sunto è marcato "regole". Senza `AI_API_KEY` tutto continua a funzionare col sunto a regole.
- Il testo delle circolari (pubbliche) viene inviato al servizio AI scelto: non metterci mai dati personali. Guida completa: `AVVIO_TEST.md`.
