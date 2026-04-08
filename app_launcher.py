import os
import subprocess
import webbrowser

APP_ALIASES = {
    "steam": r"C:\Program Files (x86)\Steam\Steam.exe",
    "discord": r"%LocalAppData%\Discord\Update.exe --processStart Discord.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}

def launch_app(name: str):
    key = name.strip().lower()
    if not key:
        return False, "No app name given."

    target = APP_ALIASES.get(key, key)

    try:
        if "--processStart" in target:
            expanded = os.path.expandvars(target)
            subprocess.Popen(expanded, shell=True)
        else:
            expanded = os.path.expandvars(target)
            subprocess.Popen(expanded, shell=True)
        return True, f"Launched: {name}"
    except Exception as e:
        return False, f"Failed to launch {name}: {e}"

def open_url(url: str):
    try:
        webbrowser.open(url)
        return True, f"Opened: {url}"
    except Exception as e:
        return False, f"Failed to open {url}: {e}"