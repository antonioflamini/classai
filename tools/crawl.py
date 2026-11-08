#!/usr/bin/env python3
"""ClassAI: esplora l'intero sito della scuola (HTML + PDF, con OCR per le scansioni) e scrive docs/data/<id>.json"""
import json, os, re, sys, time, io, hashlib, subprocess, tempfile, glob
import urllib.request, urllib.parse, urllib.robotparser
from html.parser import HTMLParser
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
os.environ["TZ"] = "Europe/Rome"   # orari in ora italiana anche sui server GitHub (UTC)
if hasattr(time, "tzset"): time.tzset()
UA = "ClassAI-Monitor/2.0 (uso personale dei rappresentanti di classe; 1 richiesta/sec)"
PARENT = re.compile(r"circolar|avvis|genitor|famigli|student|alunn|iscrizion|scadenz|pagopa|uscit|gita|viaggio d|colloqui|sciopero|assemblea|elezion|calendario|orario|vacanz|mensa|libri di testo|open day|orientament|esami|scrutini|pagell|contribut|assicurazion|vaccin|borsa di studio|pcto|alternanza|invalsi|recuper|sportello|certificazion|autorizzazion", re.I)
STAFF = re.compile(r"collegio (dei )?docenti|personale ata|interpell|ordine di servizio|graduatori|supplenz|dipartiment", re.I)
FAM = re.compile(r"genitor|famigli|student|alunn", re.I)
SKIP = re.compile(r"privacy|cookie|login|wp-admin|wp-json|/feed|/tag/|/author/|trasparente|^(mailto|tel|javascript):|\.(jpe?g|png|gif|svg|zip|docx?|xlsx?|pptx?|mp[34]|css|js|ico)(\?|$)", re.I)

def fetch(u):
    time.sleep(1)
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30)
    return r.read(8_000_000), r.headers.get("Content-Type", ""), r.headers.get("Last-Modified", "")

class Page(HTMLParser):
    def __init__(s, mark=False):
        super().__init__(); s.mark = mark; s.base = ""; s.links = []; s.txt = []; s.title = ""; s.t = 0; s.a = None; s.at = ""; s.skip = 0
    def handle_starttag(s, t, a):
        a = dict(a)
        if t == "title": s.t = 1
        if t == "a" and a.get("href"):
            s.a = a["href"]; s.at = ""
            if s.mark and "sdg2/Documenti" in s.a: s.txt.append(" ⟦" + urllib.parse.urljoin(s.base, s.a) + "⟧ ")
        if t in ("script", "style", "nav", "footer", "noscript"): s.skip += 1
    def handle_endtag(s, t):
        if t == "title": s.t = 0
        if t == "a" and s.a: s.links.append((s.a, " ".join(s.at.split()))); s.a = None
        if t in ("script", "style", "nav", "footer", "noscript") and s.skip: s.skip -= 1
    def handle_data(s, d):
        if s.t: s.title += d
        if s.a is not None: s.at += d
        if not s.skip: s.txt.append(d)

def pdf_text(data):
    txt = ""
    try:
        from pypdf import PdfReader
        txt = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages).strip()
    except Exception: pass
    if len(txt) >= 80: return txt, "ok"
    try:   # scansione: OCR gratuito con Tesseract (prime 4 pagine)
        with tempfile.TemporaryDirectory() as d:
            open(d + "/a.pdf", "wb").write(data)
            subprocess.run(["pdftoppm", "-r", "150", "-f", "1", "-l", "4", "-png", d + "/a.pdf", d + "/p"], check=True, timeout=120)
            out = [subprocess.run(["tesseract", f, "-", "-l", "ita"], capture_output=True, text=True, timeout=120).stdout for f in sorted(glob.glob(d + "/p*.png"))]
            o = "\n".join(out).strip()
            if len(o) >= 80: return o, "ocr"
    except Exception: pass
    return txt, "illeggibile"

def pubdate(text, lm):
    m = re.search(r"(?:pubblicat[oa]|del|data)\s*(?:il\s*)?(\d{1,2})[/.](\d{1,2})[/.](20\d{2})", text[:1500], re.I)
    if m and 1 <= int(m[2]) <= 12 and 1 <= int(m[1]) <= 31: return f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(lm).strftime("%Y-%m-%d")
    except Exception: return ""

TIPI = ("Alunni", "Docenti", "Famiglie", "Personale ATA", "Tutto il personale", "Albo sindacale")

def pvw(root, sc, seen, first):
    """Siti Spaggiari 'Prima Visione Web': le circolari stanno in /comunicati (schede con protocollo, tipologia, allegato)."""
    out = []
    for pg in range(sc.get("list_pages", 6 if first else 2)):
        try: data, _, _ = fetch(f"{root}/comunicati?tipo=comunicati&cerca=&categoria=&storico=0&aoo=&page={pg}")
        except Exception: break
        p = Page(mark=True); p.base = root + "/"; p.feed(data.decode("utf-8", "ignore"))
        blocks = re.split(r"(?=Protocollo\s+\S+\s+del\s+\d\d/\d\d/\d{4})", " ".join(" ".join(p.txt).split()))[1:]
        if not blocks: break
        oldest = "9999"; fresh = 0
        for b in blocks:
            m = re.search(r"Protocollo\s+(\S+)\s+del", b)
            n = re.search(r"Comunicazione\s+N°\s*(\d+)\s+(.*?)\s+Pubblicato il:\s*(\d\d)/(\d\d)/(\d{4})", b)
            if not (m and n): continue
            pub = f"{n[5]}-{n[4]}-{n[3]}"; oldest = min(oldest, pub)
            h = hashlib.sha1(f"pvw{m[1]}{n[1]}".encode()).hexdigest()[:12]
            if h in seen: continue
            seen[h] = 1; fresh += 1
            if sc.get("since") and pub < sc["since"]: continue
            ts = re.search(r"Tipologia:\s*(.*?)(?=\s*(?:Allegati:|⟦|$))", b)
            tip = [t for t in TIPI if ts and re.search(r"\b" + t + r"\b", ts[1])]
            dl = [l for l in re.findall(r"⟦(.*?)⟧", b) if "download=1" in l] or re.findall(r"⟦(.*?)⟧", b)[:1]
            text, st = "", "titolo"
            if dl:
                try:
                    d, _, _ = fetch(dl[-1])
                    if d[:4] == b"%PDF":
                        text, s2 = pdf_text(d)
                        st = s2 if len(text) >= 80 else "titolo"
                except Exception as e:
                    sc["_dl_fail"] = sc.get("_dl_fail", 0) + 1; print("allegato non scaricabile:", dl[-1], e)
            out.append({"id": h, "title": f"Comunicazione n. {n[1]}: {n[2]}"[:200], "url": dl[-1].replace("?download=1", "") if dl else root + "/comunicati", "type": "pdf",
                        "status": st if text else "titolo", "found": time.strftime("%Y-%m-%d %H:%M"), "pub": pub, "score": 1, "tip": tip,
                        "docs": [x.replace("?download=1", "") for x in dl[:-1]], "text": (n[2] + ". " + text)[:8000]})
        if oldest < sc.get("since", "0000") or (not first and not fresh): break
    return out

def tg(msg):
    tok, chat = os.getenv("TG_TOKEN"), os.getenv("TG_CHAT")
    if tok and chat:
        try: urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", urllib.parse.urlencode({"chat_id": chat, "text": msg[:4000], "disable_web_page_preview": "true"}).encode(), timeout=20)
        except Exception as e: print("telegram:", e)

def crawl(sc):
    root = sc["url"].rstrip("/"); host = urllib.parse.urlparse(root).netloc
    sid = sc["id"]; sp = f"state/{sid}.json"; dp = f"docs/data/{sid}.json"
    first = not os.path.exists(sp)
    seen = json.load(open(sp, encoding="utf-8")) if not first else {}
    old = json.load(open(dp, encoding="utf-8"))["items"] if os.path.exists(dp) else []
    rp = urllib.robotparser.RobotFileParser(root + "/robots.txt")
    try: rp.read()
    except Exception: pass
    q = [(root, 0)]; vis = set(); lt = {}; new = []; errs = []; n = 0
    ad = sc.get("adapter", "auto")
    if ad == "auto":
        try: ad = "pvw" if b"pvw2/" in fetch(root)[0] else "generic"
        except Exception: ad = "generic"
    if ad == "pvw": new += pvw(root, sc, seen, first)
    try:   # sitemap
        sm, _, _ = fetch(root + "/sitemap.xml")
        for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", sm.decode("utf-8", "ignore"))[:300]:
            if urllib.parse.urlparse(loc).netloc == host and not loc.endswith(".xml"): q.append((loc, 1))
    except Exception: pass
    while q and n < sc.get("max_pages", 150):
        u, d = q.pop(0); u = urllib.parse.urldefrag(u)[0]
        if u in vis or SKIP.search(u) or (ad == "pvw" and "/comunicati" in u) or urllib.parse.urlparse(u).netloc != host: continue
        vis.add(u)
        try:
            if not rp.can_fetch(UA, u): continue
        except Exception: pass
        ispdf = u.lower().split("?")[0].endswith(".pdf")
        if ispdf and u in seen: continue
        try: data, ct, lm = fetch(u); n += 1
        except Exception as e:
            if u == root: errs.append(f"{sid}: {e}")
            continue
        if ispdf or "pdf" in ct:
            text, st = pdf_text(data); title = lt.get(u) or os.path.basename(u.split("?")[0]).replace("-", " ").replace("_", " ")[:140]; kind = "pdf"; nl = 0
        elif "html" in ct:
            p = Page(); p.feed(data.decode("utf-8", "ignore"))
            text = " ".join(" ".join(p.txt).split()); st = "ok"; title = " ".join(p.title.split())[:140] or u; kind = "html"; nl = len(p.links)
            for h, t in p.links:
                v = urllib.parse.urljoin(u, h)
                if t and v not in lt: lt[v] = t[:140]
                if d < sc.get("depth", 3) or v.lower().split("?")[0].endswith(".pdf"): q.append((v, d + 1))
        else: continue
        h = hashlib.sha1(u.encode()).hexdigest()[:12]
        if h in seen: continue
        seen[h] = 1
        if kind == "html" and (nl > 25 or len(text) < 250): continue   # pagine-indice: si esplorano ma non sono comunicazioni
        pub = pubdate(text, lm)
        if pub and sc.get("since") and pub < sc["since"]: continue
        sc_ = len(set(m.lower() for m in PARENT.findall(title + " " + text[:3000])))
        if kind == "html" and sc_ < 1: continue
        new.append({"id": h, "title": title, "url": u, "type": kind, "status": st, "found": time.strftime("%Y-%m-%d %H:%M"), "pub": pub, "score": sc_, "text": text[:8000]})
    try:
        import ai; ai.enrich(new + old, cfg)
    except Exception as e: print("ai:", e)
    ids = {i["id"] for i in new}
    items = (new + [o for o in old if o["id"] not in ids])[:200]
    os.makedirs("docs/data", exist_ok=True); os.makedirs("state", exist_ok=True)
    json.dump({"updated": time.strftime("%Y-%m-%d %H:%M"), "errors": errs, "pages": n, "dl_fail": sc.get("_dl_fail", 0), "items": items}, open(dp, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(seen, open(sp, "w", encoding="utf-8"))
    if not first:
        hot = [i for i in new if (("Famiglie" in i["tip"] or "Alunni" in i["tip"]) if "tip" in i else (i["score"] >= 1 and not (STAFF.search(i["title"] + i["text"][:1500]) and not FAM.search(i["text"][:3000]))))]
        if hot: tg(f"🏫 {sc['name']} – novità:\n" + "\n".join(f"• {'🔁 ' if re.search('rettific|integrazion|annull', i['title'], re.I) else ''}{i['title']}\n{i['url']}" + ("\n📝 " + i["sunto"]["testo"] if i.get("sunto") else "") for i in hot[:10]) + "\n\nApri ClassAI per la bozza WhatsApp.")
    if not first:
        try:
            import digest; digest.notify_new(sc, new, cfg.get("salt", ""))
        except Exception as e: print("ntfy:", e)
    if errs: tg("⚠️ ClassAI non riesce a leggere il sito:\n" + "\n".join(errs))
    print(sid, n, "pagine,", len(new), "nuove,", len(errs), "errori")
    return {"id": sid, "name": sc["name"], "updated": time.strftime("%Y-%m-%d %H:%M")}

cfg = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "config.json", encoding="utf-8-sig"))   # utf-8-sig: accetta anche file salvati col Blocco note
done = []
for s in cfg["schools"]:
    if s["url"].startswith("INCOLLA"): sys.exit("Imposta l'URL in config.json")
    done.append(crawl(s))
json.dump({"owner": cfg.get("owner", ""), "contact": cfg.get("contact", {}), "repo": cfg.get("repo", ""), "schools": done}, open("docs/data/schools.json", "w", encoding="utf-8"), ensure_ascii=False)
