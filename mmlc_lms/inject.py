"""Dopisuje wygląd MMLC do strony /lms (Frappe Learning) w odpowiedzi HTML serwera."""

import frappe

VERSION = "0.1.1"

# Przed skryptem Frappe Learning, który ustawia motyw z ustawień systemu: domyślnie jasny,
# chyba że kursant sam wybrał motyw w aplikacji.
THEME_DEFAULT = (
	"<script>try{if(!localStorage.getItem('themePreference')&&!localStorage.getItem('theme'))"
	"{localStorage.setItem('themePreference','light')}}catch(e){}</script>"
)
HEAD_END = (
	f'<link rel="stylesheet" href="/assets/mmlc_lms/css/mmlc-lms.css?v={VERSION}">'
	f'<script defer src="/assets/mmlc_lms/js/mmlc-lms.js?v={VERSION}"></script>'
)
MARKER = "/assets/mmlc_lms/css/mmlc-lms.css"


def _lms_path() -> str:
	try:
		from lms.lms.utils import get_lms_path

		return (get_lms_path() or "lms").strip("/")
	except Exception:
		return "lms"


def after_request(response, request):
	path = (request.path or "").rstrip("/")
	base = "/" + _lms_path()
	if path != base and not path.startswith(base + "/"):
		return
	if response.direct_passthrough or response.mimetype != "text/html" or response.status_code != 200:
		return

	html = response.get_data(as_text=True)
	if MARKER in html or "<head>" not in html or "</head>" not in html:
		return

	html = html.replace("<head>", "<head>" + THEME_DEFAULT, 1)
	html = html.replace("</head>", HEAD_END + "</head>", 1)
	response.set_data(html)
