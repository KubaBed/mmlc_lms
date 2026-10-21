"""Łącznik Easycart -> Frappe Learning: logika bez importu frappe (testy w testy/, pytest bez lokalnego Frappe).

Decyzja Kuby 21.10 (MMLC/Strona www/18-plan-testow-sciezki-kursu.md, sekcja 8): webhook Easycart trafia wprost
do Frappe, bez Zapiera. Tu tylko podpis i decyzje; zapis do bazy robi api.py.
"""
from dataclasses import dataclass
import hashlib
import hmac
import json


def podpis_ok(surowa_tresc: bytes, naglowek: str | None, klucz: str) -> bool:
	"""X-Webhook-Signature = HMAC-SHA256 (hex) z surowej treści. Liczymy z bajtów, nie z ponownie złożonego JSON-a:
	przykład JS w dokumentacji Easytools robi JSON.stringify i potrafi zmienić polskie znaki."""
	if not naglowek:
		return False
	oczekiwany = hmac.new(klucz.encode(), surowa_tresc, hashlib.sha256).hexdigest()
	return hmac.compare_digest(oczekiwany, naglowek.strip().lower())


@dataclass(frozen=True)
class Zdarzenie:
	rodzaj: str
	order_id: str
	email: str
	imie: str
	nazwisko: str
	kurs: str | None  # nazwa kursu we Frappe = custom_id wariantu w Easycart
	price_id: str = ""


def odczytaj(dane: dict) -> Zdarzenie:
	"""Dostęp dostaje `assignee` (przy zakupie dla kogoś to nie kupujący). Bez `assignee`: kupujący."""
	osoba = dane.get("assignee") or {
		"email": dane.get("customer_email"),
		"first_name": dane.get("customer_first_name"),
		"last_name": dane.get("customer_last_name"),
	}
	return Zdarzenie(
		rodzaj=dane.get("event", ""),
		order_id=str(dane.get("order_id", "")),
		email=(osoba.get("email") or "").strip().lower(),
		imie=(osoba.get("first_name") or "").strip(),
		nazwisko=(osoba.get("last_name") or "").strip(),
		kurs=dane.get("price_custom_id"),
		price_id=dane.get("price_id") or "",
	)


@dataclass(frozen=True)
class Stan:
	konto_istnieje: bool
	zapis_istnieje: bool
	kurs_istnieje: bool = True
	# wcześniejsze zdarzenia z dziennika dla tego e-maila i kursu, od najstarszego: (rodzaj, order_id)
	historia: tuple[tuple[str, str], ...] = ()


NADANIE = "product_assigned"
WYGASNIECIE = "product_access_expired"


def aktywne_zamowienia(historia) -> set[str]:
	aktywne = set()
	for rodzaj, order_id in historia:
		if rodzaj == NADANIE:
			aktywne.add(order_id)
		elif rodzaj == WYGASNIECIE:
			aktywne.discard(order_id)
	return aktywne


def zaplanuj(z: Zdarzenie, stan: Stan) -> list[tuple]:
	"""Lista działań do wykonania: ("zaloz_konto",), ("zapisz",), ("wypisz",), ("alarm", tekst). Pusta = nic do zrobienia."""
	if z.rodzaj not in (NADANIE, WYGASNIECIE):
		return []
	if not z.kurs:
		return [("alarm", f"Wariant {z.price_id} nie ma custom_id z nazwą kursu we Frappe")]
	if not stan.kurs_istnieje:
		return [("alarm", f"Kursu {z.kurs} nie ma we Frappe")]
	if z.rodzaj == WYGASNIECIE:
		# kursant mógł kupić ten sam kurs drugi raz; wtedy wygasa tylko starszy dostęp, a zapis zostaje
		inne = aktywne_zamowienia(stan.historia) - {z.order_id}
		return [("wypisz",)] if stan.zapis_istnieje and not inne else []
	dzialania = []
	if not stan.konto_istnieje:
		dzialania.append(("zaloz_konto",))
	if not stan.zapis_istnieje:
		dzialania.append(("zapisz",))
	return dzialania


@dataclass(frozen=True)
class Wynik:
	kod: int  # odpowiedź HTTP dla Easycart
	status: str  # ok, pominiete, zly_podpis, blad
	opis: str = ""


def obsluz(surowa_tresc: bytes, naglowek: str | None, klucz: str, platforma) -> Wynik:
	"""Cały webhook: podpis, odczyt, stan, działania, dziennik. `platforma` to Frappe (api.py) albo atrapa w testach."""
	if not podpis_ok(surowa_tresc, naglowek, klucz):
		platforma.alarm("Webhook Easycart ze złym podpisem")
		platforma.zapisz_w_dzienniku(surowa_tresc, None, "zly_podpis", "")
		return Wynik(401, "zly_podpis")
	try:
		z = odczytaj(json.loads(surowa_tresc))
	except ValueError as e:
		platforma.zapisz_w_dzienniku(surowa_tresc, None, "blad", f"Treść nie jest JSON-em: {e}")
		return Wynik(400, "blad", "Treść nie jest JSON-em")
	if z.rodzaj not in (NADANIE, WYGASNIECIE):
		platforma.zapisz_w_dzienniku(surowa_tresc, z, "pominiete", "")
		return Wynik(200, "pominiete")
	status, opis = "ok", ""
	try:
		for dzialanie in zaplanuj(z, platforma.stan(z)):
			if dzialanie[0] == "alarm":
				status, opis = "pominiete", f"{dzialanie[1]} ({z.email}, zamówienie {z.order_id})"
				platforma.alarm(opis)
			else:
				getattr(platforma, dzialanie[0])(z)
	except Exception as e:  # noqa: BLE001 - każdy błąd Frappe ma trafić do dziennika i alarmu, a Easycart dostaje 500
		opis = f"{e} ({z.email}, zamówienie {z.order_id})"
		platforma.alarm(f"Błąd łącznika Easycart: {opis}")
		platforma.zapisz_w_dzienniku(surowa_tresc, z, "blad", opis)
		return Wynik(500, "blad", opis)
	# "ok" także bez działań (ponowny zakup): dziennik musi znać każde zamówienie, żeby wygaśnięcie starszego
	# dostępu nie wypisało kursanta z kursu (zaplanuj, historia)
	platforma.zapisz_w_dzienniku(surowa_tresc, z, status, opis)
	return Wynik(200, status, opis)
