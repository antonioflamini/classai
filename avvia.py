#!/usr/bin/env python3
"""ClassAI – avvio automatico: crea il repository GitHub, carica il progetto, attiva Pages, imposta i segreti e lancia i controlli.
Uso: apri un terminale nella cartella e scrivi:  python avvia.py   (su Mac/Linux anche python3 avvia.py)"""
import getpass, json, os, platform, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

if os.name == "nt":   # Windows: trova Git e GitHub CLI appena installati senza dover riaprire il terminale
    try:
        import winreg
        extra = []
        for root, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"), (winreg.HKEY_CURRENT_USER, "Environment")):
            with winreg.OpenKey(root, key) as k: extra += os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]).split(";")
        os.environ["PATH"] = os.pathsep.join(dict.fromkeys(os.environ.get("PATH", "").split(os.pathsep) + [p for p in extra if p]))
    except Exception: pass

def run(*a, inp=None, check=True, quiet=False):
    r = subprocess.run(a, input=inp, text=True, encoding="utf-8", errors="replace", capture_output=True)
    r.stdout = r.stdout or ""; r.stderr = r.stderr or ""
    if r.returncode and check:
        print(f"\n✖ Comando fallito: {' '.join(a[:4])}\n{r.stderr.strip() or r.stdout.strip()}"); sys.exit(1)
    return r

def ask(env, prompt, secret=False, default=""):
    if os.getenv(env) is not None: return os.getenv(env)
    v = (getpass.getpass if secret else input)(prompt + (f" [{default}]" if default else "") + ": ").strip()
    return v or default

def main():
    print("== ClassAI: avvio automatico ==\n")
    miss = [t for t in ("git", "gh") if not shutil.which(t)]
    if miss:
        os_ = platform.system()
        cmd = {"Windows": "winget install --id Git.Git -e && winget install --id GitHub.cli -e", "Darwin": "brew install git gh"}.get(os_, "sudo apt install git gh   (oppure vedi https://cli.github.com)")
        print("Mancano:", ", ".join(miss), "\nInstallali con:\n  " + cmd + "\npoi riapri il terminale e rilancia lo script."); sys.exit(1)
    if run("gh", "auth", "status", check=False).returncode:
        print("1/7 Accedi a GitHub: si apre il browser, conferma il codice che ti mostra.")
        print("   Nel terminale comparirà un codice XXXX-XXXX: premi Invio, inseriscilo nella pagina GitHub e autorizza «GitHub CLI».")
        subprocess.run(["gh", "auth", "login", "-w", "-h", "github.com", "-p", "https", "-s", "repo,workflow"])
        if run("gh", "auth", "status", check=False).returncode: print("Accesso non riuscito."); sys.exit(1)
    run("gh", "auth", "setup-git", check=False)   # git push usa le credenziali di GitHub CLI
    user = run("gh", "api", "user", "-q", ".login").stdout.strip(); print(f"✔ Collegato a GitHub come {user}\n")
    owner = ask("CLASSAI_OWNER", "2/7 Il tuo nome (comparirà come 'ClassAI by …')")
    repo = ask("CLASSAI_REPO", "    Nome del repository", default="classai")
    wa = ask("CLASSAI_WA", "    Il tuo numero WhatsApp con prefisso, senza + (facoltativo, es. 393331234567)")
    print("\n3/7 Telegram: apri @BotFather → /newbot → copia il token.")
    tok = ask("CLASSAI_TG_TOKEN", "    Incolla il token del bot (facoltativo, Invio per saltare)", secret=True)
    chat = os.getenv("CLASSAI_TG_CHAT", "")
    if tok and not chat:
        input("    Ora scrivi 'ciao' al tuo bot su Telegram e premi Invio qui… ")
        try:
            j = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getUpdates", timeout=20))
            chat = str(j["result"][-1]["message"]["chat"]["id"]); print("✔ Chat trovata")
        except Exception: print("  Non ho trovato la chat: i messaggi Telegram saranno disattivati (puoi aggiungerli dopo).")
    print("\n4/7 Chiave AI: aistudio.google.com → Get API key.")
    key = ask("CLASSAI_AI_KEY", "    Incolla la chiave (facoltativo, senza il sunto AI userà le regole)", secret=True)
    c = json.load(open("config.json", encoding="utf-8-sig")); c["owner"] = owner or c.get("owner", ""); c["repo"] = f"{user}/{repo}"; c.setdefault("contact", {})["whatsapp"] = wa
    json.dump(c, open("config.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("\n5/7 Carico il progetto su GitHub…")
    if not os.path.isdir(".git"): run("git", "init", "-b", "main")
    run("git", "add", "-A"); run("git", "-c", "user.name=classai", "-c", "user.email=bot@users.noreply.github.com", "commit", "-m", "ClassAI", check=False)
    r = run("gh", "repo", "create", f"{user}/{repo}", "--public", "--source", ".", "--remote", "origin", "--push", check=False)
    if r.returncode:
        if "already exists" in r.stderr: run("git", "remote", "add", "origin", f"https://github.com/{user}/{repo}.git", check=False); run("git", "push", "-u", "origin", "main", "--force")
        else: print(r.stderr); sys.exit(1)
    print("6/7 Attivo il sito (Pages) e i segreti…")
    run("gh", "api", "-X", "POST", f"repos/{user}/{repo}/pages", "-f", "source[branch]=main", "-f", "source[path]=/docs", check=False)
    for n, v in (("TG_TOKEN", tok), ("TG_CHAT", chat), ("AI_API_KEY", key)):
        if v: run("gh", "secret", "set", n, "-R", f"{user}/{repo}", inp=v)
    print("7/7 Lancio il primo controllo del sito (3-10 minuti)…")
    run("gh", "workflow", "run", "monitor.yml", "-R", f"{user}/{repo}"); time.sleep(8)
    rid = run("gh", "run", "list", "-R", f"{user}/{repo}", "--workflow", "monitor.yml", "-L", "1", "--json", "databaseId", "-q", ".[0].databaseId").stdout.strip()
    ok = True
    if rid: ok = subprocess.run(["gh", "run", "watch", rid, "-R", f"{user}/{repo}", "--exit-status"]).returncode == 0
    if ok: run("gh", "workflow", "run", "digest.yml", "-R", f"{user}/{repo}", check=False)
    print("\n✔ Fatto!" if ok else f"\n⚠ Il controllo ha avuto un errore: apri https://github.com/{user}/{repo}/actions e mandami le ultime righe del log.")
    print(f"\nApp (pronta tra 1-2 minuti): https://{user}.github.io/{repo}/\nSul telefono apri il link → Aggiungi a Home → primo accesso: classe 3AS, indirizzo Operatore socio sanitario, data 15/10/2026.")
main()
