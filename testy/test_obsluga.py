"""Szew 3: cały webhook od surowej treści do kodu odpowiedzi. Frappe zastępuje atrapa w pamięci (granica systemu)."""
import hashlib
import hmac
import json
import pathlib

from mmlc_lms.easycart.logika import Stan, obsluz

KLUCZ = "klucz-testowy"
PAYLOAD = json.loads((pathlib.Path(__file__).with_name("payloady") / "product_assigned.json").read_text())


def podpisz(tresc: bytes) -> str:
	return hmac.new(KLUCZ.encode(), tresc, hashlib.sha256).hexdigest()


class Atrapa:
	"""Platforma kursowa w pamięci: konta, zapisy, dziennik, alarmy. `awaria` = nazwa działania, które rzuci wyjątek."""

	def __init__(self, kursy=("test-lacznik-a",)):
		self.kursy, self.konta, self.zapisy = set(kursy), [], []
		self.dziennik, self.alarmy, self.awaria = [], [], None

	def stan(self, z):
		return Stan(konto_istnieje=z.email in self.konta, zapis_istnieje=(z.email, z.kurs) in self.zapisy,
					kurs_istnieje=z.kurs in self.kursy,
					historia=tuple((w["rodzaj"], w["order_id"]) for w in self.dziennik
                                   if w["status"] == "ok" and (w["email"], w["kurs"]) == (z.email, z.kurs)))

	def _moze(self, nazwa):
		if self.awaria == nazwa:
			raise RuntimeError(f"Frappe: {nazwa} nie przeszło")

	def zaloz_konto(self, z):
		self._moze("zaloz_konto")
		self.konta.append(z.email)

	def zapisz(self, z):
		self._moze("zapisz")
		self.zapisy.append((z.email, z.kurs))

	def wypisz(self, z):
		self._moze("wypisz")
		self.zapisy.remove((z.email, z.kurs))

	def alarm(self, tekst):
		self.alarmy.append(tekst)

	def zly_podpis(self, rozmiar, skrot):
		# jak api.py: wpis bez treści, alarm tylko pierwszy raz (w api.py: raz na godzinę przez cache)
		self.dziennik.append({"surowa": f"{rozmiar} {skrot}", "rodzaj": None, "order_id": None, "email": None, "kurs": None,
                              "status": "zly_podpis", "opis": ""})
		if not getattr(self, "_alarm_podpisu", False):
			self._alarm_podpisu = True
			self.alarmy.append("Webhook Easycart ze złym podpisem")

	def zapisz_w_dzienniku(self, surowa, z, status, opis):
		self.dziennik.append({"surowa": surowa, "rodzaj": z.rodzaj if z else None, "order_id": z.order_id if z else None,
                              "email": z.email if z else None, "kurs": z.kurs if z else None,
                              "status": status, "opis": opis})


def wyslij(atrapa, dane=None, podpis=None):
	tresc = json.dumps(dane or PAYLOAD, ensure_ascii=False).encode()
	return obsluz(tresc, podpis if podpis is not None else podpisz(tresc), KLUCZ, atrapa)


def test_nowy_kursant_konto_zapis_dziennik_i_200():
	a = Atrapa()
	assert wyslij(a).kod == 200
	assert (a.konta, a.zapisy) == (["jan.kowalski@example.com"], [("jan.kowalski@example.com", "test-lacznik-a")])
	assert [w["status"] for w in a.dziennik] == ["ok"]


def test_zly_podpis_401_nic_nie_powstaje_alarm_i_wpis():
	a = Atrapa()
	w = wyslij(a, podpis="0" * 64)
	assert (w.kod, w.status) == (401, "zly_podpis")
	assert (a.konta, a.zapisy) == ([], [])
	assert a.alarmy == ["Webhook Easycart ze złym podpisem"]
	assert [d["status"] for d in a.dziennik] == ["zly_podpis"]


def test_nieznany_kurs_200_alarm_bez_zmian():
	a = Atrapa(kursy=())
	w = wyslij(a)
	assert (w.kod, w.status) == (200, "pominiete")
	assert a.alarmy == ["Kursu test-lacznik-a nie ma we Frappe (jan.kowalski@example.com, zamówienie 500001)"]
	assert (a.konta, a.zapisy) == ([], [])


def test_zdarzenie_bez_dzialan_200_pominiete():
	a = Atrapa()
	w = wyslij(a, dict(PAYLOAD, event="single_product_bought"))
	assert (w.kod, w.status, a.alarmy) == (200, "pominiete", [])


def test_awaria_zapisu_500_blad_alarm_potem_ponowienie_bez_duplikatow():
	a = Atrapa()
	a.awaria = "zapisz"
	w = wyslij(a)
	assert (w.kod, w.status) == (500, "blad")
	assert a.alarmy == ["Błąd łącznika Easycart: Frappe: zapisz nie przeszło (jan.kowalski@example.com, zamówienie 500001)"]
	assert a.konta == ["jan.kowalski@example.com"] and a.zapisy == []

	a.awaria = None  # Easycart ponawia albo Kuba odtwarza zdarzenie z dziennika
	assert wyslij(a).kod == 200
	assert a.konta == ["jan.kowalski@example.com"]  # jedno konto, jeden mail powitalny
	assert a.zapisy == [("jan.kowalski@example.com", "test-lacznik-a")]
	assert [d["status"] for d in a.dziennik] == ["blad", "ok"]


def test_dwa_zakupy_wygasa_starszy_zapis_zostaje_wygasa_nowszy_wypis():
	a = Atrapa()
	wyslij(a)
	wyslij(a, dict(PAYLOAD, order_id=500007))
	wyslij(a, dict(PAYLOAD, event="product_access_expired", order_id=500001))
	assert a.zapisy == [("jan.kowalski@example.com", "test-lacznik-a")]
	wyslij(a, dict(PAYLOAD, event="product_access_expired", order_id=500007))
	assert a.zapisy == [] and a.konta == ["jan.kowalski@example.com"]


def test_podpisana_tresc_ktora_nie_jest_jsonem_400():
	a = Atrapa()
	tresc = b"to nie json"
	w = obsluz(tresc, podpisz(tresc), KLUCZ, a)
	assert (w.kod, w.status) == (400, "blad")
	assert [d["status"] for d in a.dziennik] == ["blad"]


def test_dwa_zle_podpisy_jeden_alarm_i_brak_tresci_w_dzienniku():
	a = Atrapa()
	wyslij(a, podpis="0" * 64)
	wyslij(a, dict(PAYLOAD, customer_email="tajne@example.com"), podpis="1" * 64)
	assert a.alarmy == ["Webhook Easycart ze złym podpisem"]
	assert [d["status"] for d in a.dziennik] == ["zly_podpis", "zly_podpis"]
	assert all("example.com" not in d["surowa"] for d in a.dziennik)


def test_nadanie_po_wygasnieciu_tego_samego_zamowienia_nie_przywraca_dostepu():
	a = Atrapa()
	wyslij(a)
	wyslij(a, dict(PAYLOAD, event="product_access_expired"))
	assert a.zapisy == []
	w = wyslij(a)  # ponowienie Easycart albo ręczne odtworzenie
	assert (w.kod, w.status) == (200, "pominiete")
	assert a.zapisy == [] and len(a.alarmy) == 1
	wyslij(a, dict(PAYLOAD, order_id=500007))  # nowy zakup działa normalnie
	assert a.zapisy == [("jan.kowalski@example.com", "test-lacznik-a")]


def test_wygasniecie_cudzego_zamowienia_nie_wypisuje_zapisu_recznego():
	a = Atrapa()
	a.konta.append("jan.kowalski@example.com")
	a.zapisy.append(("jan.kowalski@example.com", "test-lacznik-a"))  # zapis ręczny, bez wpisu w dzienniku
	w = wyslij(a, dict(PAYLOAD, event="product_access_expired", order_id=600001))
	assert (w.kod, w.status) == (200, "pominiete")
	assert a.zapisy == [("jan.kowalski@example.com", "test-lacznik-a")] and len(a.alarmy) == 1
