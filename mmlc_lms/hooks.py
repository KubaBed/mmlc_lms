app_name = "mmlc_lms"
app_title = "MMLC LMS"
app_publisher = "Aspiratio dla MMLC"
app_description = "Wygląd marki MMLC dla Frappe Learning (widok kursanta /lms)"
app_email = "jakub@workshift.pl"
app_license = "mit"

required_apps = ["lms"]

# Strona /lms (aplikacja Vue z Frappe Learning) ma własny szablon HTML, który nie wczytuje motywu WWW
# ani web_include_css. Dlatego arkusz MMLC dopisujemy do gotowej odpowiedzi HTML.
after_request = ["mmlc_lms.inject.after_request"]

# 0.3.0: nowy kurs bez samodzielnego zapisu (mmlc_lms/kurs.py)
# 0.4.0: ręczny zapis z Pulpitu dostaje datę końca, którą zmienia tylko menedżer kursu (mmlc_lms/dostep/)
doc_events = {
	"LMS Course": {"before_insert": "mmlc_lms.kurs.wylacz_samodzielny_zapis"},
	"LMS Enrollment": {
		"before_insert": "mmlc_lms.dostep.api.ustaw_koniec",
		"validate": "mmlc_lms.dostep.api.pilnuj_daty",
	},
}

# 0.4.0: codziennie wypisuje ręczne zapisy po dacie końca
scheduler_events = {"daily": ["mmlc_lms.dostep.api.wygas_reczne"]}
