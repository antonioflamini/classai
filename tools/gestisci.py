#!/usr/bin/env python3
"""ClassAI – gestione guidata. Uso:  python tools/gestisci.py   (oppure con un comando diretto)
  scuola        aggiunge una scuola (anche incollando la richiesta arrivata dall'app)
  classe        aggiunge una classe (calendario, promemoria, canale ntfy) a una scuola
  telegram      collega un gruppo Telegram al gestore, a una scuola o a una classe
  elenco        mostra scuole, classi e destinatari degli avvisi
  collaboratore invita un altro rappresentante a gestire il repository GitHub
  pacchetto     crea uno zip pulito da dare al rappresentante di un'altra scuola
  pubblica      carica su GitHub le modifiche a config.json"""
import getpass, json, os, re, secrets, shutil, subprocess, sys, urllib.request, urllib.error, zipfile, datetime as dt
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); os.chdir(ROOT)
CFG = "config.json"

def exe(name, win):
    if shutil.which(name): return name
    return win if os.name == "nt" and os.path.exists(win) else name
GIT = exe("git", r"C:\Program Files\Git\cmd\git.exe"); GH = exe("gh", r"C:\Program Files\GitHub CLI\gh.exe")

def load(): return json.load(open(CFG, encoding="utf-8-sig"))
def save(c): json.dump(c, open(CFG, "w", encoding="utf-8"), indent=2, ensure_ascii=False); print("✔ config.json aggiornato")
def ask(p, default=""):
    v = input(p + (f" [{default}]" if default else "") + ": ").strip(); return v or default
def yes(p): return ask(p + " (s/n)", "s").lower().startswith(("s", "y"))
def slug(t): return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:30]
def norm_cls(c): return re.sub(r"[\s^°]", "", c.upper())

def pick(items, label, fmt=str):
    if not items: sys.exit(f"✖ Nessun elemento: {label}")
    for i, x in enumerate(items, 1): print(f"  {i}) {fmt(x)}")
    while True:
        v = ask(f"Scegli {label} (numero)", "1")
        if v.isdigit() and 1 <= int(v) <= len(items): return items[int(v) - 1]

def pick_school(c): return pick(c["schools"], "la scuola", lambda s: f"{s['name']} ({s['id']})")

def profiles(sc):
    d = sc.get("digest") or []
    if isinstance(d, dict): d = [d]
    sc["digest"] = d; return d

# ---------------------------------------------------------------- scuola / classe
def cmd_scuola():
    c = load()
    print("Incolla la richiesta arrivata dall'app (il blocco tra { }) e premi Invio due volte,\noppure premi solo Invio per inserire i dati a mano.")
    lines = []
    while True:
        l = input()
        if not l.strip(): break
        lines.append(l)
    req = {}
    if lines:
        try: req = json.loads(re.search(r"\{.*\}", " ".join(lines), re.S).group(0))
        except Exception: print("  Non riesco a leggere la richiesta: inserisci i dati a mano.")
    name = req.get("name") or ask("Nome della scuola")
    url = (req.get("url") or ask("Sito della scuola (https://…)")).rstrip("/")
    if not re.match(r"^https?://[^\s.]+\.\S+$", url): sys.exit("✖ Indirizzo non valido.")
    sid = slug(req.get("id") or ask("Identificativo breve (senza spazi)", slug(name.split()[-1] if name else "scuola")))
    if any(s["id"] == sid for s in c["schools"]): sys.exit(f"✖ Esiste già una scuola con id «{sid}».")
    since = req.get("since") or ask("Mostra comunicazioni dal (AAAA-MM-GG, Invio = oggi)", dt.date.today().isoformat())
    try:
        html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ClassAI-Monitor/2.0"}), timeout=20).read(400000)
        ad = "pvw" if b"pvw2/" in html else "auto"; print(f"✔ Sito raggiungibile ({'Spaggiari: adattatore pvw' if ad == 'pvw' else 'adattatore automatico'})")
    except Exception as e:
        ad = "auto"; print(f"⚠ Non riesco ad aprire il sito ora ({e}): la aggiungo lo stesso, il controllo riproverà.")
    sc = {"id": sid, "name": name, "url": url, "max_pages": 150, "depth": 3, "since": since, "adapter": ad, "digest": []}
    c["schools"].append(sc); save(c)
    if yes("Vuoi aggiungere subito una classe (promemoria e calendario)?"): add_class(c, sc, req)
    offer_publish(f"Aggiunta scuola {name}")

def add_class(c, sc, pre=None):
    pre = pre or {}
    cls = norm_cls(pre.get("classe") or ask("Classe (es. 3AS)"))
    if not re.match(r"^[1-5][A-Z]{0,3}$", cls): sys.exit("✖ Classe non valida (es. 3AS).")
    if any(norm_cls(p["classe"]) == cls for p in profiles(sc)): sys.exit(f"✖ La classe {cls} c'è già per {sc['name']}.")
    ind = pre["indirizzo"] if "indirizzo" in pre else ask("Indirizzo (es. Operatore socio sanitario, Invio se nessuno)")
    al = pre["alias"] if isinstance(pre.get("alias"), list) else [a.strip() for a in ask("Altri modi in cui la scuola la nomina (separati da virgola)").split(",") if a.strip()]
    profiles(sc).append({"classe": cls, "indirizzo": ind, "alias": al}); save(c)
    print(f"✔ Classe {cls} aggiunta: dal prossimo controllo avrà calendario, promemoria e canale ntfy.")

def cmd_classe():
    c = load(); sc = pick_school(c)
    print("Incolla la richiesta di attivazione arrivata dall'app ({\"classe\":…}) e Invio, oppure solo Invio per inserire a mano.")
    l = input().strip(); pre = {}
    if l:
        try: pre = json.loads(re.search(r"\{.*\}", l).group(0))
        except Exception: print("  Richiesta non leggibile: inserisci a mano.")
    add_class(c, sc, pre); offer_publish(f"Aggiunta classe a {sc['name']}")

# ---------------------------------------------------------------- telegram
def tg_api(tok, method, data=None):
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/{method}", json.dumps(data).encode() if data else None, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=20))["result"]

def cmd_telegram():
    c = load()
    print("A chi vuoi far arrivare gli avvisi?")
    who = pick(["gestore (tutti gli avvisi, anche quelli di salute)", "una scuola (tutte le novità di quella scuola)", "una classe (novità e promemoria solo di quella classe)"], "il destinatario")
    print("\nPrima, su Telegram:\n  1. crea un gruppo con i rappresentanti (o usa la chat privata col bot, solo per il gestore)\n  2. aggiungi il bot al gruppo\n  3. scrivi nel gruppo: /start\n")
    tok = getpass.getpass("Incolla il token del bot (non si vede mentre incolli) e premi Invio: ").strip()
    try: me = tg_api(tok, "getMe")
    except Exception: sys.exit("✖ Token non valido: ricopialo da @BotFather.")
    chats = {}
    for _ in range(3):
        for u in tg_api(tok, "getUpdates"):
            for k in ("message", "my_chat_member", "channel_post", "edited_message"):
                ch = (u.get(k) or {}).get("chat")
                if ch: chats[ch["id"]] = ch.get("title") or ("chat privata con " + (ch.get("first_name") or "te"))
        if chats: break
        input(f"Non vedo chat: aggiungi @{me['username']} al gruppo, scrivi /start e premi Invio qui… ")
    if not chats: sys.exit("✖ Nessuna chat trovata. Riprova dopo aver scritto /start nel gruppo.")
    cid, title = pick(list(chats.items()), "la chat", lambda x: f"{x[1]}  (id {x[0]})")
    try: tg_api(tok, "sendMessage", {"chat_id": cid, "text": f"✅ ClassAI collegato: qui arriveranno gli avvisi per {who.split(' (')[0]}."})
    except urllib.error.HTTPError as e: sys.exit(f"✖ Il bot non riesce a scrivere in «{title}» ({e.code}): è ancora nel gruppo?")
    print(f"✔ Messaggio di prova inviato in «{title}».")
    if who.startswith("gestore"):
        repo = c.get("repo") or ask("Repository (utente/nome)")
        for n, v in (("TG_TOKEN", tok), ("TG_CHAT", str(cid))):
            r = subprocess.run([GH, "secret", "set", n, "-R", repo], input=v, text=True, capture_output=True)
            if r.returncode: sys.exit(f"✖ Non riesco a salvare {n}: {r.stderr.strip()}")
        print("✔ Segreti del gestore aggiornati su GitHub."); return
    sc = pick_school(c); target = sc
    if who.startswith("una classe"):
        ps = profiles(sc)
        if not ps: sys.exit("✖ Questa scuola non ha classi: aggiungine una con «python tools/gestisci.py classe».")
        target = pick(ps, "la classe", lambda p: f"{p['classe']} {p.get('indirizzo', '')}")
    target["tg_chat"] = str(cid)
    link = ask("Link di invito al gruppo (Telegram → info gruppo → Invita tramite link; Invio per saltare)")
    if link:
        if re.match(r"^https://t\.me/\S+$", link): target["tg_link"] = link
        else: print("  Link ignorato: deve iniziare con https://t.me/")
    save(c)
    if c.get("admin_copy", True): print("ℹ Tu (gestore) continuerai a ricevere una copia di tutto. Per non riceverla: in config.json metti \"admin_copy\": false")
    offer_publish(f"Gruppo Telegram per {target.get('classe', sc['name'])}")

# ---------------------------------------------------------------- altro
def cmd_elenco():
    c = load(); a = "una copia" if c.get("admin_copy", True) else "solo salute e scuole senza gruppo"
    print(f"Gestore: {c.get('owner', '')} · repo {c.get('repo', '')} · il gestore riceve {a}")
    for s in c["schools"]:
        print(f"\n🏫 {s['name']} ({s['id']}) – {s['url']} · dal {s.get('since', '-')}" + (f" · gruppo {s['tg_chat']}" if s.get("tg_chat") else ""))
        for p in profiles(s): print(f"   • {p['classe']} {p.get('indirizzo', '')}" + (f" · gruppo {p['tg_chat']}" if p.get("tg_chat") else " · avvisi al gestore") + (" · link invito ✔" if p.get("tg_link") else ""))

def cmd_collaboratore():
    c = load(); repo = c.get("repo") or ask("Repository (utente/nome)")
    u = ask("Nome utente GitHub del rappresentante da invitare").lstrip("@")
    if not u: return
    if not yes(f"Invio a {u} l'invito a gestire {repo} (potrà modificare tutto il progetto)?"): return
    r = subprocess.run([GH, "api", "-X", "PUT", f"repos/{repo}/collaborators/{u}", "-f", "permission=push"], text=True, capture_output=True)
    print("✔ Invito inviato: deve accettarlo dalla mail o da github.com/notifications." if not r.returncode else f"✖ {r.stderr.strip()}")

def cmd_pacchetto():
    c = load(); out = os.path.join(ROOT, f"classai-per-altra-scuola-{dt.date.today():%Y%m%d}.zip")
    skip_dirs = {".git", "__pycache__", ".claude"}
    tmpl = {"owner": "", "schools": [], "contact": {"whatsapp": ""}, "repo": "", "salt": secrets.token_hex(4), "ai": c.get("ai", {})}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for d, ds, fs in os.walk(ROOT):
            ds[:] = [x for x in ds if x not in skip_dirs]
            for f in fs:
                p = os.path.join(d, f); rel = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel.endswith(".zip") or rel == CFG or rel.startswith(("state/", "docs/cal/", "docs/data/")): continue
                z.write(p, "classai-monitor/" + rel)
        z.writestr("classai-monitor/config.json", json.dumps(tmpl, indent=2, ensure_ascii=False))
        z.writestr("classai-monitor/state/.gitkeep", ""); z.writestr("classai-monitor/docs/cal/.gitkeep", "")
        z.writestr("classai-monitor/docs/data/schools.json", json.dumps({"owner": "", "schools": []}))
        z.writestr("classai-monitor/docs/data/profiles.json", "{}")
    print(f"✔ Creato {out}\n  Contiene il programma senza i tuoi dati (niente numero, repo, chat, circolari).\n  Il collega lo decomprime e lancia «python avvia.py»: gli chiederà la sua scuola e classe.")

def cmd_pubblica(msg="Aggiornamento configurazione"):
    for a in (["add", "config.json"], ["-c", "user.name=classai", "-c", "user.email=bot@users.noreply.github.com", "commit", "-q", "-m", msg], ["pull", "-q", "--rebase", "--autostash"], ["push", "-q"]):
        r = subprocess.run([GIT] + a, text=True, capture_output=True)
        if r.returncode and "nothing to commit" not in (r.stdout + r.stderr): sys.exit(f"✖ git {a[0] if a[0] != '-c' else 'commit'}: {(r.stderr or r.stdout).strip()}")
    print("✔ Pubblicato su GitHub: vale dal prossimo controllo (o lancia Actions → ClassAI monitor → Run workflow).")

def offer_publish(msg):
    if os.path.isdir(".git") and yes("Pubblico subito su GitHub?"): cmd_pubblica(msg)

CMDS = {"scuola": cmd_scuola, "classe": cmd_classe, "telegram": cmd_telegram, "elenco": cmd_elenco,
        "collaboratore": cmd_collaboratore, "pacchetto": cmd_pacchetto, "pubblica": cmd_pubblica}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in CMDS:
        print(__doc__.split("Uso:")[0].strip() + "\n")
        desc = dict(re.findall(r"^  (\w+)\s+(.*)$", __doc__, re.M))
        cmd = pick(list(CMDS), "cosa fare", lambda k: k.ljust(14) + desc.get(k, ""))
    try: CMDS[cmd]()
    except (KeyboardInterrupt, EOFError): print("\nAnnullato.")
