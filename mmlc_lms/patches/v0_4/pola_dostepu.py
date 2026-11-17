"""0.4.0: pola daty końca ręcznego dostępu (mmlc_lms/dostep/)."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"LMS Enrollment": [
				{
					"fieldname": "mmlc_dostep_do",
					"label": "Koniec dostępu",
					"fieldtype": "Date",
					"insert_after": "member_type",
					"description": (
						"Ostatni dzień dostępu przy zapisie ręcznym. Gdy pole jest puste, codzienne wygaszanie pomija ten zapis, "
						"a dostęp kupiony w Easycart kończy łącznik Easycart."
					),
				}
			],
			"LMS Course": [
				{
					"fieldname": "mmlc_dostep_do",
					"label": "Stała data końca dostępu",
					"fieldtype": "Date",
					"insert_after": "mmlc_forma",
					"description": (
						"Ostatni dzień dostępu dla każdego ręcznego zapisu na ten kurs, jak data końca dostępu w wariancie Easycart. "
						"Gdy pole jest puste, ręczny zapis trwa 365 dni od dnia zapisu. Zmiana daty nie przesuwa zapisów już zrobionych."
					),
				}
			],
		},
		update=True,
	)
