"""Ręczny dostęp do kursu (0.4.0): logika bez importu frappe, testy w testy/test_dostep.py.

Powód (decyzja Kuby 17.11, plik 35 pkt 9): przelew po proformie. Po wpłacie menedżer kursów zapisuje osobę z Pulpitu
kursu, a taki zapis ma wygasnąć jak dostęp kupiony w Easycart (warianty: LUCID 365 dni, DIWASS stała data).
"""
from datetime import date, timedelta

from mmlc_lms.easycart.logika import aktywne_zamowienia

DNI_DOSTEPU = 365  # active_days wariantów w Easycart

ZOSTAW = "zostaw"
WYPISZ = "wypisz"
PRZEJMUJE_ZAKUP = "przejmuje_zakup"


def koniec_recznego(dzis: date, koniec_kursu: date | None = None) -> date:
	"""Ostatni dzień dostępu. Kurs ze stałą datą końca (pole LMS Course.mmlc_dostep_do) ma ją dla wszystkich."""
	return koniec_kursu or dzis + timedelta(days=DNI_DOSTEPU)


def zapis_reczny(z_lacznika: bool, z_grupy: bool, kto: str, kursant: str) -> bool:
	"""Datę końca dostaje tylko zapis zrobiony przez kogoś innego niż kursant (menedżer na Pulpicie, administrator).
	Zakup w Easycart wygasza łącznik, a samodzielny zapis na kurs darmowy i zapis przez grupę zostają bez końca."""
	return not z_lacznika and not z_grupy and kto != kursant


def decyzja(dostep_do: date | None, dzis: date, historia) -> str:
	"""Co zrobić z zapisem przy codziennym przeglądzie. `historia` jak w łączniku: (rodzaj, order_id) z dziennika."""
	if not dostep_do or dostep_do >= dzis:
		return ZOSTAW
	if aktywne_zamowienia(historia):
		return PRZEJMUJE_ZAKUP
	return WYPISZ
