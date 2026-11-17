"""Ręczny dostęp do kursu (0.4.0): data końca zapisu z Pulpitu, codzienne wygaszanie i przycisk „Wypisz z kursu”.

- `ustaw_koniec` (LMS Enrollment, before_insert): zapis zrobiony przez menedżera dostaje `mmlc_dostep_do`
  (dziś + 365 dni albo stała data kursu z LMS Course.mmlc_dostep_do). Wartość podana przy zapisie wygrywa.
- `pilnuj_daty` (LMS Enrollment, validate): datę zmienia tylko menedżer kursu, nie kursant.
- `wygas_reczne` (codziennie): wypisuje zapisy po dacie końca; konto, postęp i wyniki zostają.
- `stan`, `wypisz`: dla przycisku w oknie „Postępy kursanta” na Pulpicie kursu (public/js/mmlc-lms.js).
Każdy wypis trafia do dziennika „MMLC Zdarzenie Easycart” (rodzaje: reczny_wypis, reczne_wygasniecie, reczny_przejety).
"""

import frappe
from frappe.utils import formatdate, getdate, today

from mmlc_lms.dostep.logika import (
	PRZEJMUJE_ZAKUP,
	WYPISZ,
	decyzja,
	koniec_recznego,
	zapis_reczny,
)
from mmlc_lms.easycart.api import DZIENNIK, PlatformaFrappe
from mmlc_lms.easycart.logika import Zdarzenie, aktywne_zamowienia

POLE = "mmlc_dostep_do"


def _historia(email: str, kurs: str) -> tuple:
	wpisy = frappe.get_all(
		DZIENNIK,
		filters={"email": email, "kurs": kurs, "status": "ok"},
		fields=["rodzaj", "order_id"],
		order_by="creation asc",
	)
	return tuple((w.rodzaj, w.order_id) for w in wpisy)


def _do_dziennika(rodzaj: str, email: str, kurs: str, opis: str):
	z = Zdarzenie(rodzaj=rodzaj, order_id="", email=email, imie="", nazwisko="", kurs=kurs)
	PlatformaFrappe().zapisz_w_dzienniku(b"", z, "ok", opis)


def _menedzer(kurs: str) -> bool:
	from lms.lms.permissions import can_author_course

	return can_author_course(kurs, user=frappe.session.user)


def ustaw_koniec(doc, method=None):
	if doc.get(POLE):
		return
	if not zapis_reczny(
		z_lacznika=bool(doc.flags.mmlc_z_lacznika),
		z_grupy=bool(doc.enrollment_from_batch),
		kto=frappe.session.user,
		kursant=doc.member,
	):
		return
	koniec_kursu = frappe.db.get_value("LMS Course", doc.course, POLE)
	doc.set(POLE, koniec_recznego(getdate(today()), getdate(koniec_kursu) if koniec_kursu else None))


def pilnuj_daty(doc, method=None):
	if doc.is_new() or _menedzer(doc.course):
		return
	doc.set(POLE, frappe.db.get_value("LMS Enrollment", doc.name, POLE))


def wygas_reczne():
	dzis = getdate(today())
	zapisy = frappe.get_all(
		"LMS Enrollment", filters={POLE: ["<", dzis]}, fields=["name", "member", "course", POLE]
	)
	for z in zapisy:
		koniec = getdate(z.get(POLE))
		try:
			co = decyzja(koniec, dzis, _historia(z.member, z.course))
			if co == WYPISZ:
				frappe.delete_doc("LMS Enrollment", z.name, ignore_permissions=True)
				_do_dziennika("reczne_wygasniecie", z.member, z.course, f"Dostęp ręczny do {formatdate(koniec)} minął")
			elif co == PRZEJMUJE_ZAKUP:
				frappe.db.set_value("LMS Enrollment", z.name, POLE, None, update_modified=False)
				_do_dziennika("reczny_przejety", z.member, z.course, "Osoba kupiła kurs w Easycart, data ręczna usunięta")
			frappe.db.commit()
		except Exception:  # noqa: BLE001 - jeden błąd nie może zatrzymać wygaszania pozostałych
			frappe.db.rollback()
			frappe.log_error(title="Wygaszanie ręcznych zapisów", message=f"{z.member}, {z.course}\n{frappe.get_traceback()}")


@frappe.whitelist()
def stan(course: str, member: str) -> dict:
	"""Data końca i źródło dostępu do pokazania w oknie „Postępy kursanta”."""
	if not _menedzer(course):
		frappe.throw("Brak uprawnień do tego kursu.", frappe.PermissionError)
	dostep_do = frappe.db.get_value("LMS Enrollment", {"course": course, "member": member}, POLE)
	return {
		"dostep_do": formatdate(dostep_do, "dd.MM.yyyy") if dostep_do else None,
		"zakup": bool(aktywne_zamowienia(_historia(member, course))),
	}


@frappe.whitelist(methods=["POST"])
def wypisz(course: str, member: str) -> dict:
	"""Wypis przez menedżera kursu (Moderator, administrator, autor kursu). Konto, postęp i wyniki zostają."""
	if not _menedzer(course):
		frappe.throw("Brak uprawnień do tego kursu.", frappe.PermissionError)
	nazwa = frappe.db.get_value("LMS Enrollment", {"course": course, "member": member})
	if not nazwa:
		frappe.throw("Ta osoba nie jest już zapisana na ten kurs. Odśwież stronę.")
	frappe.delete_doc("LMS Enrollment", nazwa, ignore_permissions=True)
	_do_dziennika("reczny_wypis", member, course, f"Wypis z Pulpitu kursu: {frappe.session.user}")
	return {"status": "ok"}
