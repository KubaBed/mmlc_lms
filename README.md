# mmlc_lms

Wygląd marki MMLC (BRAND.md v1.1) dla widoku kursanta Frappe Learning (`/lms`):
krój Switzer i IBM Plex Mono (pliki fontów wgrane na stronę do `/files/`, poza repozytorium: licencja Fontshare pozwala na użycie na stronie, a nie publikujemy plików w kodzie), kolory marki w tokenach frappe-ui, promienie 0-4 px,
przycisk główny jako pigułka, domyślnie jasny motyw, polskie podpisy odtwarzacza wideo.

Jak działa: hook `after_request` dopisuje do odpowiedzi HTML strony `/lms` link do `public/css/mmlc-lms.css`
i skrypt `public/js/mmlc-lms.js`. Frappe Learning nie ma miejsca na własny CSS w tym widoku.

Wymaga: Frappe 16, Frappe Learning. Instalacja na Frappe Cloud: prywatna ławka (Bench Group) z tą aplikacją.
Po aktualizacji Frappe Learning sprawdzić zrzuty widoku kursanta (nazwy tokenów frappe-ui mogą się zmienić).

## Łącznik Easycart (0.2.0)

Webhook Easycart (`product_assigned`, `product_access_expired`) zakłada konto kursanta i zapis na kurs albo usuwa zapis
po końcu dostępu. Adres: `POST /api/method/mmlc_lms.easycart.api.webhook`, podpis HMAC-SHA256 w `X-Webhook-Signature`.

- Kurs = `custom_id` wariantu w Easycart (nazwa kursu we Frappe). Konto dostaje osoba z `assignee` (zakup dla kogoś).
- Ustawienia w `site_config` strony, nie w repo: `easycart_webhook_key`, `easycart_lacznik_user` (konto z rolą
  Moderator), `easycart_alarm_email`.
- Każdy webhook trafia do dziennika „MMLC Zdarzenie Easycart” (surowa treść, status `ok`, `pominiete`, `zly_podpis`,
  `blad`). Odtworzenie po awarii: `POST /api/method/mmlc_lms.easycart.api.odtworz` z `nazwa` wpisu (System Manager).
- Kody: 200 zrobione albo pominięte (nieznany kurs = alarm), 401 zły podpis, 400 treść nie jest JSON-em,
  500 błąd Frappe (Easycart może ponowić), 503 brak klucza w `site_config`.
- Logika i podpis: `mmlc_lms/easycart/logika.py`, bez importu `frappe`. Testy: `uv run --with pytest pytest testy`.
