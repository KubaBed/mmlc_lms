"""Szew 1: podpis webhooka Easycart (HMAC-SHA256 hex z surowej treści, nagłówek X-Webhook-Signature)."""
from mmlc_lms.easycart.logika import podpis_ok

KLUCZ = "klucz-testowy"
TRESC = '{"event":"product_assigned","customer_name":"Zażółć Gęślą"}'.encode()
# wartość policzona niezależnie: printf '%s' "$TRESC" | openssl dgst -sha256 -hmac klucz-testowy
PODPIS = "d29631948f7909841717b5ec7266b19e717e55ff880b8a43d61acf18e4397144"


def test_poprawny_podpis_z_surowej_tresci():
	assert podpis_ok(TRESC, PODPIS, KLUCZ)


def test_zly_podpis():
	assert not podpis_ok(TRESC, "0" * 64, KLUCZ)


def test_brak_naglowka():
	assert not podpis_ok(TRESC, None, KLUCZ)
	assert not podpis_ok(TRESC, "", KLUCZ)


def test_poprawny_podpis_ale_zmieniona_tresc():
	assert not podpis_ok(TRESC.replace(b"Zaj", b"Zbj").replace("Gęślą".encode(), "Gesla".encode()), PODPIS, KLUCZ)


def test_wielkie_litery_w_podpisie():
	assert podpis_ok(TRESC, PODPIS.upper(), KLUCZ)
