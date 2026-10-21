"""Webhook Easycart -> konto i zapis na kurs we Frappe Learning (decyzja Kuby 21.10, plik 18 sekcja 8).

Adres dla Easycart (pole webhook_url produktu): https://<strona>/api/method/mmlc_lms.easycart.api.webhook
Ustawienia w site_config strony (nie w repo, repo jest publiczne):
- easycart_webhook_key: klucz podpisu z panelu Easycart (Ustawienia sklepu, API i Webhooki)
- easycart_lacznik_user: konto techniczne z rolą Moderator; tylko ono może zapisać kogoś na kurs
  z wyłączonym samodzielnym zapisem (LMS Enrollment.managed_by_caller)
- easycart_alarm_email: adres na alarmy (zły podpis, nieznany kurs, błąd Frappe)
Decyzje i podpis: logika.py (testy w testy/, bez lokalnego Frappe).
"""

import hashlib
import hmac

import frappe
from frappe.rate_limiter import rate_limit

from mmlc_lms.easycart.logika import Stan, Zdarzenie, obsluz

DZIENNIK = "MMLC Zdarzenie Easycart"
MAKS_TRESC = 65_000  # bajtów zapisywanych w dzienniku (obcy, niepodpisany ruch też tu trafia)


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
		# Notification "MMLC zapis na kurs" wysyła mail o zapisie
		frappe.get_doc(
			{"doctype": "LMS Enrollment", "member": z.email, "course": z.kurs, "member_type": "Student"}
		).insert(ignore_permissions=True)

	@_w_punkcie_zapisu
	def wypisz(self, z: Zdarzenie):
		# konto, postęp lekcji i wyniki testów zostają; ponowny zapis przywraca historię (próba 20.10)
		nazwa = frappe.db.get_value("LMS Enrollment", {"member": z.email, "course": z.kurs})
		if nazwa:
			frappe.delete_doc("LMS Enrollment", nazwa, ignore_permissions=True)

	def alarm(self, tekst: str):
		frappe.log_error(title="Łącznik Easycart", message=tekst)
		adres = frappe.conf.get("easycart_alarm_email")
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
	frappe.set_user(frappe.conf.get("easycart_lacznik_user") or "Administrator")
	try:
		return obsluz(surowa, naglowek, klucz, PlatformaFrappe())
	finally:
		frappe.set_user(uzytkownik)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=120, seconds=60)
def webhook():
	klucz = frappe.conf.get("easycart_webhook_key")
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
	klucz = frappe.conf.get("easycart_webhook_key")
	wpis = frappe.db.get_value(DZIENNIK, nazwa, ["status", "tresc"], as_dict=True)
	if wpis.status == "zly_podpis":
		frappe.throw("Zdarzenia ze złym podpisem nie odtwarzamy: nie przyszło od Easycart.")
	surowa = wpis.tresc.encode()
	podpis = hmac.new(klucz.encode(), surowa, hashlib.sha256).hexdigest()
	wynik = _obsluz_jako_lacznik(surowa, podpis, klucz)
	return {"kod": wynik.kod, "status": wynik.status, "opis": wynik.opis}
