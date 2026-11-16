"""Zasady dla kursów Frappe Learning w MMLC (0.3.0)."""


def wylacz_samodzielny_zapis(doc, method=None):
	"""Nowy kurs bez samodzielnego zapisu: dostęp daje tylko zakup w Easycart (łącznik) albo menedżer.

	Frappe Learning zakłada kurs z `disable_self_learning` = 0, więc jedno przeoczenie otwierało kurs dla każdego
	zalogowanego (uwagi z 20.10, pkt 1). Kurs darmowy z samodzielnym zapisem nadal da się włączyć po zapisie kursu.
	"""
	doc.disable_self_learning = 1
