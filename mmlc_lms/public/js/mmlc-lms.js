// Odtwarzacz wideo (Plyr) ma w Frappe Learning angielskie podpisy wpisane w kod.
// Podmieniamy je na polskie w drzewie strony, gdy odtwarzacz się pojawi.
(function () {
	var PL = {
		"Play": "Odtwórz", "Pause": "Wstrzymaj", "Restart": "Od początku", "Mute": "Wycisz", "Unmute": "Włącz dźwięk",
		"Settings": "Ustawienia", "Speed": "Szybkość", "Normal": "Normalna", "Quality": "Jakość", "Captions": "Napisy",
		"Disabled": "Wyłączone", "Enabled": "Włączone", "Enter fullscreen": "Pełny ekran",
		"Exit fullscreen": "Zamknij pełny ekran", "Go back to previous menu": "Wróć", "Seek": "Przewiń",
		"Current time": "Bieżący czas", "Duration": "Czas trwania", "Volume": "Głośność", "PIP": "Obraz w obrazie",
		"Download": "Pobierz", "Loop": "Pętla", "Reset": "Resetuj", "Enable captions": "Włącz napisy",
		"Disable captions": "Wyłącz napisy", "% buffered": "% wczytano"
	};
	function tr(root) {
		root.querySelectorAll(".plyr [aria-label], .plyr .plyr__tooltip, .plyr .plyr__sr-only, .plyr .plyr__menu span, .plyr label, .plyr progress").forEach(function (el) {
			var a = el.getAttribute("aria-label");
			if (a && PL[a]) el.setAttribute("aria-label", PL[a]);
			if (el.childNodes.length === 1 && el.firstChild.nodeType === 3) {
				var t = el.firstChild.nodeValue.trim();
				if (PL[t]) el.firstChild.nodeValue = PL[t];
			}
		});
	}
	// Frappe Learning dokleja do liczby jedną formę słowa ("6 lekcje", "1 Kursanci"). Poprawiamy odmianę.
	var FORMS = {
		"lekcje": ["lekcja", "lekcje", "lekcji"], "lekcji": ["lekcja", "lekcje", "lekcji"],
		// Frappe mówi „section”, a w edytorze kursu i w instrukcji jest „rozdział” (uwagi z 20.10)
		"sekcja": ["rozdział", "rozdziały", "rozdziałów"], "sekcje": ["rozdział", "rozdziały", "rozdziałów"],
		"sekcji": ["rozdział", "rozdziały", "rozdziałów"],
		"kursanci": ["kursant", "kursanci", "kursantów"], "kursantów": ["kursant", "kursanci", "kursantów"]
	};
	function form(n, f) {
		if (n === 1) return f[0];
		var d = n % 10, h = n % 100;
		return d >= 2 && d <= 4 && (h < 12 || h > 14) ? f[1] : f[2];
	}
	var NUM = /(\d+)\s+(lekcje|lekcji|sekcja|sekcje|sekcji|kursanci|kursantów)(?![\p{L}])/giu;
	function plurals(root) {
		var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), n;
		while ((n = w.nextNode())) {
			var v = n.nodeValue;
			if (!/\d/.test(v) && v.indexOf("ocena kursu") < 0) continue;
			var r = v.replace(NUM, function (m, num, word) { return num + " " + form(+num, FORMS[word.toLowerCase()]); });
			r = r.replace(/^(\d+)\s+zapisanych$/, "Zapisani: $1")
				.replace(/ocena kursu\s*&\s*(\d+)\s+ocen\S*\s+kursant\S*/, "średnia ocena · opinie: $1");
			if (r !== v) n.nodeValue = r;
		}
	}
	// Elementy, których kancelaria nie używa: filtr certyfikatów i zachęta do uzupełnienia profilu.
	function tidy(root) {
		root.querySelectorAll("label, button, span, div").forEach(function (el) {
			if (el.childElementCount > 3) return;
			var t = (el.textContent || "").trim();
			if (t === "Certyfikacja" && el.tagName === "LABEL") {
				var box = el.closest("div") || el;
				box.style.display = "none";
			} else if (t === "Uzupełnij profil") {
				var card = el.parentElement && el.parentElement.parentElement;
				if (card && /Mój profil/.test(card.textContent || "")) card.style.display = "none";
			} else if (t === "Opublikowany" && el.tagName === "BUTTON") {
				el.textContent = "Opublikowane";
			} else if (t === "Opublikowany" && el.tagName === "DIV" && /rounded-full/.test(el.className)) {
				// Odznaka statusu kursu przy tytule: kursant nie potrzebuje "Opublikowany", autor dalej widzi "Szkic".
				el.style.display = "none";
			}
		});
	}
	// Napisy wpisane w Frappe Learning na sztywno po angielsku (menu użytkownika, ustawienia, edytor lekcji, postępy).
	// Podmieniamy tylko węzeł tekstowy równy całemu napisowi (uwagi z 20.10).
	var UI = {
		"Toggle Theme": "Motyw", "Log out": "Wyloguj się", "Log Out": "Wyloguj się", "Log in": "Zaloguj się",
		"Login to Frappe Cloud": "Panel Frappe Cloud", "My Profile": "Mój profil", "Settings": "Ustawienia",
		"Student Progress": "Postępy kursanta", "Progress": "Postęp", "Heading": "Nagłówek", "List": "Lista",
		"Table": "Tabela", "CodeBox": "Kod", "Upload": "Plik", "Quote": "Cytat", "Embed": "Osadzenie",
		"Badges": "Odznaki", "Categories": "Kategorie", "Accounts": "Konta", "Gateways": "Bramki płatności",
		"Transactions": "Transakcje", "Coupons": "Kupony", "Signup": "Rejestracja", "User Management": "Użytkownicy",
		"Email Templates": "Szablony maili", "Payment": "Płatności", "Branding": "Wygląd", "Sidebar": "Menu boczne",
		"Evaluators": "Oceniający", "Title": "Tytuł",
		"Ty": "Konto", "Wróć tam, gdzie skończyłeś": "Wróć do swoich kursów"
	};
	var COVER = "Okładka 1600 × 900 px (16:9), plik .jpg lub .png, widoczna na karcie kursu.";
	function ui(root) {
		var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), n, hide = [];
		while ((n = w.nextNode())) {
			var t = n.nodeValue.trim();
			if (!t) continue;
			if (UI[t]) { n.nodeValue = n.nodeValue.replace(t, UI[t]); continue; }
			if (t === "Clear Demo Data") { hide.push(n.parentElement); continue; }
			if (/750\s*[×x]\s*422/.test(t)) { n.nodeValue = COVER; continue; }
			var m = t.match(/^Nie znaleziono: (Courses|Kursy)$/);
			if (m) n.nodeValue = "Nie znaleziono kursów";
		}
		hide.forEach(function (el) {
			var item = el && (el.closest("[role='menuitem']") || el.closest("button") || el);
			if (item) item.style.display = "none";
		});
	}
	// 0.3.1 (przegląd kursanta 17.11): elementy, które kancelaria ukrywa, i komunikat o zakupie zamiast „skontaktuj się
	// z administratorem”. Ukrywane po treści, bo frappe-ui nie daje im stałych klas.
	var SKLEP = "https://mmlc.pl/kursy/";
	var UKRYJ = /^(Zapisani: \d+|Certyfikat ukończenia|Społeczność|Odśwież sesję)$/;
	function kursant(root) {
		var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), n, hide = [], zapis = [];
		while ((n = w.nextNode())) {
			var t = n.nodeValue.trim(), el = n.parentElement;
			if (!t || !el) continue;
			if (UKRYJ.test(t)) hide.push(t === "Społeczność" || t === "Odśwież sesję" ? el.closest("button") : el.closest("div"));
			else if (t === "🔥") hide.push(el.closest("button"));
			else if (/^Aby zapisać się na ten kurs/.test(t)) zapis.push(el);
			else if (/enrolled programs/i.test(t)) n.nodeValue = /^Nie znaleziono/.test(t) ? "Nie masz jeszcze ścieżek nauki" : "Gdy dołączysz do ścieżki, zobaczysz ją tutaj.";
			else if (/^Brak elementów: courses/i.test(t)) n.nodeValue = "Kupione kursy pojawią się tutaj. Ofertę znajdziesz na mmlc.pl.";
			else if (t === "Osoby" && el.closest("header")) n.nodeValue = "Profil";
		}
		hide.forEach(function (e) { if (e) e.style.display = "none"; });
		zapis.forEach(function (el) {
			if (el.dataset.mmlc) return;
			el.dataset.mmlc = "1";
			el.classList.add("mmlc-zapis");
			el.innerHTML = 'Dostęp do kursu kupisz na stronie <a href="' + SKLEP + '" target="_top" style="text-decoration:underline">mmlc.pl</a>. Po zakupie kurs pojawi się na Twojej liście.';
		});
		// stronicowanie przy jednej stronie kursów („0 z 0”, „2 z 2” w trzech blokach) razem z wyborem 24/60/120
		document.querySelectorAll("div.flex.items-center.gap-1").forEach(function (c) {
			var k = c.children;
			if (k.length !== 3 || k[1].textContent.trim() !== "z") return;
			var a = k[0].textContent.trim(), b = k[2].textContent.trim();
			if (a === b && +a <= 24 && document.querySelector("[role='radiogroup']")) {
				var bar = c.parentElement && c.parentElement.parentElement;
				if (bar && bar.querySelector("[role='radiogroup']")) bar.style.display = "none";
			}
		});
		// kategoria podwójnie: link z ikoną i etykieta pod tytułem
		document.querySelectorAll("section.space-y-4 div.flex.flex-wrap.gap-2").forEach(function (box) {
			var link = box.closest("section").querySelector("a[href*='category=']");
			if (link && box.textContent.trim() === link.textContent.trim()) box.style.display = "none";
		});
		document.querySelectorAll("[aria-label='Notifications alt+T']").forEach(function (e) { e.setAttribute("aria-label", "Powiadomienia (Alt+T)"); });
	}
	function skipLink() {
		var a = document.querySelector("a.sr-only[href^='#']");
		if (a && a.textContent.trim() === "Skip to main content") a.textContent = "Przejdź do treści";
	}
	var pending = false;
	new MutationObserver(function () {
		if (pending) return;
		pending = true;
		requestAnimationFrame(function () {
			pending = false;
			if (document.querySelector(".plyr")) tr(document);
			plurals(document.body);
			tidy(document.body);
			ui(document.body);
			kursant(document.body);
			skipLink();
		});
	}).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
