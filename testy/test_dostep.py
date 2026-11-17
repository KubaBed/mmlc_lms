"""Ręczny dostęp do kursu (0.4.0): data końca, kto dostaje datę, kiedy zapis wygasa. Wartości oczekiwane wpisane ręcznie."""
from datetime import date

from mmlc_lms.dostep.logika import (
	PRZEJMUJE_ZAKUP,
	WYPISZ,
	ZOSTAW,
	decyzja,
	koniec_recznego,
	zapis_reczny,
)

# data końca: jak warianty w Easycart (LUCID 365 dni, DIWASS stała data)

def test_bez_stalej_daty_dostep_trwa_365_dni():
	assert koniec_recznego(date(2026, 11, 18)) == date(2027, 11, 18)


def test_rok_przestepny_liczy_dni_a_nie_miesiace():
	assert koniec_recznego(date(2027, 3, 1)) == date(2028, 2, 29)


def test_stala_data_kursu_wygrywa():
	assert koniec_recznego(date(2026, 11, 18), date(2027, 12, 10)) == date(2027, 12, 10)


# kto dostaje datę końca

def test_menedzer_zapisuje_kogos_z_pulpitu():
	assert zapis_reczny(z_lacznika=False, z_grupy=False, kto="ola@mmlc.pl", kursant="jan@example.com")


def test_zapis_z_lacznika_easycart_bez_daty():
	# dostępem z zakupu rządzi Easycart (product_access_expired), nie nasz harmonogram
	assert not zapis_reczny(z_lacznika=True, z_grupy=False, kto="lacznik.easycart@example.com", kursant="jan@example.com")


def test_samodzielny_zapis_na_kurs_darmowy_bez_daty():
	assert not zapis_reczny(z_lacznika=False, z_grupy=False, kto="jan@example.com", kursant="jan@example.com")


def test_zapis_przez_grupe_bez_daty():
	assert not zapis_reczny(z_lacznika=False, z_grupy=True, kto="ola@mmlc.pl", kursant="jan@example.com")


# wygaśnięcie (codziennie)

DZIS = date(2027, 11, 19)


def test_ostatni_dzien_dostepu_jeszcze_trwa():
	assert decyzja(date(2027, 11, 19), DZIS, historia=()) == ZOSTAW


def test_dzien_po_koncu_wypisuje():
	assert decyzja(date(2027, 11, 18), DZIS, historia=()) == WYPISZ


def test_zapis_bez_daty_nie_wygasa():
	# zapisy sprzed 0.4.0 i zapisy z łącznika
	assert decyzja(None, DZIS, historia=()) == ZOSTAW


def test_kupiony_pozniej_dostep_przejmuje_zapis():
	# osoba z ręcznym zapisem kupiła kurs w Easycart: łącznik nie zakłada drugiego zapisu, więc data ręczna nie może jej wypisać
	historia = (("product_assigned", "500001"),)
	assert decyzja(date(2027, 11, 18), DZIS, historia) == PRZEJMUJE_ZAKUP


def test_wygasly_zakup_nie_chroni_recznego_zapisu():
	historia = (("product_assigned", "500001"), ("product_access_expired", "500001"))
	assert decyzja(date(2027, 11, 18), DZIS, historia) == WYPISZ


def test_wpisy_recznego_wypisu_w_dzienniku_nie_licza_sie_jako_zakup():
	historia = (("reczny_wypis", ""), ("reczne_wygasniecie", ""))
	assert decyzja(date(2027, 11, 18), DZIS, historia) == WYPISZ
