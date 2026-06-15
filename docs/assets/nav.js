/* ENSECNET CiscoParser docs — sidebar navigation.
   Add a page: add an entry here and create the matching .html. */
const NAV = [
  { group: "Getting Started", items: [
    { title: "Overview",        path: "index.html" },
    { title: "Why a parser",    path: "pages/why.html" },
  ]},
  { group: "Reference", items: [
    { title: "What it extracts", path: "pages/extraction.html" },
    { title: "Architecture",     path: "pages/architecture.html" },
    { title: "API",              path: "pages/api.html" },
  ]},
  { group: "Deployment", items: [
    { title: "Deploy on Proxmox", path: "pages/deploy.html" },
    { title: "Web edition",       path: "pages/web.html" },
  ]},
];

(function () {
  const root = document.body.getAttribute("data-root") || "";
  const current = document.body.getAttribute("data-page") || "";
  const sb = document.querySelector(".nav");
  if (!sb) return;
  let html = "";
  NAV.forEach((g) => {
    html += `<div class="nav-group"><div class="nav-group-title">${g.group}</div>`;
    g.items.forEach((it) => {
      const cls = [it.child ? "child" : "", it.path === current ? "active" : ""]
        .filter(Boolean).join(" ");
      html += `<a class="${cls}" href="${root}${it.path}">${it.title}</a>`;
    });
    html += `</div>`;
  });
  sb.innerHTML = html;
})();
