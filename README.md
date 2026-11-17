# mmlc_lms

Wygląd marki MMLC (BRAND.md v1.1) dla widoku kursanta Frappe Learning (`/lms`):
krój Switzer i IBM Plex Mono (pliki fontów wgrane na stronę do `/files/`, poza repozytorium: licencja Fontshare pozwala na użycie na stronie, a nie publikujemy plików w kodzie), kolory marki w tokenach frappe-ui, promienie 0-4 px,
przycisk główny jako pigułka, domyślnie jasny motyw, polskie podpisy odtwarzacza wideo.

Jak działa: hook `after_request` dopisuje do odpowiedzi HTML strony `/lms` link do `public/css/mmlc-lms.css`
i skrypt `public/js/mmlc-lms.js`. Frappe Learning nie ma miejsca na własny CSS w tym widoku.

Wymaga: Frappe 16, Frappe Learning. Instalacja na Frappe Cloud: prywatna ławka (Bench Group) z tą aplikacją.
Po aktualizacji Frappe Learning sprawdzić zrzuty widoku kursanta (nazwy tokenów frappe-ui mogą się zmienić).

## Łącznik Easycart (0.2.1)

Webhook Easycart (`product_assigned`, `product_access_expired`) zakłada konto kursanta i zapis na kurs albo usuwa zapis
po końcu dostępu. Adres: `POST /api/method/mmlc_lms.easycart.api.webhook`, podpis HMAC-SHA256 w `X-Webhook-Signature`.

- Kurs = `custom_id` wariantu w Easycart (nazwa kursu we Frappe). Konto dostaje osoba z `assignee` (zakup dla kogoś).
- Ustawienia w bazie (0.2.1), doctype „MMLC Ustawienia Easycart”: klucz podpisu (pole hasła), konto techniczne z rolą
  Moderator, adres na alarmy. Puste pole = wartość z `site_config` (`easycart_webhook_key`, `easycart_lacznik_user`,
  `easycart_alarm_email`). **Nie zmieniać `site_config` przez API ani panel Frappe Cloud:** 21.10 taki zapis zmienił klucz
  szyfrowania strony (przestały działać klucz API admina i sekret M365 do wysyłki maili).
- Każdy webhook trafia do dziennika „MMLC Zdarzenie Easycart” (surowa treść, status `ok`, `pominiete`, `zly_podpis`,
  `blad`). Odtworzenie po awarii: `POST /api/method/mmlc_lms.easycart.api.odtworz` z `nazwa` wpisu (System Manager).
- Kody: 200 zrobione albo pominięte (nieznany kurs = alarm), 401 zły podpis, 400 treść nie jest JSON-em,
  500 błąd Frappe (Easycart może ponowić), 503 brak klucza podpisu.
- Logika i podpis: `mmlc_lms/easycart/logika.py`, bez importu `frappe`. Testy: `uv run --with pytest pytest testy`.

## Ręczny dostęp: data końca i wypis z kursu (0.4.0)

Dla przelewu po proformie: po wpłacie menedżer kursów zapisuje osobę z Pulpitu kursu, a dostęp wygasa sam,
tak jak kupiony w Easycart.

- Zapis zrobiony przez kogoś innego niż kursant (Pulpit kursu, administrator) dostaje pole `mmlc_dostep_do` na
  `LMS Enrollment`: dziś + 365 dni albo stała data z pola `mmlc_dostep_do` kursu (jak `access_until` wariantu w Easycart,
  np. DIWASS 10.12.2027). Zapis z łącznika Easycart, samodzielny zapis na kurs darmowy i zapis przez grupę zostają bez
  daty. Data podana przy zapisie (np. import przez API) wygrywa; zmienić ją może tylko menedżer kursu.
- Codziennie (`scheduler_events`, `daily`) `mmlc_lms.dostep.api.wygas_reczne` usuwa zapisy po dacie końca. Konto,
  postęp i wyniki testów zostają. Gdy osoba kupiła potem kurs w Easycart (aktywne zamówienie w dzienniku), data ręczna
  znika, a dostępem rządzi zakup.
- Okno „Postępy kursanta” na Pulpicie kursu pokazuje datę końca dostępu i przycisk „Wypisz z kursu” (tylko Moderator,
  administrator, autor kursu; sprawdza serwer w `wypisz`).
- Ślad w dzienniku „MMLC Zdarzenie Easycart”: `reczny_wypis`, `reczne_wygasniecie`, `reczny_przejety`.
- Pola dodaje patch `mmlc_lms.patches.v0_4.pola_dostepu` przy `migrate`. Zapisy sprzed 0.4.0 nie mają daty i nie wygasają.
- Logika: `mmlc_lms/dostep/logika.py`, testy `testy/test_dostep.py`.
