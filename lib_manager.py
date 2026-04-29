from i18n import _, set_language
"""
lib_manager.py — Gestion automatique de la bibliothèque roomba (neutrino85/Roomba980-Python).
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import io
import importlib
import traceback

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOMBA_DIR = os.path.join(_PLUGIN_DIR, "roomba")

_GITHUB_ZIP = "https://github.com/neutrino85/Roomba980-Python/archive/refs/heads/master.zip"
_ZIP_PREFIX = "Roomba980-Python-master/roomba/"
_REQ_MEMBER = "Roomba980-Python-master/requirements.txt"


def ensure_sys_path():
    if _PLUGIN_DIR not in sys.path:
        sys.path.insert(0, _PLUGIN_DIR)


def _purge_roomba_cache():
    """Supprime les entrées roomba* de sys.modules (purge les ImportError mis en cache)."""
    for key in [k for k in sys.modules if k == "roomba" or k.startswith("roomba.")]:
        del sys.modules[key]


def _try_import_roomba():
    """
    Tente d'importer roomba et retourne (True, "") ou (False, message_erreur).
    Capture TOUTES les exceptions, pas seulement ImportError.
    """
    ensure_sys_path()
    _purge_roomba_cache()
    try:
        importlib.import_module("roomba")
        # Test supplementaire : les sous-modules utilises par le plugin
        importlib.import_module("roomba.password")
        _purge_roomba_cache()
        return True, ""
    except Exception:
        err = traceback.format_exc()
        _purge_roomba_cache()
        return False, err


def is_roomba_available():
    ok, _ = _try_import_roomba()
    return ok


def diagnose_roomba_import():
    """Retourne le traceback complet de l'echec d'import (pour les logs)."""
    _, err = _try_import_roomba()
    return err


def is_paho_available():
    try:
        importlib.import_module("paho.mqtt.client")
        return True
    except ImportError:
        return False


def _pip_install(packages, progress_cb=None):
    """Installe une liste de packages via pip. Retourne (ok, message)."""
    if not packages:
        return True, "Rien a installer."
    cmd = [sys.executable, "-m", "pip", "install"] + packages + ["--quiet"]
    if progress_cb:
        progress_cb("pip install " + " ".join(packages) + "...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            importlib.invalidate_caches()
            return True, "OK : " + " ".join(packages)
        return False, "pip echoue : " + result.stderr.strip()
    except Exception as e:
        return False, str(e)


def install_paho():
    return _pip_install(["paho-mqtt"])


def _install_requirements_from_archive(data, progress_cb=None):
    """
    Lit requirements.txt dans l'archive ZIP et installe les deps non-optionnelles.
    Ignore les lignes vides, commentaires et packages lourds (opencv, PIL...).
    """
    SKIP = {"pillow", "opencv-python", "opencv-python-headless", "numpy",
            "aiohttp", "requests", "matplotlib"}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            if _REQ_MEMBER not in zf.namelist():
                return True, "Pas de requirements.txt dans l'archive."
            content = zf.read(_REQ_MEMBER).decode(errors="replace")
    except Exception as e:
        return False, "Lecture requirements.txt : " + str(e)

    packages = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = line.split(">=")[0].split("==")[0].split("<=")[0].strip().lower()
        if name in SKIP:
            continue
        packages.append(line)

    if not packages:
        return True, "Aucune dependance obligatoire dans requirements.txt."

    return _pip_install(packages, progress_cb)


def download_roomba_lib(progress_cb=None):
    """
    Telecharge la lib roomba depuis GitHub, l'extrait et installe ses dependances.
    Retourne (succes, message).
    """
    def _log(msg):
        if progress_cb:
            progress_cb(msg)

    # ── 1. Telechargement ────────────────────────────────────────────────────
    _log("Telechargement depuis GitHub...")
    try:
        req = urllib.request.Request(
            _GITHUB_ZIP,
            headers={"User-Agent": "Domoticz-Roomba-Plugin/1.2"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        _log("Archive telechargee (" + str(len(data) // 1024) + " Ko).")
    except Exception as e:
        return False, "Telechargement echoue : " + str(e)

    # ── 2. Extraction du dossier roomba/ ─────────────────────────────────────
    _log("Extraction des fichiers roomba/...")
    try:
        os.makedirs(_ROOMBA_DIR, exist_ok=True)
        extracted = 0
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            members = [m for m in zf.namelist()
                       if m.startswith(_ZIP_PREFIX) and not m.endswith("/")]
            for member in members:
                rel  = member[len(_ZIP_PREFIX):]
                dest = os.path.join(_ROOMBA_DIR, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with zf.open(member) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                extracted += 1
        _log(str(extracted) + " fichiers extraits.")
    except Exception as e:
        return False, "Extraction echouee : " + str(e)

    # ── 3. Installation des dependances depuis requirements.txt ───────────────
    _log("Installation des dependances...")
    ok, msg = _install_requirements_from_archive(data, progress_cb)
    if not ok:
        _log("Avertissement dependances : " + msg)

    # ── 4. Test d'import avec purge complete du cache ─────────────────────────
    _purge_roomba_cache()
    importlib.invalidate_caches()
    ensure_sys_path()

    ok, err = _try_import_roomba()
    if ok:
        return True, "Bibliotheque roomba installee et importable avec succes."

    # ── 5. Diagnostic detaille si l'import echoue encore ────────────────────
    detail = "\n=== DIAGNOSTIC IMPORT ===\n" + err
    _log(detail)
    return False, (
        "Extraction OK mais import echoue. Voir les logs Domoticz pour le detail.\n" + err
    )


def ensure_all(progress_cb=None):
    """Verifie et installe paho-mqtt + roomba. Retourne (tout_ok, [(statut, msg)])."""
    ensure_sys_path()
    messages = []

    if not is_paho_available():
        ok, msg = install_paho()
        messages.append(("ok" if ok else "err", "paho-mqtt : " + msg))
        if not ok:
            return False, messages
    else:
        messages.append(("ok", "paho-mqtt deja disponible."))

    if not is_roomba_available():
        ok, msg = download_roomba_lib(progress_cb)
        messages.append(("ok" if ok else "err", msg))
        if not ok:
            # Log le diagnostic complet
            diag = diagnose_roomba_import()
            if diag:
                messages.append(("err", "Detail : " + diag))
            return False, messages
    else:
        messages.append(("ok", "Bibliotheque roomba deja disponible."))

    return True, messages
