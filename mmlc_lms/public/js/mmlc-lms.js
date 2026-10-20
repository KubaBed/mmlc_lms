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
	var pending = false;
	new MutationObserver(function () {
		if (pending) return;
		pending = true;
		requestAnimationFrame(function () { pending = false; if (document.querySelector(".plyr")) tr(document); });
	}).observe(document.documentElement, { childList: true, subtree: true });
})();
