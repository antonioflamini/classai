# Avvio del test

## VIA RAPIDA (consigliata, circa 10 minuti)
1. Installa una volta sola: Python (python.org), Git e GitHub CLI. Su Windows: `winget install Python.Python.3.12 Git.Git GitHub.cli`; su Mac: `brew install git gh`.
2. Prepara in anticipo: il token del bot Telegram (@BotFather → /newbot) e la chiave AI (aistudio.google.com → Get API key). Sono facoltativi: senza, l'app funziona con meno funzioni.
3. Decomprimi lo zip, apri un terminale dentro la cartella `classai-monitor` e scrivi `python avvia.py`.
4. Lo script apre il browser per l'accesso a GitHub (tu confermi il codice), ti chiede nome e dati, crea il repository, attiva Pages, imposta i segreti e lancia il primo controllo. Alla fine stampa il link dell'app.
5. Poi vai al punto E qui sotto (prova sul telefono).

## VIA MANUALE (se lo script non funziona), circa 40 minuti

## A. Prepara 3 account gratuiti
1. **GitHub**: github.com → Sign up.
2. **Telegram**: se non lo hai, installalo. Apri @BotFather → `/newbot` → scegli nome → copia il **token**. Poi scrivi "ciao" al tuo bot e apri nel browser `https://api.telegram.org/bot<TOKEN>/getUpdates`: copia il numero in `"chat":{"id":...}`.
3. **Chiave AI**: aistudio.google.com → accedi con Google → "Get API key" → copia la chiave. Controlla in AI Studio il nome del modello gratuito attuale (es. `gemini-2.5-flash`): se è diverso, scrivilo in `config.json` → `ai.model`.

## B. Carica il progetto
4. Su GitHub: "+" → New repository → nome `classai` → **Public** → Create.
5. Decomprimi lo zip. Nel repository: Add file → Upload files → trascina **il contenuto** della cartella `classai-monitor` (cartelle `docs`, `tools`, `state`, file `config.json`, ecc.) → Commit.
6. La cartella nascosta `.github` può non venire caricata. Verifica: se nel repo non vedi `.github/workflows`, crea i due file a mano: Add file → Create new file → nome `.github/workflows/monitor.yml` → incolla il contenuto del file omonimo dello zip → Commit. Ripeti per `digest.yml`.

## C. Imposta
7. Nel repo apri `config.json` → matita: scrivi il tuo nome in `owner`; in `repo` scrivi `tuonomeutente/classai`; in `contact.whatsapp` il tuo numero con prefisso, senza + (es. 393331234567). Commit.
8. Settings → Pages → Source "Deploy from a branch" → Branch `main`, cartella `/docs` → Save. Dopo 1-2 minuti compare il link `https://TUONOME.github.io/classai/`.
9. Settings → Secrets and variables → Actions → New repository secret: `TG_TOKEN`, `TG_CHAT`, `AI_API_KEY` (3 segreti).

## D. Fai partire i controlli
10. Tab Actions → (se chiede) "I understand my workflows, enable them". Scegli **ClassAI monitor** → Run workflow. Attendi 3-10 minuti.
11. Se è verde ✅: apri `docs/data/apicio.json`. Controlla: `"pages"` > 0, gli `items` ci sono; alcuni hanno `"sunto"` e `"status": "ok"` (allegato letto). Se vedi solo `"status": "titolo"`, gli allegati non si scaricano: dimmelo.
12. Poi lancia **ClassAI promemoria** → Run workflow. Dovresti ricevere messaggi su Telegram.
13. Se è rosso ❌: apri il run → clicca sul passaggio rosso → copia le ultime righe e mandamele.

## E. Prova sul telefono
14. Apri il link Pages sul telefono → aggiungilo alla Home (iPhone: Condividi → Aggiungi a Home; Android: menu ⋮ → Installa app).
15. Primo accesso: nome; ruolo; Secondaria di II grado; scuola "IIS Apicio Colonna Gatti"; classe **3AS**; indirizzo **Operatore socio sanitario**; altri nomi "3 A SS"; data **15/10/2026** → Salva e inizia.
16. Verifica: "Per te" mostra le circolari delle famiglie (non quelle solo docenti/ATA e non quelle di altre classi); tab "Calendario" mostra eventi e scadenze; "Prepara messaggio" su una scheda con "🤖✓ sunto verificato" crea la bozza con "In breve".
17. Calendario: tab Calendario → "Iscriviti al calendario". Notifiche: installa l'app **ntfy** → "+" → inserisci il nome del canale mostrato nel tab.
18. Voce: tocca "Parla" e dì "novità", "calendario", "riassumi", "prepara il messaggio".

## F. Cosa mandarmi dopo 2-3 giorni
- Il file `docs/data/apicio.json` (contiene i testi letti e i sunti).
- 3-5 casi in cui il sunto o il filtro sbaglia (usa il pulsante ⚠ Segnala errore).
- Se qualche passaggio sopra non ha funzionato: lo screenshot o il log.
