"""Ustawienia łącznika Easycart (mmlc_lms/easycart/api.py). W bazie, nie w site_config: zapis site_config przez
API Frappe Cloud 21.10 zmienił klucz szyfrowania strony (plik 18, sekcja 9.2)."""

from frappe.model.document import Document


class MMLCUstawieniaEasycart(Document):
	pass
