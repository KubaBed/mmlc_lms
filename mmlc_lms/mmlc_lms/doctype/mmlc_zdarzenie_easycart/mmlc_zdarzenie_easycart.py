"""Dziennik webhooków Easycart (łącznik w mmlc_lms/easycart). Zapisuje go tylko api.py; służy do diagnozy,
odtwarzania zdarzeń i do sprawdzenia, czy kursant ma inny aktywny dostęp do kursu."""

from frappe.model.document import Document


class MMLCZdarzenieEasycart(Document):
	pass
