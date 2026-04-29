"""
enrollment_server.py — Serveur HTTP léger pour l'enrôlement du Roomba.
"""

import ipaddress
import json
from i18n import _, set_language
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Le beau design original restauré (avec les accolades {{ }} échappées pour Python)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Roomba Domoticz Enrollment</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {{
            --bg: #f8fafc; --surface: #ffffff; --text: #1e293b; --text-muted: #64748b;
            --primary: #0284c7; --primary-hover: #0369a1; --border: #e2e8f0;
            --success: #10b981; --error: #ef4444; --warning: #f59e0b;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; padding: 2rem 1rem; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .card {{ background: var(--surface); padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 1.5rem; }}
        h1 {{ font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; }}
        p {{ color: var(--text-muted); margin-bottom: 1.5rem; }}
        .alert {{ padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.9rem; }}
        .alert-error {{ background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }}
        .alert-success {{ background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }}
        .alert-warning {{ background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }}
        .form-group {{ margin-bottom: 1.5rem; }}
        label {{ display: block; font-weight: 500; margin-bottom: 0.5rem; font-size: 0.9rem; }}
        input {{ width: 100%; padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; transition: border-color 0.15s; }}
        input:focus {{ outline: none; border-color: var(--primary); box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.2); }}
        input:read-only {{ background: var(--bg); cursor: not-allowed; color: var(--text-muted); }}
        button {{ display: inline-flex; justify-content: center; align-items: center; width: 100%; padding: 0.75rem 1.5rem; background: var(--primary); color: white; border: none; border-radius: 6px; font-size: 1rem; font-weight: 500; cursor: pointer; transition: background 0.15s; }}
        button:hover {{ background: var(--primary-hover); }}
        button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        button.danger {{ background: var(--error); }}
        button.danger:hover {{ background: #b91c1c; }}
        button.secondary {{ background: var(--surface); color: var(--text); border: 1px solid var(--border); margin-top: 0.5rem; }}
        button.secondary:hover {{ background: var(--bg); }}
        .lib-status {{ display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem; padding: 1rem; background: var(--bg); border-radius: 8px; border: 1px solid var(--border); }}
        .status-item {{ display: flex; align-items: center; justify-content: space-between; font-size: 0.9rem; font-weight: 500; }}
        .badge {{ padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
        .badge.ok {{ background: #d1fae5; color: #065f46; }}
        .badge.err {{ background: #fee2e2; color: #991b1b; }}
        .loader {{ display: none; margin-left: 0.5rem; width: 16px; height: 16px; border: 2px solid #ffffff; border-bottom-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; }}
        button.secondary .loader {{ border-color: var(--text); border-bottom-color: transparent; }}
        @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        button.loading .loader {{ display: inline-block; }}
        .hidden {{ display: none !important; }}
        pre {{ background: #1e293b; color: #f8fafc; padding: 1rem; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; margin-top: 1rem; max-height: 200px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>{t_ui_title}</h1>
            <p>{t_ui_subtitle}</p>

            <div id="alert" class="alert hidden"></div>

            <div class="lib-status">
                <div class="status-item">
                    <span>{t_ui_lib_roomba}</span>
                    <span class="badge {lib_cls}">{lib_txt}</span>
                </div>
                <div class="status-item">
                    <span>{t_ui_lib_paho}</span>
                    <span class="badge {paho_cls}">{paho_txt}</span>
                </div>
                {install_btn}
            </div>

            {install_log}

            <div id="enroll-section" class="{enroll_hidden}">
                <div class="alert alert-warning">
                    <strong>{t_ui_step1}</strong> {t_ui_step1_txt}<br>
                    <strong>{t_ui_step2}</strong> {t_ui_step2_txt}<br>
                    <strong>{t_ui_step3}</strong> {t_ui_step3_txt}
                </div>

                <div class="form-group">
                    <label>{t_ui_ip_label}</label>
                    <input type="text" id="ip" value="{current_ip}" readonly>
                </div>

                <button id="btn-enroll" onclick="startEnrollment()">
                    {t_ui_btn_enroll}
                    <div class="loader"></div>
                </button>
            </div>

            <div id="success-section" class="{ok_hidden}">
                <div class="alert alert-success">
                    <strong>{t_ui_cred_saved}</strong><br>
                    {t_ui_cred_saved_txt}
                </div>
                <div class="form-group">
                    <label>BLID</label>
                    <input type="text" value="{blid}" readonly>
                </div>
                <button class="danger" onclick="resetCredentials()">{t_ui_btn_reset}</button>
            </div>
        </div>
    </div>

    <script>
        async function startEnrollment() {{
            const btn = document.getElementById('btn-enroll');
            const alert = document.getElementById('alert');
            const ip = document.getElementById('ip').value;
            
            if (!ip) {{
                showAlert("{t_ui_err_ip_missing}", 'error');
                return;
            }}

            btn.classList.add('loading');
            btn.disabled = true;
            alert.className = 'alert hidden';

            try {{
                const res = await fetch('/api/enroll', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: 'ip=' + encodeURIComponent(ip)
                }});
                const data = await res.json();
                
                if (data.status === 'ok') {{
                    window.location.reload();
                }} else {{
                    showAlert(data.message, 'error');
                }}
            }} catch (e) {{
                showAlert('{t_ui_err_network}', 'error');
            }} finally {{
                btn.classList.remove('loading');
                btn.disabled = false;
            }}
        }}

        async function startInstall() {{
            const btn = document.getElementById('btn-install');
            btn.classList.add('loading');
            btn.disabled = true;
            
            try {{
                await fetch('/api/install', {{ method: 'POST' }});
                window.location.reload();
            }} catch (e) {{
                showAlert("{t_ui_err_network_install}", 'error');
                btn.classList.remove('loading');
                btn.disabled = false;
            }}
        }}

        async function resetCredentials() {{
            if (!confirm('{t_ui_confirm_reset}')) return;
            await fetch('/api/reset', {{ method: 'POST' }});
            window.location.reload();
        }}

        function showAlert(msg, type) {{
            const alert = document.getElementById('alert');
            alert.innerHTML = msg;
            alert.className = 'alert alert-' + type;
        }}
    </script>
</body>
</html>
"""
# ── Classe HTTP réutilisable définie une seule fois au niveau module ──────────
class _ReusableHTTP(HTTPServer):
    allow_reuse_address = True


class _Handler(BaseHTTPRequestHandler):
    # Injectés par EnrollmentServer via sous-classe dynamique
    _cb_credentials = None
    _cb_reset       = None
    _cb_install     = None
    _state          = None
    _lock           = None   # NOUVEAU : verrou partagé
    _debug          = False  # NOUVEAU : flag de log

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        # Copie locale thread-safe de l'état
        with self._lock:
            st = dict(self._state)

        lib_ok    = st.get("lib_ok", False)
        paho_ok   = st.get("paho_ok", False)
        lib_ready = lib_ok and paho_ok
        has_creds = st.get("has_credentials", False)
        log       = st.get("install_log", [])

        install_log = (
            "<pre>" + "\n".join(log) + "</pre>"
        ) if log and not lib_ready else ""
        install_btn = (
            '<button onclick="install()">{t_ui_btn_install_lib}</button>'
        ) if not lib_ready else ""

# Prepare UI translations
        t_ui = {
            't_ui_title': _('ui_title'),
            't_ui_subtitle': _('ui_subtitle'),
            't_ui_lib_roomba': _('ui_lib_roomba'),
            't_ui_lib_paho': _('ui_lib_paho'),
            't_ui_step1': _('ui_step1'),
            't_ui_step1_txt': _('ui_step1_txt'),
            't_ui_step2': _('ui_step2'),
            't_ui_step2_txt': _('ui_step2_txt'),
            't_ui_step3': _('ui_step3'),
            't_ui_step3_txt': _('ui_step3_txt'),
            't_ui_ip_label': _('ui_ip_label'),
            't_ui_btn_enroll': _('ui_btn_enroll'),
            't_ui_success_title': _('ui_success_title'),
            't_ui_success_subtitle': _('ui_success_subtitle'),
            't_ui_btn_close': _('ui_btn_close'),
            't_ui_btn_delete': _('ui_btn_delete'),
            't_ui_btn_install_lib': _('ui_btn_install_lib'),
            't_ui_log_title': _('ui_log_title'),
            't_ui_msg_fetching': _('ui_msg_fetching'),
            't_ui_msg_error': _('ui_msg_error'),
            't_ui_msg_delete_ok': _('ui_msg_delete_ok'),
            't_ui_msg_installing': _('ui_msg_installing'),
            't_ui_cred_saved': _('ui_cred_saved'),
            't_ui_cred_saved_txt': _('ui_cred_saved_txt'),
            't_ui_btn_reset': _('ui_btn_reset'),
            't_ui_err_ip_missing': _('ui_err_ip_missing').replace("'", "\\'"), # Escaping for JS
            't_ui_err_network': _('ui_err_network').replace("'", "\\'"),
            't_ui_err_network_install': _('ui_err_network_install').replace("'", "\\'"),
            't_ui_confirm_reset': _('ui_confirm_reset').replace("'", "\\'")
        }

        html = HTML_TEMPLATE.format(
            current_ip    = st.get("current_ip", ""),
            blid          = st.get("blid", ""),
            lib_cls       = "ok"  if lib_ok    else "err",
            lib_txt       = _("ui_status_ok") if lib_ok    else _("ui_status_err"),
            paho_cls      = "ok"  if paho_ok   else "err",
            paho_txt      = _("ui_status_ok") if paho_ok   else _("ui_status_err"),
            enroll_hidden = "hidden" if has_creds or not lib_ready else "",
            ok_hidden     = "hidden" if not has_creds or not lib_ready else "",
            install_btn   = install_btn,
            install_log   = install_log,
            **t_ui
        )
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        # CORRIGÉ : Content-Length malformé ne plante plus
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self.send_error(400, "Content-Length invalide")
            return

        body   = self.rfile.read(length).decode("utf-8")
        params = parse_qs(body)

        if self.path == "/api/enroll":
            ip = params.get("ip", [""])[0].strip()
            if not ip:
                self._json({"status": "error",
                            "message": _("ui_err_ip_missing_api")})
                return
            # NOUVEAU : validation de l'adresse IP
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                self._json({"status": "error", "message": "Adresse IP invalide."})
                return
            try:
                blid, pwd = _run_enrollment(ip)
                if self._cb_credentials:
                    self._cb_credentials(blid, pwd)
                with self._lock:
                    self._state["has_credentials"] = True
                    self._state["blid"] = blid
                self._json({"status": "ok"})
            except Exception as e:
                self._json({"status": "error", "message": str(e)})

        elif self.path == "/api/install":
            # CORRIGÉ : réponse immédiate + exécution asynchrone
            with self._lock:
                self._state["install_log"] = []
            self._json({"status": "pending"})
            threading.Thread(
                target=self._run_install,
                daemon=True,
                name="EnrollInstall",
            ).start()

        elif self.path == "/api/reset":
            if self._cb_reset:
                self._cb_reset()
            with self._lock:
                self._state["has_credentials"] = False
                self._state["blid"] = ""
            self._json({"status": "ok"})

        else:
            self.send_error(404)

    # ── Installation asynchrone ───────────────────────────────────────────────
    def _run_install(self):
        # CORRIGÉ : import protégé + exécution hors thread HTTP
        try:
            from lib_manager import ensure_all
        except ImportError as e:
            msg = _("ui_err_import", e=e)
            with self._lock:
                self._state["install_log"].append(msg)
            if self._cb_install:
                self._cb_install(False, [msg])
            return

        def progress(msg):
            with self._lock:
                self._state["install_log"].append(msg)

        ok, messages = ensure_all(progress_cb=progress)
        if self._cb_install:
            self._cb_install(ok, messages)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # CORRIGÉ : activable via debug=True au lieu d'être blindé à off
        if self._debug:
            super().log_message(format, *args)


# ── Classe publique ───────────────────────────────────────────────────────────
class EnrollmentServer:
    def __init__(
        self,
        port=8788,
        current_ip="",
        on_credentials=None,
        on_reset=None,
        on_install=None,
        has_credentials=False,
        blid="",
        lib_ok=False,
        paho_ok=False,
        debug=False,          # NOUVEAU
    ):
        self._port = port
        self._srv  = None
        self._lock = threading.Lock()  # NOUVEAU : un seul verrou partagé
        self._state = {
            "has_credentials": has_credentials,
            "blid":            blid,
            "current_ip":      current_ip,
            "lib_ok":          lib_ok,
            "paho_ok":         paho_ok,
            "install_log":     [],
        }

        lock  = self._lock
        state = self._state

        class Handler(_Handler):
            _cb_credentials = on_credentials
            _cb_reset       = on_reset
            _cb_install     = on_install
            _state          = state
            _lock           = lock
            _debug          = debug

        self._HandlerClass = Handler

    # NOUVEAU : property utile pour vérifier l'état
    @property
    def is_running(self) -> bool:
        return self._srv is not None

    def start(self):
        try:
            # CORRIGÉ : _ReusableHTTP défini au niveau module, pas à chaque appel
            self._srv = _ReusableHTTP(("0.0.0.0", self._port), self._HandlerClass)
        except OSError as e:
            raise RuntimeError(f"Port {self._port} indisponible : {e}")
        threading.Thread(
            target=self._srv.serve_forever,
            daemon=True,
            name="EnrollHTTP",
        ).start()

    def stop(self):
        """Arrêt synchrone pour ne pas laisser de thread zombie."""
        if self._srv:
            self._srv.shutdown()
            self._srv.server_close()
            self._srv = None

    def update_lib_status(self, lib_ok: bool, paho_ok: bool):
        with self._lock:
            self._state["lib_ok"]  = lib_ok
            self._state["paho_ok"] = paho_ok

    def set_has_credentials(self, value: bool):
        with self._lock:
            self._state["has_credentials"] = value