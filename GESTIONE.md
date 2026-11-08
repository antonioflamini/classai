# Gestione di ClassAI (leggere se sei tu a prenderlo in carico)
**Chi ha le chiavi:** il repository GitHub e i segreti Telegram (`TG_TOKEN`, `TG_CHAT`). Aggiungi come collaboratore almeno un secondo rappresentante, così non dipende da una persona sola (Settings → Collaborators).

**Controlli automatici:** `monitor.yml` legge il sito ogni 4 ore; `digest.yml` manda i promemoria alle 7:30 circa (2 giorni prima, il giorno stesso, riepilogo del lunedì). Per forzarli: tab Actions → workflow → Run workflow.

**Se non arrivano più novità**
1. Actions → ultimo "ClassAI monitor": è rosso? Apri il log e leggi l'errore.
2. `docs/data/<scuola>.json` ha `"errors"` pieno o `"pages": 0`: il sito è cambiato o ci blocca. Scrivi a chi ha costruito ClassAI incollando il log.
3. Se la scuola cambia dominio: aggiorna `url` in `config.json`.

**Aggiungere una scuola o cambiare classe dei promemoria:** modifica `config.json` (voce in `schools`, campo `digest` con `classe`, `indirizzo`, `alias`). I promemoria sono per UNA classe per scuola; per più classi crea più voci con id diversi.

**Segnalazioni:** compila `repo` ("tuonome/nomerepo") in `config.json`: il pulsante "Segnala errore" aprirà una segnalazione su GitHub già compilata. In alternativa `contact.whatsapp` (numero con prefisso, senza +).

**Regole d'oro:** ClassAI prepara, il rappresentante rilegge e invia. Non caricare mai dati riservati nel repository (è pubblico). Rispetta i termini del sito della scuola: il monitor fa 1 richiesta al secondo.
