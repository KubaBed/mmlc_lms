"""Webhook Easycart -> konto i zapis na kurs we Frappe Learning (decyzja Kuby 21.10, plik 18 sekcja 8).

Adres dla Easycart (pole webhook_url produktu): https://<strona>/api/method/mmlc_lms.easycart.api.webhook
Ustawienia w bazie, doctype "MMLC Ustawienia Easycart" (nie w repo, repo jest publiczne; od 0.2.1 nie w site_config,
bo zapis site_config przez API Frappe Cloud 21.10 zmienił klucz szyfrowania strony):
- klucz_podpisu: klucz z panelu Easycart (Ustawienia sklepu, API i Webhooki)
- konto_lacznika: konto techniczne z rolą Moderator; tylko ono może zapisać kogoś na kurs
  z wyłączonym samodzielnym zapisem (LMS Enrollment.managed_by_caller)
- adres_alarmow: adres na alarmy (zły podpis, nieznany kurs, błąd Frappe)
Pole puste = wartość z site_config (easycart_webhook_key, easycart_lacznik_user, easycart_alarm_email), jak w 0.2.0.
Decyzje i podpis: logika.py (testy w testy/, bez lokalnego Frappe).
"""

import hashlib
import hmac

import frappe
from frappe.rate_limiter import rate_limit

from mmlc_lms.easycart.logika import Stan, Zdarzenie, obsluz

DZIENNIK = "MMLC Zdarzenie Easycart"
USTAWIENIA = "MMLC Ustawienia Easycart"
MAKS_TRESC = 65_000  # bajtów zapisywanych w dzienniku (tylko podpisane zdarzenia; zły podpis zostawia sam skrót)
ALARM_ZLY_PODPIS = "mmlc_lms:easycart:alarm_zly_podpis"


def _ustawienie(pole: str, klucz_site_config: str, haslo: bool = False) -> str | None:
	if haslo:
		wartosc = frappe.get_single(USTAWIENIA).get_password(pole, raise_exception=False)
	else:
		wartosc = frappe.db.get_single_value(USTAWIENIA, pole)
	return wartosc or frappe.conf.get(klucz_site_config)


def _klucz_podpisu() -> str | None:
	return _ustawienie("klucz_podpisu", "easycart_webhook_key", haslo=True)


def _w_punkcie_zapisu(dzialanie):
	"""Nieudane działanie cofa tylko siebie: konto założone wcześniej zostaje, a wpis w dzienniku powstaje."""

	def opakowane(self, z):
		frappe.db.savepoint("easycart")
		try:
			return dzialanie(self, z)
		except Exception:
			frappe.db.rollback(save_point="easycart")
			raise

	return opakowane


class PlatformaFrappe:
	"""Stan i działania na bazie Frappe dla logika.obsluz."""

	def stan(self, z: Zdarzenie) -> Stan:
		historia = frappe.get_all(
			DZIENNIK,
			filters={"email": z.email, "kurs": z.kurs, "status": "ok"},
			fields=["rodzaj", "order_id"],
			order_by="creation asc",
		)
		return Stan(
			konto_istnieje=bool(z.email and frappe.db.exists("User", z.email)),
			zapis_istnieje=bool(z.kurs and frappe.db.exists("LMS Enrollment", {"member": z.email, "course": z.kurs})),
			kurs_istnieje=bool(z.kurs and frappe.db.exists("LMS Course", z.kurs)),
			historia=tuple((h.rodzaj, h.order_id) for h in historia),
		)

	@_w_punkcie_zapisu
	def zaloz_konto(self, z: Zdarzenie):
		# rolę LMS Student dokłada hook Frappe Learning; mail powitalny z szablonu "MMLC powitanie" (od kursy@mmlc.pl)
		frappe.get_doc(
			{
				"doctype": "User",
				"email": z.email,
				"first_name": z.imie or z.email.split("@")[0],
				"last_name": z.nazwisko,
				"user_type": "Website User",
				"language": "pl",
				"send_welcome_email": 1,
			}
		).insert(ignore_permissions=True)

	@_w_punkcie_zapisu
	def zapisz(self, z: Zdarzenie):
		# Notification "MMLC zapis na kurs" wysyła mail o zapisie; flaga: bez daty końca ręcznego dostępu (dostep/api.py)
		zapis = frappe.get_doc(
			{"doctype": "LMS Enrollment", "member": z.email, "course": z.kurs, "member_type": "Student"}
		)
		zapis.flags.mmlc_z_lacznika = True
		zapis.insert(ignore_permissions=True)

	@_w_punkcie_zapisu
	def wypisz(self, z: Zdarzenie):
		# konto, postęp lekcji i wyniki testów zostają; ponowny zapis przywraca historię (próba 20.10)
		nazwa = frappe.db.get_value("LMS Enrollment", {"member": z.email, "course": z.kurs})
		if nazwa:
			frappe.delete_doc("LMS Enrollment", nazwa, ignore_permissions=True)

	def zly_podpis(self, rozmiar: int, skrot: str):
		# w dzienniku sam ślad (rozmiar i skrót), bez treści od nieznanego nadawcy; mail alarmowy najwyżej raz na godzinę
		self.zapisz_w_dzienniku(f"[odrzucone: zły podpis, {rozmiar} bajtów, sha256 {skrot}]".encode(), None, "zly_podpis", "")
		if not frappe.cache.get_value(ALARM_ZLY_PODPIS, expires=True):
			frappe.cache.set_value(ALARM_ZLY_PODPIS, 1, expires_in_sec=3600)
			self.alarm("Webhook Easycart ze złym podpisem (kolejne z tej godziny tylko w dzienniku)")

	def alarm(self, tekst: str):
		frappe.log_error(title="Łącznik Easycart", message=tekst)
		adres = _ustawienie("adres_alarmow", "easycart_alarm_email")
		if adres:
			frappe.sendmail(recipients=[adres], subject=f"Łącznik Easycart: {tekst[:120]}", message=tekst)

	def zapisz_w_dzienniku(self, surowa: bytes, z: Zdarzenie | None, status: str, opis: str):
		frappe.get_doc(
			{
				"doctype": DZIENNIK,
				"rodzaj": z.rodzaj if z else None,
				"order_id": z.order_id if z else None,
				"email": z.email if z else None,
				"kurs": z.kurs if z else None,
				"status": status,
				"opis": opis,
				"tresc": surowa[:MAKS_TRESC].decode("utf-8", "replace"),
			}
		).insert(ignore_permissions=True)


def _obsluz_jako_lacznik(surowa: bytes, naglowek: str | None, klucz: str):
	uzytkownik = frappe.session.user
	frappe.set_user(_ustawienie("konto_lacznika", "easycart_lacznik_user") or "Administrator")
	try:
		return obsluz(surowa, naglowek, klucz, PlatformaFrappe())
	finally:
		frappe.set_user(uzytkownik)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=120, seconds=60)
def webhook():
	klucz = _klucz_podpisu()
	if not klucz:
		frappe.local.response.http_status_code = 503
		return {"status": "brak_konfiguracji"}
	wynik = _obsluz_jako_lacznik(
		frappe.request.get_data(), frappe.request.headers.get("X-Webhook-Signature"), klucz
	)
	frappe.local.response.http_status_code = wynik.kod
	return {"status": wynik.status}


@frappe.whitelist(methods=["POST"])
def odtworz(nazwa: str):
	"""Ponowne przetworzenie zdarzenia z dziennika (np. po awarii, scenariusz S8). Tylko System Manager."""
	frappe.only_for("System Manager")
	klucz = _klucz_podpisu()
	wpis = frappe.db.get_value(DZIENNIK, nazwa, ["status", "tresc"], as_dict=True)
	if wpis.status == "zly_podpis":
		frappe.throw("Zdarzenia ze złym podpisem nie odtwarzamy: nie przyszło od Easycart.")
	surowa = wpis.tresc.encode()
	podpis = hmac.new(klucz.encode(), surowa, hashlib.sha256).hexdigest()
	wynik = _obsluz_jako_lacznik(surowa, podpis, klucz)
	return {"kod": wynik.kod, "status": wynik.status, "opis": wynik.opis}
