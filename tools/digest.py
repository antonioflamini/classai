#!/usr/bin/env python3
"""Promemoria (Telegram + ntfy per classe), calendario .ics per classe e riepilogo del lunedì.
Uso: python tools/digest.py [--dry] [--ics-only] [--today AAAA-MM-GG]"""
import json, os, re, sys, hashlib, datetime as dt, urllib.parse, urllib.request, urllib.error
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")   # Windows: emoji nei log senza errori
    except Exception: pass
MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
GG = "lun mar mer gio ven sab dom".split()
ANN = {"1": "prim[ae]", "2": "second[ae]", "3": "terz[ae]", "4": "quart[ae]", "5": "quint[ae]"}
GEN = ("oper", "tecn", "indi", "serv", "scuo", "corso")
STAFF = re.compile(r"collegio (dei )?docenti|personale ata|interpell|ordine di servizio|graduatori|supplenz|dipartiment", re.I)

def find_dates(text, today):
    t = re.sub(r"\b(Prot\.|Circolare)\s*n?[°.]?\s*[\w/.\-]+(\s+del\s+[\d/.]+)?", "", text, flags=re.I)
    raw = [(int(m[1]), MESI.index(m[2].lower()) + 1, int(m[3]) if m[3] else None, m.start())
           for m in re.finditer(r"(\d{1,2})\s*°?\s*(" + "|".join(MESI) + r")(?:\s+(\d{4}))?", t, re.I)]
    raw += [(int(m[1]), int(m[2]), int(m[3]) + (2000 if int(m[3]) < 100 else 0), m.start()) for m in re.finditer(r"(\d{1,2})[/.](\d{1,2})[/.](\d{2,4})", t)]
    out = []
    for d, mo, y, pos in raw:
        try:
            x = dt.date(y or today.year, mo, d)
            if y is None and x < today - dt.timedelta(days=30): x = dt.date(today.year + 1, mo, d)
        except ValueError: continue
        out.append((x, bool(re.search(r"entro|non oltre|scadenza|improrogabil|termine", re.split(r"[.;]\s", t[max(0, pos - 45):pos])[-1], re.I))))
    return out

def stems(x): return {w[:4] for w in re.sub(r"[^a-zà-ú\s]", " ", (x or "").lower()).split() if len(w) > 3 and w[:4] not in GEN}

def relevant(it, prof):
    tip = it.get("tip")
    if tip and not any(re.search(r"famigli|alunni", x, re.I) for x in tip): return False
    t = " ".join((it.get("text") or "").split())
    if not tip and STAFF.search(t) and not re.search(r"genitor|famigli|student|alunn", t, re.I): return False
    m = re.match(r"^([1-5])([A-Z]{1,3})?$", re.sub(r"[\s^°]", "", prof.get("classe", "").upper()))
    ok = True
    if m and re.search(r"class[ei]\s+(?:prim[ae]|second[ae]|terz[ae]|quart[ae]|quint[ae]|[1-5]\s?[A-Za-z]?\^?)", t, re.I):
        y, L = m[1], m[2] or ""
        hit = any(a.lower() in t.lower() for a in prof.get("alias", []) if len(a) > 2)
        for mm in re.finditer(r"class[ei]?[^.]{0,40}\b" + ANN[y] + r"\b", t, re.I):
            if not re.match(r"\s+[A-Z]\b", t[mm.end():]): hit = True; break
        if not hit and L: hit = bool(re.search(r"(?<![A-Za-z0-9])" + y + r"\s?\^?°?\s?" + L + r"(?![A-Za-z0-9])", t, re.I))
        if not hit and not L: hit = bool(re.search(r"class[ei]?[^.]{0,40}(?<![0-9])" + y + r"(?![0-9])", t, re.I))
        ok = hit
    mi = re.search(r"indirizzo\s+([A-ZÀ-Ú][\wÀ-ú'’-]+(?:\s+[\wÀ-ú'’-]+){0,7})", t)
    if ok and prof.get("indirizzo") and mi and stems(prof["indirizzo"]) and not (stems(mi[1]) & stems(prof["indirizzo"])): ok = False
    return ok

def tg(msg, chat=None):
    """Invia a una chat Telegram; senza `chat` va al gestore (segreto TG_CHAT)."""
    tok, chat = os.getenv("TG_TOKEN"), str(chat or os.getenv("TG_CHAT") or "")
    if not (tok and chat): return
    for _ in range(2):
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", urllib.parse.urlencode({"chat_id": chat, "text": msg[:4000], "disable_web_page_preview": "true"}).encode(), timeout=20); return
        except urllib.error.HTTPError as e:
            try: new = json.loads(e.read()).get("parameters", {}).get("migrate_to_chat_id")
            except Exception: new = None
            if new:   # il gruppo è diventato "supergruppo": Telegram cambia l'ID
                print(f"telegram: la chat {chat} ora è {new}: aggiorna tg_chat in config.json (python tools/gestisci.py telegram)"); chat = str(new); continue
            print("telegram:", chat, e); return
        except Exception as e: print("telegram:", chat, e); return

def tg_route(msg, chats, cfg):
    """Invia ai gruppi indicati (scuola/classe); il gestore riceve una copia se admin_copy è attivo
    (predefinito) oppure se non c'è nessun gruppo configurato. Ogni chat riceve il messaggio una volta sola."""
    out = [str(c) for c in chats if c]
    if cfg.get("admin_copy", True) or not out: out.append(os.getenv("TG_CHAT") or "")
    for c in dict.fromkeys(c for c in out if c): tg(msg, c)

def class_chat(sc, prof): return prof.get("tg_chat") or sc.get("tg_chat")

def fmt_news(sc, items, cfg, head=""):
    return (f"🏫 {sc['name']}{head} – novità:\n" + "\n\n".join(
        f"• {'🔁 ' if re.search('rettific|integrazion|annull', i['title'], re.I) else ''}{i['title']}\n{i['url']}"
        + ("\n📝 " + i["sunto"]["testo"] if i.get("sunto") else "") + upload_hint(i, cfg) for i in items[:10])
        + (f"\n\n…e altre {len(items) - 10}: le trovi in ClassAI." if len(items) > 10 else "") + "\n\nApri ClassAI per la bozza WhatsApp.")

def news(sc, hot, cfg):
    """Chiamata da crawl.py con le novità per famiglie/alunni: gestore + gruppo della scuola ricevono tutto,
    il gruppo di ogni classe riceve solo ciò che riguarda quella classe."""
    if hot: tg_route(fmt_news(sc, hot, cfg), [sc.get("tg_chat")], cfg)
    done = {str(sc.get("tg_chat") or ""), str(os.getenv("TG_CHAT") or "")}
    for prof in profiles(sc):
        c = str(prof.get("tg_chat") or "")
        if not c or c in done: continue
        rel = [i for i in hot if relevant(i, prof)]
        if rel: tg(fmt_news(sc, rel, cfg, f" · classe {prof['classe']}"), c)

def unread(it):
    """Circolare di cui ClassAI non ha il testo: allegato bloccato/assente, scansione illeggibile o testo troppo corto."""
    return it.get("status") in ("titolo", "illeggibile") or (it.get("type") == "pdf" and len(it.get("text") or "") < 250)

def app_url(cfg):
    u, _, r = (cfg.get("repo") or "").partition("/")
    return cfg.get("app_url") or (f"https://{u.lower()}.github.io/{r}/" if u and r else "")

def upload_hint(it, cfg):
    a = app_url(cfg)
    return (("\n📄 Non riesco a leggerla da solo. Tocca qui, poi ① Apri e ② Carica:\n" + f"{a}?carica={it['id']}") if a
            else "\n📄 Non riesco a leggerla da solo: scarica il PDF e caricalo in ClassAI.") if unread(it) else ""

def short(it): return ("🔁 " if re.search(r"rettific|integrazion|annull", it["title"], re.I) else "") + re.sub(r"^Comunicazione n\. (\d+): ", r"n. \1 – ", it["title"])[:100]

def profiles(sc):
    d = sc.get("digest") or []
    return [d] if isinstance(d, dict) else d

def topic(sc, prof, salt):
    return prof.get("ntfy") or f"classai-{sc['id']}-{prof['classe'].lower()}-{hashlib.sha1((salt + sc['id'] + prof['classe']).encode()).hexdigest()[:6]}"

def ntfy(tp, title, msg, click=""):
    body = json.dumps({"topic": tp, "title": title, "message": msg, "click": click, "tags": ["school"]}).encode()
    try: urllib.request.urlopen(urllib.request.Request(os.getenv("NTFY_SERVER", "https://ntfy.sh"), body, {"Content-Type": "application/json"}), timeout=20)
    except Exception as e: print("ntfy:", e)

def notify_new(sc, new, salt, cfg=None):
    """Chiamata da crawl.py: avvisa su ntfy, canale per canale, le comunicazioni nuove che riguardano la classe."""
    for prof in profiles(sc):
        for it in new:
            if "score" in it and relevant(it, prof): ntfy(topic(sc, prof, salt), "ClassAI " + prof["classe"], short(it) + (("\n" + it["sunto"]["testo"]) if it.get("sunto") else "") + upload_hint(it, cfg or {}), it["url"])

def esc(t): return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def fold(line):
    b = line.encode("utf-8"); parts = []; lim = 75
    while len(b) > lim:
        cut = lim
        while (b[cut] & 0xC0) == 0x80: cut -= 1
        parts.append(b[:cut]); b = b[cut:]; lim = 74
    parts.append(b)
    return "\r\n ".join(x.decode("utf-8") for x in parts)

def make_ics(sc, prof, ag, today):
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ClassAI//IT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:" + esc(f"ClassAI {prof['classe']} – {sc['name']}"), "X-WR-TIMEZONE:Europe/Rome", "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"]
    for d, scad, it in ag:
        L += ["BEGIN:VEVENT", "UID:" + hashlib.sha1(f"{it['id']}{d}".encode()).hexdigest()[:20] + "@classai", f"DTSTAMP:{today:%Y%m%d}T000000Z",
              f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + dt.timedelta(days=1):%Y%m%d}",
              "SUMMARY:" + esc(("⏰ Scadenza: " if scad else "📅 ") + short(it)), "DESCRIPTION:" + esc(it["title"] + "\n" + it["url"]), "URL:" + it["url"]]
        if scad: L += ["BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-P1D", "DESCRIPTION:" + esc("Domani: " + short(it)), "END:VALARM"]
        L.append("END:VEVENT")
    L.append("END:VCALENDAR")
    return "\r\n".join(fold(x) for x in L) + "\r\n"

def rome_now():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Rome")).replace(tzinfo=None)
    except Exception:   # senza tzdata: stima ora legale (ultima dom. di marzo – ultima dom. di ottobre)
        u = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None); y = u.year
        last_sun = lambda m: max(dt.date(y, m, d) for d in range(25, 32) if dt.date(y, m, d).weekday() == 6)
        return u + dt.timedelta(hours=2 if last_sun(3) <= u.date() < last_sun(10) else 1)

def health(cfg, now):
    """Avviso se il controllo del sito non aggiorna i dati da più di 24 ore o non riesce a leggerlo."""
    out = []
    for sc in cfg["schools"]:
        f = f"docs/data/{sc['id']}.json"
        if not os.path.exists(f): out.append(f"• {sc['name']}: nessun dato ancora letto"); continue
        d = json.load(open(f, encoding="utf-8"))
        try: age = (now - dt.datetime.strptime(d.get("updated", ""), "%Y-%m-%d %H:%M")).total_seconds() / 3600
        except ValueError: age = 999
        if age > 24: out.append(f"• {sc['name']}: ultimo controllo riuscito {d.get('updated', '?')} ({int(age)} ore fa)")
        if d.get("errors"): out.append(f"• {sc['name']}: sito non raggiungibile ({'; '.join(d['errors'])[:200]})")
        elif d.get("pages", 1) == 0 and not d.get("items"): out.append(f"• {sc['name']}: 0 pagine lette, il sito potrebbe essere cambiato")
    return out

def main():
    a = sys.argv[1:]; dry = "--dry" in a; ics_only = "--ics-only" in a
    now = rome_now()
    today = dt.date.fromisoformat(a[a.index("--today") + 1]) if "--today" in a else now.date()
    cfg = json.load(open("config.json", encoding="utf-8-sig")); salt = cfg.get("salt", ""); sp = "state/reminders.json"
    sent = set(json.load(open(sp, encoding="utf-8"))) if os.path.exists(sp) else set(); msgs = []; prof_out = {}
    # Orario stabile: GitHub ragiona in UTC, quindi il workflow parte alle 5:30 e alle 6:30 UTC
    # e qui si invia una sola volta al giorno, dalle 7:00 ora italiana (= 7:30 sia d'inverno sia d'estate).
    if not ics_only and os.getenv("GITHUB_EVENT_NAME") == "schedule":
        if now.hour < 7 or f"day|{today}" in sent: print("non è ancora l'ora (o già inviato oggi): esco"); return
    if not ics_only: sent.add(f"day|{today}")
    if not ics_only:
        h = health(cfg, now)
        if h:
            m = "⚠️ ClassAI: il controllo del sito non sta funzionando.\n" + "\n".join(h) + (f"\nApri https://github.com/{cfg['repo']}/actions e guarda l'ultimo «ClassAI monitor»." if cfg.get("repo") else "")
            if dry: print(m, "\n---")
            else: tg(m)
    for sc in cfg["schools"]:
        f = f"docs/data/{sc['id']}.json"
        if not os.path.exists(f): continue
        items = json.load(open(f, encoding="utf-8"))["items"]; ps = profiles(sc)
        for prof in ps:
            full = []; seen = set()
            for it in items:
                if not relevant(it, prof): continue
                for d, scad in find_dates(it.get("title", "") + ". " + (it.get("text") or ""), today):
                    if -7 <= (d - today).days <= 180 and (it["id"], d) not in seen: seen.add((it["id"], d)); full.append((d, scad, it))
            full.sort(key=lambda x: x[0]); tp = topic(sc, prof, salt); tag = f"[{prof['classe']}] " if len(ps) > 1 else ""
            if not dry:
                os.makedirs("docs/cal", exist_ok=True); fn = f"cal/{sc['id']}-{re.sub('[^A-Za-z0-9]', '', prof['classe'].upper())}.ics"
                open("docs/" + fn, "w", encoding="utf-8", newline="").write(make_ics(sc, prof, full, today))
                po = {"classe": prof["classe"].upper(), "ics": fn, "ntfy": tp}
                if prof.get("tg_link") or sc.get("tg_link"): po["tg_link"] = prof.get("tg_link") or sc.get("tg_link")   # invito al gruppo Telegram
                prof_out.setdefault(sc["id"], []).append(po)
            if ics_only: continue
            week = [(d, s, it) for d, s, it in full if 0 <= (d - today).days <= 7]
            for d, scad, it in week:
                delta = (d - today).days
                if delta in (0, 2):
                    k = f"{prof['classe']}|{it['id']}|{d}|{delta}"
                    if k not in sent: sent.add(k); msgs.append((tp, f"{tag}{'⏰ Scadenza' if scad else '📅 Evento'} {'OGGI' if delta == 0 else 'tra 2 giorni'} ({GG[d.weekday()]} {d:%d/%m}): {short(it)}", it["url"], class_chat(sc, prof)))
            if today.weekday() == 0 and f"week|{sc['id']}|{prof['classe']}|{today}" not in sent:
                sent.add(f"week|{sc['id']}|{prof['classe']}|{today}")
                body = "\n".join(f"• {GG[d.weekday()]} {d:%d/%m} {'⏰' if s else '📅'} {short(it)}" for d, s, it in week) or "Nessuna scadenza o evento in programma."
                msgs.append((tp, f"{tag}🗓 Settimana dal {today:%d/%m} – classe {prof['classe']} ({sc['name']}):\n{body}", "", class_chat(sc, prof)))
    for tp, m, url, chat in msgs:
        if dry: print(f"[→ {'gruppo ' + str(chat) if chat else 'gestore'}{' + gestore' if chat and cfg.get('admin_copy', True) else ''}]", m, "\n---")
        else: tg_route(m + (("\n" + url) if url else ""), [chat], cfg); ntfy(tp, "ClassAI", m, url)
    if not dry:
        os.makedirs("state", exist_ok=True)
        if not ics_only: json.dump(sorted(sent), open(sp, "w", encoding="utf-8"))
        json.dump(prof_out, open("docs/data/profiles.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(len(msgs), "messaggi")

if __name__ == "__main__": main()
