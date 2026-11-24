/* Quanto Custa — menu do topo, comum ao hub e às páginas Índice, Sobre e Privacidade.
   Nas páginas internas, <nav id="menu" data-auto></nav> é preenchido aqui (uma só lista de links para todas). */
(function () {
  const R = "https://quantocustaum.com/";
  const menu = document.getElementById("menu"), hamb = document.getElementById("hamb");
  if (!menu) return;

  if (menu.hasAttribute("data-auto")) {
    const aqui = location.pathname.replace(/index\.html$/, "");
    const link = (href, txt, extra = "") => `<a href="${href}"${extra}${aqui !== "/" && href.endsWith(aqui) ? ' aria-current="page"' : ""}>${txt}</a>`;
    menu.innerHTML = link(R, "Início") +
      `<div class="sub-menu" id="sub-pol">
        <button class="sub-bot" type="button" aria-haspopup="true" aria-expanded="false">Políticos <span aria-hidden="true">▾</span></button>
        <div class="sub-lista">
          <a href="${R}quanto-custa-deputados/">Deputados federais<small>513 deputados · Câmara dos Deputados</small></a>
          <a href="${R}quanto-custa-deputados-estaduais/">Deputados estaduais<small>por enquanto, Ceará, Bahia e Rio Grande do Norte</small></a>
          <a href="${R}quanto-custa-senadores/">Senadores<small>81 senadores · Senado Federal</small></a>
          <a href="${R}quanto-custa-municipios/">Prefeitos e vereadores<small>prefeituras e câmaras do Nordeste</small></a>
        </div>
      </div>
      <div class="sub-menu" id="sub-div">
        <button class="sub-bot" type="button" aria-haspopup="true" aria-expanded="false">Dívidas <span aria-hidden="true">▾</span></button>
        <div class="sub-lista">
          <a href="${R}quanto-custa-divida/">Dívida pública<small>o que o governo deve · juros, vencimentos, bancos</small></a>
          <a href="${R}quanto-custa-devedores/">Devedores da União<small>quem deve ao governo · Dívida Ativa (PGFN)</small></a>
        </div>
      </div>` +
      link(`${R}indice/`, "Índice de Governança", ' title="Índice de Transparência e Governança Pública"') +
      link(`${R}sobre/`, "Sobre") + link(`${R}privacidade/`, "Privacidade");
  }

  // celular: botão ☰ abre e fecha; tocar num link fecha
  if (hamb) {
    hamb.addEventListener("click", () => { const a = menu.classList.toggle("aberto"); hamb.setAttribute("aria-expanded", String(a)); });
    menu.addEventListener("click", (e) => { if (e.target.closest("a")) { menu.classList.remove("aberto"); hamb.setAttribute("aria-expanded", "false"); } });
  }

  // menus "Políticos" e "Dívidas": no toque (sem mouse), o botão abre e fecha a lista
  ["sub-pol", "sub-div"].forEach((id) => {
    const sm = document.getElementById(id); if (!sm) return;
    const b = sm.querySelector(".sub-bot");
    b.addEventListener("click", (e) => { e.stopPropagation(); const a = sm.classList.toggle("aberto"); b.setAttribute("aria-expanded", String(a)); });
    document.addEventListener("click", (e) => { if (!sm.contains(e.target)) { sm.classList.remove("aberto"); b.setAttribute("aria-expanded", "false"); } });
  });
})();
