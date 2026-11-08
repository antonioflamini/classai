#!/usr/bin/env python3
"""Collega Telegram a ClassAI: trova l'ID della tua chat col bot e salva TG_TOKEN e TG_CHAT come segreti GitHub.
Uso: python tools/telegram_setup.py   (prima scrivi "ciao" al tuo bot su Telegram)"""
import getpass, json, os, subprocess, sys, urllib.request, urllib.error
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
GH = "gh"
if os.name == "nt" and os.path.exists(r"C:\Program Files\GitHub CLI\gh.exe"): GH = r"C:\Program Files\GitHub CLI\gh.exe"

cfg = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config.json"), encoding="utf-8-sig"))
repo = cfg.get("repo") or input("Repository (utente/nome): ").strip()
print("1) Su Telegram scrivi 'ciao' al tuo bot (quello creato con @BotFather).")
tok = getpass.getpass("2) Incolla il token INTERO del bot (es. 123456789:AA...; non si vede mentre incolli) e premi Invio: ").strip()
if ":" not in tok or not tok.split(":")[0].isdigit():
    sys.exit("✖ Il token non sembra completo: deve iniziare con numeri, poi ':' e il resto. Ricopialo da BotFather.")
try:
    me = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getMe", timeout=20))["result"]
    print(f"✔ Token valido: bot @{me['username']}")
except urllib.error.HTTPError as e:
    sys.exit(f"✖ Telegram rifiuta il token (errore {e.code}). Ricopialo da BotFather (o usa /token).")
chat = ""
for _ in range(3):
    j = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getUpdates", timeout=20))
    msgs = [u.get("message") or u.get("my_chat_member") for u in j.get("result", [])]
    ids = [m["chat"]["id"] for m in msgs if m and "chat" in m]
    if ids: chat = str(ids[-1]); break
    input(f"   Non vedo messaggi: scrivi 'ciao' a @{me['username']} su Telegram e premi Invio qui… ")
if not chat: sys.exit("✖ Nessun messaggio trovato. Scrivi 'ciao' al bot e rilancia lo script.")
for name, val in (("TG_TOKEN", tok), ("TG_CHAT", chat)):
    r = subprocess.run([GH, "secret", "set", name, "-R", repo], input=val, text=True, capture_output=True)
    if r.returncode: sys.exit(f"✖ Non riesco a salvare {name}: {r.stderr.strip()}")
req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",
                             json.dumps({"chat_id": chat, "text": "✅ ClassAI è collegato: qui riceverai novità, promemoria e avvisi."}).encode(),
                             {"Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=20)
print(f"✔ Segreti TG_TOKEN e TG_CHAT salvati su {repo}. Controlla Telegram: dovresti aver ricevuto un messaggio di prova.")
