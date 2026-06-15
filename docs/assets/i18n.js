/* ENSECNET docs — EN/SK i18n engine. Primary language: EN.
   Pages mark translatable nodes with data-i18n="key"; the dictionary below
   holds en/sk strings. Nav labels and footer are translated here too.
   Choice persists in localStorage. */
(function () {
  const DICT = {
    // chrome
    "footer":        { en: "ENSECNET · open-source · <em>Great infrastructure is invisible — its absence is not.</em>",
                       sk: "ENSECNET · open-source · <em>dobrá infraštruktúra nie je vidieť — jej absencia áno.</em>" },
    "nav.lang":      { en: "Language", sk: "Jazyk" },
    // shared nav group titles
    "nav.getting":   { en: "Getting Started", sk: "Začíname" },
    "nav.reference": { en: "Reference",       sk: "Referencia" },
    "nav.deploy":    { en: "Deployment",      sk: "Nasadenie" },
  };

  function current() {
    return localStorage.getItem("ensecnet-lang") || "en";
  }
  function set(lang) {
    localStorage.setItem("ensecnet-lang", lang);
    apply(lang);
  }
  function apply(lang) {
    document.documentElement.setAttribute("lang", lang);
    // toggle per-page EN/SK blocks
    document.querySelectorAll("[data-lang]").forEach((el) => {
      const on = el.getAttribute("data-lang") === lang;
      // inline-level nav labels stay inline; block-level page sections use block
      const inline = el.tagName === "SPAN";
      el.style.display = on ? (inline ? "inline" : "block") : "none";
    });
    // dictionary nodes
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const k = el.getAttribute("data-i18n");
      if (DICT[k] && DICT[k][lang] != null) el.innerHTML = DICT[k][lang];
    });
    // switch button state
    document.querySelectorAll(".lang-btn").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-set") === lang);
    });
  }

  window.ENSECNET_I18N = { current, set, apply, DICT };
  document.addEventListener("DOMContentLoaded", () => apply(current()));
})();
