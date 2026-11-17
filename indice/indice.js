/* Índice de Transparência e Governança Pública — lê dados/indice.json (gerado pelo robo/indice.py) */
"use strict";
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nf = (v, d = 0) => (v || 0).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const norm = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const COR = { boa: "#23966B", regular: "#D69A32", ruim: "#C84C4C", sem: "#B8C3CF" };
const FX = { boa: "boa", regular: "regular", ruim: "ruim", sem: "sem nota" };
const NOME_UF = { CE: "Ceará", BA: "Bahia" };
const SITE = "https://quantocustaum.com/";
const S = { d: null, aba: "assembleias", uf: "", busca: "", ordem: "pior", limite: 50, sel: null };

const barra = (n, f) => `<div class="ix-barra"><i style="width:${n ?? 0}%;background:${COR[f]}"></i></div>`;
const legenda = () => `<div class="ix-leg"><span><i style="background:${COR.boa}"></i>Boa (80 a 100)</span><span><i style="background:${COR.regular}"></i>Regular (50 a 79)</span><span><i style="background:${COR.ruim}"></i>Ruim (menos de 50)</span>${S.aba === "assembleias" ? `<span><i style="background:${COR.sem}"></i>Ainda sem nota</span>` : ""}</div>`;
const circ = (n, f) => `<div class="ix-circ" style="background:conic-gradient(${COR[f]} 0 ${n}%,rgba(255,255,255,.15) ${n}% 100%)"><span>${n ?? "—"}</span></div>`;
const dataBR = (s) => { const [a, m, d] = String(s).slice(0, 10).split("-"); return `${d}/${m}/${a}`; };

// ------------------------------------------------------------------ Assembleias
function listaAssembleias() {
  const A = S.d.assembleias;
  const linhas = A.avaliadas.map((a, i) => `<tr data-id="${a.id}" class="${S.sel === a.id ? "ativo" : ""}" tabindex="0"><td class="ix-pos">${i + 1}</td>
    <td class="ix-org"><b>${esc(a.sigla)}</b><small>${esc(a.nome)}</small></td>
    <td><div class="ix-nota">${barra(a.nota, a.faixa)}<span class="ix-num">${a.nota ?? "—"}</span></div></td>
    <td class="ix-col-fx"><span class="ix-fx ${a.faixa}">${FX[a.faixa]}</span></td></tr>`).join("");
  const sem = A.sem_nota.map((g) => `<div class="ix-sn"><b>${esc(g.titulo)}:</b> ${esc(g.orgaos.join(" · "))}<p>${esc(g.explica)}</p></div>`).join("");
  return `<div class="ix-cab"><h2>Assembleias Legislativas</h2><span>toque numa linha para ver a ficha</span></div>${legenda()}
    <table><thead><tr><th>#</th><th>Órgão</th><th>Nota</th><th class="ix-col-fx">Faixa</th></tr></thead><tbody>${linhas}</tbody></table>
    <div class="ix-semnota"><h3>Ainda sem nota</h3>${sem}</div>`;
}

function fichaAssembleia(id) {
  const a = S.d.assembleias.avaliadas.find((x) => x.id === id) || S.d.assembleias.avaliadas[0];
  if (!a) return "";
  const P = Object.fromEntries(S.d.pesos.assembleias.map(([c, nome, peso, txt]) => [c, { nome, peso, txt }]));
  const crit = a.criterios.map(([c, p, peso]) => {
    const f = p == null ? "sem" : p / peso >= 0.8 ? "boa" : p / peso >= 0.5 ? "regular" : "ruim";
    return `<div class="ix-cr"><span>${esc(P[c].nome)} <span class="peso">· peso ${peso}</span></span>${barra(p == null ? 0 : (100 * p) / peso, f)}<span class="v">${p == null ? "fora" : `${p}/${peso}`}</span></div>`;
  }).join("");
  const tag = (c, p, peso) => p == null ? ["fora", "fora da conta"] : p >= peso ? ["bom", "bom"] : p / peso >= 0.5 ? ["atencao", "atenção"] : ["ruim", "ruim"];
  const provas = a.criterios.map(([c, p, peso, prova]) => { const [cls, rot] = tag(c, p, peso);
    return `<li><span class="ix-tag ${cls}">${rot}</span><b>${esc(P[c].nome)}:</b> ${esc(prova)}</li>`; }).join("");
  const fora = a.fora_da_conta.length ? ` · ${a.fora_da_conta.length === 1 ? "1 critério ainda fora da conta" : a.fora_da_conta.length + " critérios ainda fora da conta"}` : "";
  return `<div class="ix-f-cab">${circ(a.nota, a.faixa)}<div><h3>${esc(a.sigla)} · ${esc(NOME_UF[a.uf] || a.uf)}</h3><p>${FX[a.faixa][0].toUpperCase() + FX[a.faixa].slice(1)} · avaliada em ${dataBR(a.avaliado_em)}; a pontualidade é conferida todo dia${fora}</p></div></div>
    <div class="ix-crit">${crit}</div>
    <div class="ix-prov"><h4>As provas</h4><ul>${provas}</ul></div>
    <div class="ix-f-links"><a href="${SITE}quanto-custa-deputados-estaduais/?uf=${a.id}">Ver os gastos dos deputados →</a><a href="${esc(a.fonte)}" rel="noopener">Fonte oficial →</a></div>`;
}

// ------------------------------------------------------------------ municípios
function filtrados() {
  const q = norm(S.busca);
  let ms = S.d.municipios.filter((m) => (!S.uf || m.uf === S.uf) && (!q || norm(m.nome).includes(q)));
  if (S.ordem === "melhor") ms = [...ms].sort((a, b) => b.nota - a.nota || a.nome.localeCompare(b.nome, "pt-BR"));
  else if (S.ordem === "nome") ms = [...ms].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  return ms;
}
const chave = (m) => `${m.uf}-${m.id}`;

function listaMunicipios() {
  const R = S.d.resumo_municipios[S.uf || "todos"] || {};
  const ms = filtrados();
  const linhas = ms.slice(0, S.limite).map((m, i) => `<tr data-id="${chave(m)}" class="${S.sel === chave(m) ? "ativo" : ""}" tabindex="0"><td class="ix-pos">${S.ordem === "nome" ? "" : i + 1}</td>
    <td class="ix-org"><b>${esc(m.nome)}</b><small>${esc(NOME_UF[m.uf])}</small></td>
    <td><div class="ix-nota">${barra(m.nota, m.faixa)}<span class="ix-num">${m.nota}</span></div></td>
    <td class="ix-col-fx"><span class="ix-fx ${m.faixa}">${FX[m.faixa]}</span></td></tr>`).join("");
  return `<div class="ix-cab"><h2>Prefeituras e câmaras${S.uf ? " · " + NOME_UF[S.uf] : ""}</h2><span>prestação de contas aos órgãos de controle</span></div>
    <div class="ix-resumo"><div><small>cidades</small><b>${nf(R.n)}</b></div><div><small>nota média</small><b>${R.media ?? "—"}</b></div>
      <div><small>regular</small><b style="color:#8a5a12">${nf(R.regular)}</b></div><div><small>ruim</small><b style="color:#8a2a22">${nf(R.ruim)}</b></div></div>
    ${legenda()}
    <div class="ix-ferr"><input id="m-busca" type="search" placeholder="Procurar cidade" value="${esc(S.busca)}" aria-label="Procurar cidade">
      <select id="m-ordem" aria-label="Ordem"><option value="pior"${S.ordem === "pior" ? " selected" : ""}>Piores notas primeiro</option><option value="melhor"${S.ordem === "melhor" ? " selected" : ""}>Melhores notas primeiro</option><option value="nome"${S.ordem === "nome" ? " selected" : ""}>Ordem alfabética</option></select></div>
    ${ms.length ? `<table><thead><tr><th>#</th><th>Cidade</th><th>Nota</th><th class="ix-col-fx">Faixa</th></tr></thead><tbody>${linhas}</tbody></table>` : `<p class="ix-nota-rod">Nenhuma cidade com esse nome.</p>`}
    ${ms.length > S.limite ? `<button type="button" class="ix-mais" id="m-mais">Mostrar mais ${nf(Math.min(50, ms.length - S.limite))} (de ${nf(ms.length)})</button>` : ""}
    <p class="ix-nota-rod">Nas cidades, a nota mede só a <b>prestação de contas</b> ao tribunal de contas (Ceará) ou ao Tesouro Nacional (Bahia). O portal de transparência de cada prefeitura ainda não é avaliado: veja "Limites desta prévia", abaixo.</p>`;
}

function fichaMunicipio(k) {
  const m = S.d.municipios.find((x) => chave(x) === k) || filtrados()[0];
  if (!m) return `<p class="ix-carregando">Nenhuma cidade selecionada.</p>`;
  const P = S.d.pesos.municipios;
  const crit = P.map(([c, nome, peso], i) => { const p = m.pts[i], f = p / peso >= 0.8 ? "boa" : p / peso >= 0.5 ? "regular" : "ruim";
    return `<div class="ix-cr"><span>${esc(nome)} <span class="peso">· peso ${peso}</span></span>${barra((100 * p) / peso, f)}<span class="v">${nf(p, p % 1 ? 1 : 0)}/${peso}</span></div>`; }).join("");
  const rot = { ruim: "ruim", atencao: "atenção", bom: "bom" };
  const provas = m.provas.map(([t, txt]) => `<li><span class="ix-tag ${t}">${rot[t]}</span>${esc(txt)}</li>`).join("");
  const link = m.uf === "CE" ? `${SITE}quanto-custa-municipios/#municipio/${m.id}` : `${SITE}quanto-custa-municipios/?uf=ba#municipio/${m.id}`;
  return `<div class="ix-f-cab">${circ(m.nota, m.faixa)}<div><h3>${esc(m.nome)} · ${m.uf}</h3><p>${FX[m.faixa][0].toUpperCase() + FX[m.faixa].slice(1)} · fonte: ${esc(S.d.fontes[m.uf])} · recalculada todo dia</p></div></div>
    <div class="ix-crit">${crit}</div>
    <div class="ix-prov"><h4>As provas</h4><ul>${provas}</ul></div>
    <div class="ix-f-links"><a href="${link}">Ver os gastos da cidade →</a></div>`;
}

// ------------------------------------------------------------------ como a nota é feita
function como() {
  const D = S.d, ass = S.aba === "assembleias";
  const pesos = (ass ? D.pesos.assembleias : D.pesos.municipios).map(([, nome, peso, txt]) => `<div class="ix-peso"><b>${esc(nome)} <span>${peso}</span></b><p>${esc(txt)}</p></div>`).join("");
  const limites = ass ? [
    "Por enquanto só as Assembleias do Ceará e da Bahia têm nota, porque são as que os robôs do projeto já coletam todo dia. As outras entram à medida que o robô testa cada uma.",
    "Quando o site de uma Assembleia não responde ao robô, isso ainda não vira nota zero: o bloqueio pode ser só para robôs, e não para o cidadão. Vamos conferir de outra forma antes.",
    "Um critério que ainda não deu para verificar fica fora da conta (aparece como \"fora\"), e a nota é calculada sobre os outros, na mesma proporção.",
    "Os pontos de cada critério vêm das dificuldades reais que o robô encontrou e estão escritos nas provas. Só a pontualidade é recalculada sozinha todo dia; os outros critérios são revistos quando a Assembleia muda o site.",
  ] : [
    `A nota das cidades mede só a prestação de contas aos órgãos de controle: no Ceará, os balancetes e as notas de empenho enviados ao TCE-CE; na Bahia, o relatório bimestral (RREO) entregue ao Tesouro Nacional. É o que os robôs conseguem conferir em todas as cidades.`,
    "O portal de transparência de cada prefeitura e de cada câmara ainda não é avaliado (são centenas de sites, cada um de um jeito). Por isso a maioria das cidades tem nota alta: entregar as contas é obrigação, e quase todas cumprem. Nota alta aqui não quer dizer que o portal da cidade é bom.",
    `"Entrega no prazo" compara cada cidade com a maioria: no Ceará, com o mês que a maioria já tem no TCE-CE; na Bahia, com o bimestre que a maioria já entregou ao Tesouro. Assim a nota não cai só porque o tribunal ou o Tesouro ainda não publicou o período.`,
    "Ceará e Bahia são avaliados por fontes diferentes (tribunal de contas e Tesouro Nacional). Compare cidades do mesmo estado.",
    `No Ceará, só contam diferenças entre as notas de empenho e o balancete da câmara acima de 1% do gasto do ano; diferenças menores costumam ser arredondamento ou lançamento de fim de mês.`,
    `Na Bahia, prefeitura e câmara são avaliadas juntas: o relatório ao Tesouro é um só, entregue pela prefeitura, e já traz o gasto da câmara.`,
  ];
  return `<h2>Como a nota é feita</h2>
    <p>${ass ? "Oito critérios, que somam 100 pontos. Cada ponto perdido tem uma prova escrita na ficha. A Assembleia pode corrigir o problema, e a nota sobe na revisão seguinte." : `Três critérios, que somam 100 pontos, calculados sozinhos todo dia a partir dos dados de ${D.inicio} até hoje. A cidade pode entregar o que falta, e a nota sobe na atualização seguinte.`}</p>
    <div class="ix-pesos">${pesos}</div>
    <div class="ix-limites"><h3>Limites desta prévia</h3><ul>${limites.map((t) => `<li>${t}</li>`).join("")}</ul></div>`;
}

// ------------------------------------------------------------------ tela
function desenhar() {
  const ass = S.aba === "assembleias";
  document.querySelectorAll(".ix-aba").forEach((b) => b.classList.toggle("on", b.dataset.aba === S.aba));
  $("#f-uf-rot").hidden = ass;
  $("#lista").innerHTML = ass ? listaAssembleias() : listaMunicipios();
  $("#ficha").innerHTML = ass ? fichaAssembleia(S.sel) : fichaMunicipio(S.sel);
  $("#como").innerHTML = como();
  const busca = $("#m-busca");
  if (busca) busca.oninput = () => { S.busca = busca.value; S.limite = 50; redesenharLista(); };
  const ordem = $("#m-ordem");
  if (ordem) ordem.onchange = () => { S.ordem = ordem.value; S.limite = 50; desenhar(); };
  const mais = $("#m-mais");
  if (mais) mais.onclick = () => { S.limite += 50; desenhar(); };
}
// ao digitar, redesenha só a lista e devolve o foco à caixa de busca
function redesenharLista() {
  const pos = $("#m-busca")?.selectionStart;
  desenhar();
  const b = $("#m-busca"); if (b) { b.focus(); if (pos != null) b.setSelectionRange(pos, pos); }
}
function escolher(id) {
  if (!id) return;
  S.sel = id;
  document.querySelectorAll("#lista tbody tr").forEach((t) => t.classList.toggle("ativo", t.dataset.id === id));
  $("#ficha").innerHTML = S.aba === "assembleias" ? fichaAssembleia(id) : fichaMunicipio(id);
  if (matchMedia("(max-width: 860px)").matches) $("#ficha").scrollIntoView({ behavior: "smooth", block: "start" });
}
function lerEndereco() {
  const u = new URL(location);
  S.aba = u.searchParams.get("aba") === "cidades" ? "municipios" : "assembleias";
  const uf = (u.searchParams.get("uf") || "").toUpperCase();
  S.uf = NOME_UF[uf] ? uf : "";
  $("#f-uf").value = S.uf;
}
function gravarEndereco() {
  const u = new URL(location);
  u.searchParams.delete("aba"); u.searchParams.delete("uf");
  if (S.aba === "municipios") { u.searchParams.set("aba", "cidades"); if (S.uf) u.searchParams.set("uf", S.uf.toLowerCase()); }
  history.replaceState(null, "", u);
}

async function iniciar() {
  try {
    const r = await fetch("../dados/indice.json", { cache: "no-cache" });
    if (!r.ok) throw new Error(r.status);
    S.d = await r.json();
  } catch {
    $("#lista").innerHTML = `<p class="ix-carregando">Não foi possível carregar o índice agora. Tente de novo em alguns minutos.</p>`;
    return;
  }
  lerEndereco();
  desenhar();
  $("#atual").textContent = `Notas recalculadas em ${new Date(S.d.gerado_em).toLocaleString("pt-BR")}. Fontes: robôs do Projeto Quanto Custa, ${Object.values(S.d.fontes).join(" e ")} e os portais das Assembleias.`;
  document.querySelectorAll(".ix-aba").forEach((b) => (b.onclick = () => { S.aba = b.dataset.aba; S.sel = null; S.limite = 50; gravarEndereco(); desenhar(); }));
  $("#f-uf").onchange = (e) => { S.uf = e.target.value; S.sel = null; S.limite = 50; gravarEndereco(); desenhar(); };
  $("#lista").addEventListener("click", (e) => escolher(e.target.closest("tbody tr")?.dataset.id));
  $("#lista").addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { const t = e.target.closest("tbody tr"); if (t) { e.preventDefault(); escolher(t.dataset.id); } } });
}
iniciar();
