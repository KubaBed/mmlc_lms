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
		root.querySelectorAll(".plyr [aria-label], .plyr .plyr__tooltip, .plyr .plyr__menu span, .plyr label").forEach(function (el) {
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
		"sekcje": ["sekcja", "sekcje", "sekcji"], "sekcji": ["sekcja", "sekcje", "sekcji"],
		"kursanci": ["kursant", "kursanci", "kursantów"], "kursantów": ["kursant", "kursanci", "kursantów"]
	};
	function form(n, f) {
		if (n === 1) return f[0];
		var d = n % 10, h = n % 100;
		return d >= 2 && d <= 4 && (h < 12 || h > 14) ? f[1] : f[2];
	}
	var NUM = /(\d+)\s+(lekcje|lekcji|sekcje|sekcji|kursanci|kursantów)(?![\p{L}])/giu;
	function plurals(root) {
		var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), n;
		while ((n = w.nextNode())) {
			var v = n.nodeValue;
			if (!/\d/.test(v)) continue;
			var r = v.replace(NUM, function (m, num, word) { return num + " " + form(+num, FORMS[word.toLowerCase()]); });
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
			}
		});
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
		});
	}).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
