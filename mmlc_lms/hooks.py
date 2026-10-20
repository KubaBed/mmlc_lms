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
