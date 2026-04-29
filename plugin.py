"""
<plugin key="Roomba" name="iRobot Roomba" author="Neutrino" version="1.2.5"
         externallink="https://github.com/neutrino85/Roomba980-Python">
    <description>
        Contrôle iRobot Roomba via la bibliothèque Roomba980-Python.
        Récupération des identifiants pour se connecter au robot : http://IPdomoticz:8788 (par défaut)
        Control the iRobot Roomba via the Roomba980-Python library.
        Retrieve the credentials to connect to the robot: http://IPdomoticz:8788 (by default)
    </description>
    <params>
        <param field="Address"  label="IP Roomba"            width="150px" required="true"  default=""/>
        <param field="Username" label="BLID (optionnel)"     width="200px" required="false" default=""/>
        <param field="Password" label="Password (optionnel)" width="200px" required="false" default="" password="true"/>
        
        <param field="Mode1"    label="Port UI Enrollment"   width="80px"  required="true"  default="8788"/>
        <param field="Mode2"    label="Heartbeat (s)"        width="80px"  required="true"  default="30"/>
        <param field="Mode3"    label="Langue"               width="120px" required="true"  default="fr">
            <options>
                <option label="Français" value="fr" default="true"/>
                <option label="English" value="en"/>
            </options>
        </param>

        <param field="Mode6"    label="Debug" width="75px">
            <options>
                <option label="Aucun"   value="0" default="true"/>
                <option label="Python"  value="2"/>
                <option label="Basique" value="62"/>
                <option label="Tout"    value="1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import os
import sys
import json
import time
import asyncio
import threading

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

import Domoticz
from i18n import _, set_language
from lib_manager import ensure_all, is_roomba_available, is_paho_available
from enrollment_server import EnrollmentServer

_CRED_FILE = os.path.join(_PLUGIN_DIR, "credentials.json")
UNIT_STATE = 1
UNIT_BAT   = 2
UNIT_BIN   = 3
UNIT_CMD   = 4

# Niveau 0 = "En charge" pour coller au script dzVents LUA

# Niveaux de commandes
CMD_KEYS = {
    0:  "cmd_charging",
    10: "cmd_start",
    20: "cmd_pause",
    30: "cmd_resume",
    40: "cmd_dock",
    50: "cmd_stop",
    60: "cmd_reboot"
}

def get_cmd_levels():
    return {k: _(v) for k, v in CMD_KEYS.items()}

CMD_MAP = {
    0:  "charge",
    10: "start",
    20: "pause",
    30: "resume",
    40: "dock",
    50: "stop",
    60: "reset"
}

# Clé de base des icônes dans icons.txt du zip
ICON_KEY = "Saugroboter"
ICON_ZIP = "Saugroboter.zip"

def _save_credentials(blid, password):
    tmp = _CRED_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"blid": blid, "password": password, "version": 1}, f, indent=2)
    os.replace(tmp, _CRED_FILE)
    Domoticz.Log("Credentials sauvegardés → " + _CRED_FILE)

def _load_credentials():
    if not os.path.isfile(_CRED_FILE):
        return None
    try:
        with open(_CRED_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("blid") and data.get("password"):
            return data
    except Exception as e:
        Domoticz.Error("Lecture credentials.json : " + str(e))
    return None

def _delete_credentials():
    if os.path.isfile(_CRED_FILE):
        os.remove(_CRED_FILE)
        Domoticz.Log(_("cred_deleted"))


class BasePlugin:
    def __init__(self):
        self._loop    = None
        self._worker  = None
        self._roomba  = None
        self._enroll  = None
        self._running = False
        self._blid    = ""
        self._password = ""
        self._last_state = None  
        self._last_bat = None     
        self._last_bin = None     

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def onStart(self):
        # Initialize Language based on Mode3 if available
        lang = Parameters.get("Mode3", "fr") if "Parameters" in globals() else "fr"
        set_language(lang)

        debug = int(Parameters["Mode6"])
        if debug > 0:
            Domoticz.Debugging(debug)
         # ── Chargement icône personnalisée ──────────────────────────────────
        # bbox.zip doit être dans le dossier du plugin.
        # icons.txt dans le zip doit avoir une clé commençant par "BboxPlugin".
        # Exemple de icons.txt :
        #   BboxPlugin
        #   Bbox Router
        #   Icône pour la Bouygues Bbox
        if ICON_KEY not in Images:
            try:
                Domoticz.Image(Filename=ICON_ZIP).Create()
                Domoticz.Log("Icône '{}' chargée depuis {}".format(ICON_KEY, ICON_ZIP))
            except Exception as exc:
                Domoticz.Error("Impossible de charger {} : {}".format(ICON_ZIP, exc))
        
        self._createDevices()

        lib_ok  = is_roomba_available()
        paho_ok = is_paho_available()

        if not lib_ok or not paho_ok:
            Domoticz.Log(_("lib_missing"))
            ok, messages = ensure_all(progress_cb=Domoticz.Log)
            for status, msg in messages:
                (Domoticz.Log if status == "ok" else Domoticz.Error)(msg)
            lib_ok  = is_roomba_available()
            paho_ok = is_paho_available()
            if not lib_ok:
                Domoticz.Error(_("enroll_failed"))
        else:
            Domoticz.Log(_("lib_available"))

        creds = _load_credentials()
        if creds:
            self._blid     = creds["blid"]
            self._password = creds["password"]
            Domoticz.Log(_("cred_loaded"))
        else:
            self._blid     = Parameters["Username"].strip()
            self._password = Parameters["Password"].strip()
            if self._blid and self._password:
                _save_credentials(self._blid, self._password)

        port = int(Parameters.get("Mode1", 8788))
        self._enroll = EnrollmentServer(
            port=port,
            current_ip=Parameters["Address"].strip(),
            on_credentials=self._onCredentials,
            on_reset=self._onReset,
            on_install=self._onInstall,
            has_credentials=bool(self._blid and self._password),
            blid=self._blid,
            lib_ok=lib_ok,
            paho_ok=paho_ok,
        )
        self._enroll.start()
        Domoticz.Log(_("enroll_page", port=port))

        if lib_ok and self._blid and self._password and Parameters["Address"].strip():
            self._startWorker()
        elif not lib_ok:
            Domoticz.Log(_("waiting_lib"))
        else:
            Domoticz.Log(_("waiting_credentials"))

    def onStop(self):
        if self._enroll:
            self._enroll.stop()   # bloque ~1s max, libère EnrollHTTP proprement
        self._stopWorker()
        Domoticz.Log(_("plugin_stopped"))

    def onHeartbeat(self):
        if self._running:
            self._submit({"action": "poll"})

    def onCommand(self, Unit, Command, Level, Hue):
        if Unit == UNIT_CMD and self._running:
            cmd = CMD_MAP.get(int(Level), "stop")
            self._submit({"action": "command", "cmd": cmd})

    # ── Callbacks enrollment ───────────────────────────────────────────────────

    def _onCredentials(self, blid, password):
        _save_credentials(blid, password)
        self._blid     = blid
        self._password = password
        if self._running:
            self._stopWorker()
        if is_roomba_available() and Parameters["Address"].strip():
            self._startWorker()

    def _onReset(self):
        _delete_credentials()
        self._blid = self._password = ""
        self._stopWorker()
        self._enroll.set_has_credentials(False)

    def _onInstall(self, ok, messages):
        lib_ok  = is_roomba_available()
        paho_ok = is_paho_available()
        self._enroll.update_lib_status(lib_ok, paho_ok)
        for status, msg in messages:
            (Domoticz.Log if status == "ok" else Domoticz.Error)(msg)
        if lib_ok and self._blid and self._password and not self._running:
            self._startWorker()
    
    
    # ── Worker asyncio ─────────────────────────────────────────────────────────

    def _startWorker(self):
        self._running = True
        self._loop    = asyncio.new_event_loop()
        self._worker  = threading.Thread(target=self._taskLoop, daemon=True, name="RoombaWorker")
        self._worker.start()
        time.sleep(0.2)
        self._submit({"action": "connect"})
        Domoticz.Heartbeat(int(Parameters.get("Mode2", 30)))

    def _submit(self, task):
        if self._running and self._loop and self._loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self._dispatch(task), self._loop)
            except RuntimeError:
                pass

    def _stopWorker(self):
        self._running = False
        if self._loop and self._loop.is_running():
            # 1. Déconnecter proprement (annule les tasks + loop_stop paho) AVANT d'arrêter la boucle
            future = asyncio.run_coroutine_threadsafe(self._shutdown_roomba(), self._loop)
            try:
                future.result(timeout=4)
            except Exception:
                pass
            # 2. Arrêter la boucle asyncio
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=5)
        self._worker = None

    def _taskLoop(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        except Exception as e:
            Domoticz.Error("Erreur boucle asyncio : " + str(e))
        finally:
            # Fermeture propre : pas de run_until_complete ici pour éviter de re-bloquer
            self._loop.close()

    # ── Coroutines asyncio ─────────────────────────────────────────────────────

    async def _shutdown_roomba(self):
        """Annule toutes les tasks asyncio ET arrête le thread réseau paho."""
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        if self._roomba:
            try:
                # Arrêt du thread paho loop_start() — la lib ne le fait pas dans _disconnect()
                self._roomba.client.loop_stop()
            except Exception:
                pass
            try:
                self._roomba.client.disconnect()
            except Exception:
                pass
        self._roomba = None

    async def _dispatch(self, task):
        action = task["action"]
        try:
            if action == "connect":
                await self._connect()
            elif action == "poll":
                await self._poll()
            elif action == "command":
                await self._command(task["cmd"])
        except Exception as e:
            Domoticz.Error("Erreur _dispatch " + action + " : " + str(e))

    async def _connect(self):
        from roomba import Roomba
        self._roomba = Roomba(Parameters["Address"].strip(), self._blid, self._password)
        self._roomba.connect()
        await asyncio.sleep(5)
        Domoticz.Log(_("roomba_connected"))
        await self._poll()

    async def _poll(self):
        if not self._roomba:
            return

        ms = getattr(self._roomba, "master_state", {})
        reported = ms.get("state", {}).get("reported", {})

        state = str(getattr(self._roomba, "current_state", "Inconnu"))
        bat   = int(reported.get("batPct", 0) or 0)
        bin_f = reported.get("bin", {}).get("full", False)

        if state != self._last_state:
            Devices[UNIT_STATE].Update(nValue=0, sValue=state)
            self._last_state = state
            Domoticz.Log("state → " + state)

        #if bat != self._last_bat:
        Devices[UNIT_BAT].Update(nValue=bat, sValue=str(bat))
        self._last_bat = bat
        Domoticz.Log("bat → {}%".format(bat))

        if bin_f != self._last_bin:
            Devices[UNIT_BIN].Update(nValue=1 if bin_f else 0, sValue="")
            self._last_bin = bin_f
            Domoticz.Log("bin_full → " + str(bin_f))
        
    async def _command(self, cmd):
        if not self._roomba:
            return
        self._roomba.send_command(cmd)
        Domoticz.Log("Commande envoyée : " + str(cmd))
        await asyncio.sleep(2)
        await self._poll()

    # ── Devices ───────────────────────────────────────────────────────────────

    def _icon_id(self):
        """Retourne l'ID de l'icône si disponible, sinon 0."""
        if ICON_KEY in Images:
            return Images[ICON_KEY].ID
        return 0

    def _createDevices(self):
        icon = self._icon_id()
        opts = {
            "LevelActions": "|" * (len(CMD_KEYS) - 1),
            "LevelNames": "|".join(get_cmd_levels().values()),
            "LevelOffHidden": "true",
            "SelectorStyle": "0"
            # Suppression de "Image": icon ici
        }

        if UNIT_STATE not in Devices:
            Domoticz.Device(Name=_("device_state"), Unit=UNIT_STATE, TypeName="Text", Image=icon, Used=1).Create()
        if UNIT_BAT not in Devices:
            Domoticz.Device(Name=_("device_battery"), Unit=UNIT_BAT, TypeName="Custom",
                            Options={"Custom": "1;%"}, Image=icon, Used=1).Create()
        if UNIT_BIN not in Devices:
            Domoticz.Device(Name=_("device_bin"), Unit=UNIT_BIN, TypeName="Switch", Image=icon, Used=1).Create()
            
        if UNIT_CMD not in Devices:
            Domoticz.Device(Name=_("device_commands"), Unit=UNIT_CMD,
                            TypeName="Selector Switch", Options=opts, Image=icon, Used=1).Create()
        else:
            Devices[UNIT_CMD].Update(
                nValue=Devices[UNIT_CMD].nValue,
                sValue=Devices[UNIT_CMD].sValue,
                Options=opts,
                Image=icon
            )


_plugin = BasePlugin()

def onStart():              _plugin.onStart()
def onStop():               _plugin.onStop()
def onHeartbeat():          _plugin.onHeartbeat()
def onCommand(U, C, L, H): _plugin.onCommand(U, C, L, H)