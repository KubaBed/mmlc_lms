"""Szew 2: co zrobić z webhookiem Easycart przy danym stanie platformy. Wartości oczekiwane wpisane ręcznie."""
import json
import pathlib

from mmlc_lms.easycart.logika import Stan, odczytaj, zaplanuj

PAYLOADY = pathlib.Path(__file__).with_name("payloady")


def payload(nazwa="product_assigned", **zmiany):
	d = json.loads((PAYLOADY / f"{nazwa}.json").read_text())
	d.update(zmiany)
	return d


def test_nowy_kursant_dostaje_konto_i_zapis():
	z = odczytaj(payload())
	assert (z.email, z.imie, z.nazwisko, z.kurs, z.order_id) == (
		"jan.kowalski@example.com", "Jan", "Kowalski", "test-lacznik-a", "500001")
	assert zaplanuj(z, Stan(konto_istnieje=False, zapis_istnieje=False)) == [("zaloz_konto",), ("zapisz",)]


def test_kursant_z_kontem_dostaje_tylko_zapis():
	assert zaplanuj(odczytaj(payload()), Stan(konto_istnieje=True, zapis_istnieje=False)) == [("zapisz",)]


def test_ponowny_zakup_tego_samego_kursu_nic_nie_robi():
	# bez drugiego zapisu nie ma drugiego maila "Zapis na kurs"
	assert zaplanuj(odczytaj(payload()), Stan(konto_istnieje=True, zapis_istnieje=True)) == []


def test_zakup_dla_kogos_innego_dotyczy_osoby_z_dostepem():
	z = odczytaj(payload(order_delegated=True, assignee={
		"id": 100002, "name": "Anna Nowak", "first_name": "Anna", "last_name": "Nowak", "email": "anna.nowak@example.com"}))
	assert (z.email, z.imie, z.nazwisko) == ("anna.nowak@example.com", "Anna", "Nowak")


def test_wielkie_litery_i_spacje_w_adresie():
	z = odczytaj(payload(assignee={"first_name": "Jan", "last_name": "Kowalski", "email": " Jan.Kowalski+MMLC@Example.com "}))
	assert z.email == "jan.kowalski+mmlc@example.com"


def test_bez_assignee_dostep_dla_kupujacego():
	d = payload()
	del d["assignee"]
	z = odczytaj(d)
	assert (z.email, z.imie, z.nazwisko) == ("jan.kowalski@example.com", "Jan", "Kowalski")


def test_wariant_bez_custom_id_to_alarm():
	z = odczytaj(payload(price_custom_id=None))
	assert zaplanuj(z, Stan(konto_istnieje=False, zapis_istnieje=False)) == [
		("alarm", "Wariant price_XXXXXXXXXXXX nie ma custom_id z nazwą kursu we Frappe")]


def test_kursu_nie_ma_we_frappe_to_alarm():
	z = odczytaj(payload(price_custom_id="kurs-ktorego-nie-ma"))
	assert zaplanuj(z, Stan(konto_istnieje=False, zapis_istnieje=False, kurs_istnieje=False)) == [
		("alarm", "Kursu kurs-ktorego-nie-ma nie ma we Frappe")]


def test_inne_zdarzenia_sa_pomijane():
	for rodzaj in ("single_product_bought", "product_access_expiring", "customer_data_changed"):
		assert zaplanuj(odczytaj(payload(event=rodzaj)), Stan(konto_istnieje=False, zapis_istnieje=False)) == []


def wygasniecie(order_id=500001):
	return odczytaj(payload(event="product_access_expired", order_id=order_id))


def test_wygasniecie_wypisuje_z_kursu_a_konto_zostaje():
	stan = Stan(konto_istnieje=True, zapis_istnieje=True, historia=(("product_assigned", "500001"),))
	assert zaplanuj(wygasniecie(), stan) == [("wypisz",)]


def test_wygasniecie_bez_zapisu_nic_nie_robi():
	assert zaplanuj(wygasniecie(), Stan(konto_istnieje=True, zapis_istnieje=False)) == []


def test_wygasniecie_starszego_dostepu_gdy_drugi_jest_aktywny():
	# S3b: dwa zakupy tego samego kursu, wygasa pierwszy; drugi trwa, więc zapis zostaje
	historia = (("product_assigned", "500001"), ("product_assigned", "500007"))
	assert zaplanuj(wygasniecie(500001), Stan(konto_istnieje=True, zapis_istnieje=True, historia=historia)) == []


def test_wygasniecie_ostatniego_z_dwoch_dostepow():
	historia = (("product_assigned", "500001"), ("product_assigned", "500007"), ("product_access_expired", "500001"))
	assert zaplanuj(wygasniecie(500007), Stan(konto_istnieje=True, zapis_istnieje=True, historia=historia)) == [("wypisz",)]
