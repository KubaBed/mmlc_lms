# mmlc_lms

Wygląd marki MMLC (BRAND.md v1.1) dla widoku kursanta Frappe Learning (`/lms`):
krój Switzer i IBM Plex Mono (pliki fontów wgrane na stronę do `/files/`, poza repozytorium: licencja Fontshare pozwala na użycie na stronie, a nie publikujemy plików w kodzie), kolory marki w tokenach frappe-ui, promienie 0-4 px,
przycisk główny jako pigułka, domyślnie jasny motyw, polskie podpisy odtwarzacza wideo.

Jak działa: hook `after_request` dopisuje do odpowiedzi HTML strony `/lms` link do `public/css/mmlc-lms.css`
i skrypt `public/js/mmlc-lms.js`. Frappe Learning nie ma miejsca na własny CSS w tym widoku.

Wymaga: Frappe 16, Frappe Learning. Instalacja na Frappe Cloud: prywatna ławka (Bench Group) z tą aplikacją.
Po aktualizacji Frappe Learning sprawdzić zrzuty widoku kursanta (nazwy tokenów frappe-ui mogą się zmienić).
