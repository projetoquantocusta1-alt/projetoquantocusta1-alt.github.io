/* Projeto Quanto Custa — hub. Só lê dados/totais_hub.json (feito pelo Mensageiro). */
(() => {
"use strict";
const $ = (s) => document.querySelector(s);
const nf = (v, d = 0) => (v || 0).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const brl = (v, d = 0) => "R$ " + nf(v, d);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const curto = (v) => { const a = Math.abs(v || 0);
  if (a >= 1e12) return "R$ " + nf(v / 1e12, 2) + (a < 2e12 ? " trilhão" : " trilhões");
  if (a >= 1e9) return "R$ " + nf(v / 1e9, 2) + (a < 2e9 ? " bilhão" : " bilhões");
  if (a >= 1e6) return "R$ " + nf(v / 1e6, a >= 1e8 ? 0 : 1) + (a < 2e6 ? " milhão" : " milhões");
  if (a >= 1e3) return "R$ " + nf(v / 1e3, 0) + " mil";
  return brl(v, 2); };
// valor por extenso para ler números grandes: 2.193.266.731 -> "≈ 2,19 bilhões de reais"
const porExtenso = (v) => { const a = Math.abs(v || 0);
  for (const [b, um, varios] of [[1e12, "trilhão", "trilhões"], [1e9, "bilhão", "bilhões"], [1e6, "milhão", "milhões"], [1e3, "mil", "mil"]]) {
    if (a < b) continue;
    const x = v / b, t = x.toLocaleString("pt-BR", { maximumFractionDigits: Math.abs(x) < 10 ? 2 : Math.abs(x) < 100 ? 1 : 0 });
    return b === 1e3 ? `≈ ${t} mil reais` : `≈ ${t} ${Math.abs(x) < 2 ? um : varios} de reais`; }
  return ""; };
const pct = (x) => nf(x * 100, 1) + "%";
const dataLocal = (iso) => { const [a, m, d] = iso.split("-").map(Number); return new Date(a, m - 1, d).getTime(); };

const ESF = {
  deputados: { cor: "var(--dep)", k: "Câmara dos Deputados", nome: "Deputados federais", ir: "Ver deputados, notas e presença" },
  senadores: { cor: "var(--sen)", k: "Senado Federal", nome: "Senadores", ir: "Ver senadores e cada nota" },
  municipios: { cor: "var(--mun)", k: "Prefeituras e câmaras", nome: "Prefeitos e vereadores", ir: "Ver minha cidade, nota a nota", tag: "Ceará e Bahia" },
};

function valorAgora(c, t) {
  if (!c) return 0;
  const ini = dataLocal(c.inicio);
  return Math.min(c.teto || c.ja, c.ja + Math.max(0, (t - ini) / 1000) * (c.por_seg || 0));
}

// comparação entre esferas: quanto custa, por ano, uma unidade de cada uma
function comparar(T) {
  const d = T.esferas.deputados, s = T.esferas.senadores, m = T.esferas.municipios, it = [];
  if (d?.por_cadeira) it.push(`<b>1 deputado federal</b> ${curto(d.por_cadeira.valor)}/ano (${d.por_cadeira.ano})`);
  if (s?.por_cadeira) it.push(`<b>1 senador</b> ${curto(s.por_cadeira.valor)}/ano (${s.por_cadeira.ano}, sem a equipe do gabinete)`);
  if (m?.por_vereador && m?.vereadores) { const cam = (m.por_vereador.valor * m.vereadores) / m.total_municipios;
    it.push(`<b>1 câmara municipal do Ceará</b> ${curto(cam)}/ano em média (${m.por_vereador.ano}) · ${curto(m.por_vereador.valor)} por vereador`); }
  $("#comparar").innerHTML = it.length ? "Lado a lado: " + it.join(" · ") + ". Valores de hoje (IPCA)." : "";
}

function contador(T) {
  // principal: Congresso Nacional; câmaras do Ceará num contador à parte (não misturar Brasil com um estado)
  const cs = ["deputados", "senadores"].map((k) => (T.contador || {})[k]).filter(Boolean);
  const cms = ["municipios", "municipios_ba"].map((k) => (T.contador || {})[k]).filter(Boolean);
  const cm = cms.length ? cms : null;
  document.querySelectorAll(".ano").forEach((e) => (e.textContent = T.ano));
  const porSeg = cs.reduce((s, c) => s + (c.por_seg || 0), 0);
  $("#cont-rot .ano").textContent = T.ano;
  $("#cont-ritmo").innerHTML = porSeg ? `+ <b>${brl(porSeg, 2)}</b> por segundo · <b>${curto(porSeg * 86400)}</b> por dia` : "";
  const mun = T.esferas.municipios;
  $("#cont-nota").textContent = "Valor estimado em tempo real: soma o que já foi registrado e avança no ritmo de gasto do ano.";
  if (cm && mun) {
    $("#cont-mun").hidden = false;
    $("#cont-mun-nota").textContent = `Câmaras inteiras (vereadores, servidores e despesas). No Ceará, os órgãos "Gabinete do Prefeito/Vice" ficam fora: registraram ${curto(mun.gabinetes_registrado_ano || 0)} em ${T.ano}, mas incluem comunicação, cerimonial, procuradoria e programas.` +
      (mun.pago_ano && mun.registrado_ano > mun.pago_ano ? ` O contador avança no ritmo do que já foi pago (${curto(mun.pago_ano)}), não do empenhado (${curto(mun.registrado_ano)}): contratos e folha são empenhados de uma vez no começo do ano e pagos aos poucos.` : "") +
      (mun.cobertura < mun.total_municipios ? ` Ainda em coleta: ${mun.cobertura} de ${mun.total_municipios} cidades com dados de ${T.ano}.` : "") +
      (T.esferas.municipios_ba ? ` Bahia (${nf(T.esferas.municipios_ba.cobertura)} de ${nf(T.esferas.municipios_ba.total_municipios)} cidades): dados do Tesouro Nacional, a cada dois meses; o contador avança no ritmo do liquidado (o relatório do Tesouro não traz o pago) e não inclui gabinetes.` : "");
    const b = T.esferas.municipios_ba;
    if (b) $("#cont-mun-rot").innerHTML = `E com as <b>câmaras municipais do Ceará e da Bahia</b> (${nf(mun.total_municipios + b.total_municipios)} cidades) em <span class="ano">${T.ano}</span>`;
  }
  const el = $("#contador");
  const ext = $("#contador-ext");
  const elM = $("#contador-mun"), extM = $("#contador-mun-ext");
  const passo = () => { const t = Date.now(), v = cs.reduce((s, c) => s + valorAgora(c, t), 0); el.textContent = brl(v); ext.textContent = porExtenso(v);
    if (cm) { const vm = cm.reduce((s, c) => s + valorAgora(c, t), 0); elM.textContent = brl(vm); extM.textContent = porExtenso(vm); }
    requestAnimationFrame(passo); };
  passo();
}

function barras(hist) {
  const h = (hist || []).slice(-12), mx = Math.max(...h.map((x) => x[1]), 1);
  return `<div class="barras" aria-hidden="true">${h.map(([a, v, completo]) =>
    `<i class="${completo ? "" : "parcial"}" style="height:${Math.max(4, (v / mx) * 100)}%" title="${a}: ${brl(v)}${completo ? "" : " (parcial)"}"></i>`).join("")}</div>`;
}

// soma, ano a ano, dois históricos [ano, valor, completo] (só os anos que os dois têm)
function somaHist(a, b) {
  const mb = new Map((b || []).map((h) => [h[0], h]));
  return (a || []).filter((h) => mb.has(h[0])).map(([ano, v, c]) => [ano, v + mb.get(ano)[1], c && mb.get(ano)[2]]);
}
function cartao(id, x, T) {
  const e = ESF[id];
  if (!x) return `<article class="cartao" style="--c:${e.cor}"><div class="k">${e.k}</div><h3>${e.nome}</h3><p class="sub">Dados indisponíveis no momento.</p></article>`;
  let quem, inds, aviso = "", avisoDiv = "", partes = "", avisoBa = "", valorRot = `em ${x.ano}`;
  if (id === "deputados") {
    quem = `${nf(x.cadeiras)} deputados · desde ${x.desde}`;
    inds = [[`por deputado, por ano (${x.por_cadeira?.ano ?? "—"})`, x.por_cadeira ? curto(x.por_cadeira.valor) : "—"],
            [`faltas no Plenário em ${x.ano}`, x.faltas_plenario != null ? pct(x.faltas_plenario) : "—"]];
  } else if (id === "senadores") {
    quem = `${nf(x.cadeiras)} senadores · desde ${x.desde}`;
    inds = [[`cota (CEAPS) em ${x.ano}`, curto(x.cota_ano)], ["maior cota do ano", x.maior_cota ? `${curto(x.maior_cota.valor)}` : "—"]];
    if (x.maior_cota) inds[1][0] = `maior cota do ano · ${esc(x.maior_cota.nome)}`;
  } else {
    const comp = x.anos_completos || [], b = T.esferas.municipios_ba;
    const nMun = x.total_municipios + (b?.total_municipios || 0), nVer = (x.vereadores || 0) + (b?.vereadores || 0);
    quem = `${nf(nMun)} municípios${b ? ` (Ceará ${nf(x.total_municipios)} e Bahia ${nf(b.total_municipios)})` : ""}${nVer ? ` · ${nf(nVer)} vereadores` : ""}`;
    valorRot = `câmaras municipais, registrado em ${x.ano}`;
    inds = [[`por vereador, por ano no Ceará (${x.por_vereador?.ano ?? "—"}, valores de hoje) · câmara inteira ÷ vereadores`, x.por_vereador ? curto(x.por_vereador.valor) : "—"],
            ...(b?.por_vereador ? [[`por vereador, por ano na Bahia (${b.por_vereador.ano}, valores de hoje)`, curto(b.por_vereador.valor)]] : []),
            [`gabinetes do prefeito e do vice no Ceará em ${x.ano} (órgão inteiro, fora do total; a Bahia não tem esse dado)`, curto(x.gabinetes_registrado_ano || 0)]];
    if (b) partes = `<p class="partes"><span><b>Ceará</b> ${curto(x.registrado_ano)} · ${nf(x.cobertura)} de ${nf(x.total_municipios)} cidades</span><span><b>Bahia</b> ${curto(b.registrado_ano)} · ${nf(b.cobertura)} de ${nf(b.total_municipios)} cidades${b.bimestre && b.bimestre < 6 ? `, até ${["", "fev", "abr", "jun", "ago", "out", "dez"][b.bimestre]}` : ""}</span></p>`;
    if (b) avisoBa = `<p class="aviso">Bahia: dados do Tesouro Nacional (SICONFI), porque o tribunal de contas dos municípios da Bahia não responde ao nosso robô; sem nota a nota nem gabinetes.${b.bimestre && b.bimestre < 6 ? ` O valor de ${b.ano} é o empenhado até ${["", "fevereiro", "abril", "junho", "agosto", "outubro"][b.bimestre]}, que já fica perto do ano inteiro: as câmaras empenham a folha e os contratos do ano logo no começo.` : ""}${(b.faltas_ano || []).length ? ` Não entregaram o relatório de ${b.ano}: ${esc(b.faltas_ano.join(", "))}.` : ""}</p>`;
    const dv = x.divergencias || {}, tit = (n) => String(n || "").toLowerCase().replace(/(^|\s)(\p{L})/gu, (m) => m.toUpperCase());
    const sb = (dv.sem_balancete || []).map(([n]) => tit(n)), df = (dv.diferenca || []).map(([n]) => tit(n));
    if (sb.length || df.length) avisoDiv = `<p class="aviso diverg">${sb.length ? `<b>Sem balancete enviado ao TCE-CE em ${x.ano}:</b> câmara${sb.length > 1 ? "s" : ""} de ${esc(sb.join(", "))} (valor pela soma das notas de empenho). ` : ""}${df.length ? `<b>Notas e balancete não batem:</b> ${esc(df.join(", "))}. ` : ""}<a href="${x.url}#camaras">ver detalhes</a></p>`;
    if (x.em_coleta) aviso = `<p class="aviso">Em coleta: ${x.cobertura < x.total_municipios ? `${nf(x.cobertura)} de ${nf(x.total_municipios)} cidades têm dados de ${x.ano}. ` : ""}${comp.length ? `Série completa: ${comp[0]}–${comp[comp.length - 1]}; ` : ""}os anos desde 2017 chegam nos próximos dias.</p>`;
  }
  // municípios: o valor JÁ REGISTRADO (o mesmo do mapa); o estimado fica só no contador
  const bMun = id === "municipios" ? T.esferas.municipios_ba : null;
  const valor = id === "municipios" ? (x.cobertura ? curto((x.registrado_ano ?? x.total_ano) + (bMun?.registrado_ano || 0)) : "—") : curto(x.total_ano);
  const hist = bMun ? somaHist(x.historico, bMun.historico) : x.historico;
  return `<article class="cartao" style="--c:${e.cor}">
    <div class="k"><span>${e.k}</span>${e.tag ? `<span class="tag">${e.tag}</span>` : ""}</div>
    <h3>${e.nome}</h3><p class="quem">${quem}</p>
    <div class="valor"><b class="num">${valor}</b><span>${valorRot}${x.meses && x.meses < 12 ? " (até agora)" : ""}</span></div>
    ${partes}${barras(hist)}
    ${aviso}${avisoBa}${avisoDiv}
    <div class="inds">${inds.map(([r, v]) => `<div class="ind"><small>${r}</small><b class="num">${v}</b></div>`).join("")}</div>
    <a class="ir" href="${esc(x.url)}"><span>${e.ir}</span><span aria-hidden="true">→</span></a>
  </article>`;
}

let DAVA_PCT = null;
function dava(T) {
  const D = T.dava, R = window.REFERENCIAS;
  if (!D || !R) { $("#dava").hidden = true; return; }
  const p = DAVA_PCT ?? D.percentual, exc = D.base * p;
  const n = (x) => (x >= 10 ? nf(Math.floor(x)) : x >= 1 ? nf(x, 1) : x >= 0.75 ? "quase 1" : nf(x, 1));
  $("#dava-valor").textContent = curto(exc);
  $("#dava-pct-rot").textContent = nf(p * 100) + "%";
  $("#dava-txt").textContent = `${nf(p * 100)}% do que deputados e senadores gastaram em ${D.ano} com transporte, alimentação, hospedagem e divulgação do mandato (${curto(D.base)}) daria para:`;
  const it = Object.fromEntries(R.itens.map((x) => [x.id, x]));
  const cards = [
    ["escola", "escolas de tempo integral funcionando 1 ano"],
    ["ubs", "UBS construídas e funcionando 1 ano"],
    ["hospital", "hospital(is) de 100 leitos, construído(s) e funcionando 1 ano"],
  ].filter(([id]) => it[id]).map(([id, rot]) => [n(exc / (it[id].construcao + it[id].ano_funcionando)), rot]);
  cards.push([nf(exc / R.bolsa_familia.por_familia_ano / 1000, 1) + " mil", "famílias a mais no Bolsa Família"]);
  $("#dava-itens").innerHTML = cards.map(([v, r]) => `<div class="dava-item"><b class="num">${v}</b><span>${r}</span></div>`).join("");
}

// ---------------------------------------------------------------- mapa por estado
const SITES = {
  dep: "https://quantocustaum.com/quanto-custa-deputados/",
  sen: "https://quantocustaum.com/quanto-custa-senadores/",
  mun: "https://quantocustaum.com/quanto-custa-municipios/",
};
const UF_ROT = { AC: [58, 228], AL: [626, 240, 583, 233], AP: [336, 62], AM: [150, 150], BA: [500, 290], CE: [538, 160], DF: [446, 318, 409, 330],
  ES: [556, 404, 520, 392], GO: [370, 352], MA: [446, 168], MT: [282, 282], MS: [302, 412], MG: [452, 374], PA: [330, 140], PB: [626, 192, 590, 193],
  PR: [352, 478], PE: [626, 216, 572, 213], PI: [482, 196], RJ: [520, 452, 492, 433], RN: [626, 168, 585, 174], RS: [314, 584], RO: [168, 254],
  RR: [188, 56], SC: [364, 530], SP: [400, 446], SE: [626, 264, 573, 247], TO: [402, 228] };
const ESTADO = { sel: "CE", dados: null };

function desenharMapa() {
  const M = window.MAPA_BR, D = ESTADO.dados; if (!M || !D) return;
  const ufs = Object.keys(M.ufs), val = Object.fromEntries(ufs.map((u) => [u, D.ufs[u]?.por_mes || 0]));
  const vs = Object.values(val).filter((v) => v > 0), mn = Math.min(...vs), mx = Math.max(...vs);
  $("#mapa").innerHTML = `<svg viewBox="${M.viewBox}" role="img" aria-label="Mapa do Brasil por estado">${ufs.map((u) => {
      const t = val[u] && mx > mn ? (val[u] - mn) / (mx - mn) : 0.3, c = [222 - 150 * t, 235 - 110 * t, 247 - 60 * t].map(Math.round);
      return `<path d="${M.ufs[u][1]}" data-uf="${u}" tabindex="0" class="${u === ESTADO.sel ? "sel" : ""}" style="fill:rgb(${c})"><title>${M.ufs[u][0]}${val[u] ? " · " + brl(val[u]) + " por político, por mês" : ""}</title></path>`; }).join("")}
    ${ufs.map((u) => { const p = UF_ROT[u]; return p.length > 2 ? `<line x1="${p[0] - 6}" y1="${p[1] - 4}" x2="${p[2]}" y2="${p[3]}" class="uf-linha"/>` : ""; }).join("")}
    ${ufs.map((u) => { const p = UF_ROT[u], t = val[u] && mx > mn ? (val[u] - mn) / (mx - mn) : 0.3;
      return `<text x="${p[0]}" y="${p[1]}" data-uf="${u}" class="uf-rot${p.length > 2 ? " fora" : (u === ESTADO.sel || t > 0.62 ? " claro" : "")}${u === ESTADO.sel ? " sel" : ""}">${u}</text>`; }).join("")}</svg>
    <p class="mapa-leg">Mais claro: ${brl(mn)} · mais escuro: ${brl(mx)} por político federal, por mês (diferença de ${nf((mx / mn - 1) * 100)}%). Deputados incluem a equipe do gabinete; senadores ainda não (o Senado não publica esse valor), por isso estados com mais senadores proporcionalmente aparecem mais claros.</p>`;
}

function painelUF() {
  const u = ESTADO.sel, x = ESTADO.dados?.ufs[u], M = window.MAPA_BR; if (!x || !M) return;
  const ano = ESTADO.dados.ano;
  const linha = (tag, cor, txt, v, cls = "") => `<tr><td>${tag ? `<span class="t" style="--c:${cor}">${tag}</span>` : ""}${txt}</td><td class="v ${cls}">${v}</td></tr>`;
  let rows = linha("DEP", "var(--dep)", `${nf(x.dep.n)} deputados federais`, curto(x.dep.custo)) +
             linha("SEN", "var(--sen)", `${nf(x.sen.n)} senadores`, curto(x.sen.custo));
  if (x.mun) {
    const m = x.mun, completo = m.com_dados >= m.total;
    rows += linha("MUN", "var(--mun)", `${nf(m.total)} câmaras municipais (registrado)${completo ? "" : ` <small class="sub">(em coleta: ${nf(m.com_dados)} de ${nf(m.total)})</small>`}`, m.com_dados ? curto(m.custo) : "—");
    if (m.gabinetes) rows += linha("", "", `Gabinetes do prefeito e do vice <small class="sub">(órgão inteiro, fora do custo dos políticos)</small>`, curto(m.gabinetes));
    if (m.emendas != null) rows += linha("", "", "Emendas recebidas pelos municípios", m.com_dados ? curto(m.emendas) : "—");
    if (m.fonte === "SICONFI") rows += linha("", "", `<span class="sub">Dados do Tesouro Nacional (SICONFI): sem gabinetes nem emendas para este estado.</span>`, "");
    if (x.por_habitante) rows += linha("", "", "Por habitante, no ano", brl(x.por_habitante, 2), "vermelho");
  } else {
    rows += linha("", "", `<span class="sub">Prefeitos e vereadores deste estado ainda não estão no projeto (por enquanto, Ceará e Bahia).</span>`, "");
  }
  rows += linha("", "", "Custo médio por político federal, por mês", x.por_mes ? brl(x.por_mes) : "—");
  $("#uf-painel").innerHTML = `<div class="uf-cab"><small>Estado selecionado · ${ano} até agora</small><h3>${esc(M.ufs[u][0])}</h3></div>
    <table class="uf-linhas"><tbody>${rows}</tbody></table>
    <div class="uf-links"><a href="${SITES.dep}?uf=${u}&pag=deputados">Deputados de ${u} →</a><a class="sec2" href="${SITES.sen}?uf=${u}#senadores">Senadores de ${u} →</a>${x.mun ? `<a class="sec2" href="${SITES.mun}${u === "CE" ? "" : "?uf=" + u.toLowerCase()}">Cidades ${u === "BA" ? "da Bahia" : "do Ceará"} →</a>` : ""}</div>`;
}

async function iniciarEstados() {
  try { const r = await fetch("dados/estados.json", { cache: "no-cache" }); if (!r.ok) throw 0; ESTADO.dados = await r.json(); }
  catch { $("#estados").hidden = true; return; }
  document.querySelectorAll(".ano-mapa").forEach((e) => (e.textContent = ESTADO.dados.ano));
  desenharMapa(); painelUF();
  const escolher = (u) => { if (!u || !ESTADO.dados.ufs[u]) return; ESTADO.sel = u; desenharMapa(); painelUF(); };
  $("#mapa").addEventListener("click", (e) => escolher(e.target.closest("[data-uf]")?.dataset.uf));
  $("#mapa").addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); escolher(e.target.dataset?.uf); } });
}

// ---------------------------------------------------------------- destaques (fase 3)
const COR_ESF = { DEP: "var(--dep)", SEN: "var(--sen)", MUN: "var(--mun)" };
const dataCurta = (iso) => (iso ? iso.slice(8, 10) + "/" + iso.slice(5, 7) : "");
const fmtCnpj = (c) => c.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
let DEST = null;
async function carregarDestaques() {
  if (DEST) return DEST;
  try { const r = await fetch("dados/destaques.json", { cache: "no-cache" }); DEST = r.ok ? await r.json() : {}; } catch { DEST = {}; }
  return DEST;
}
async function iniciarDestaques() {
  const D = await carregarDestaques();
  if (!D.ano) { $("#destaques").hidden = true; return; }
  const ns = D.notas_semana || [];
  $("#top-notas").innerHTML = ns.length ? ns.map(([e, v, oque, quem, onde, data, url, qtd]) =>
    `<li><span class="o"><a href="${esc(url)}">${esc(oque)}</a><span class="q"><span class="etq" style="--c:${COR_ESF[e]}">${e}</span>${esc(quem)} · ${esc(onde)}${data ? " · " + dataCurta(data) : ""}${qtd > 1 ? ` · <b>${qtd} notas iguais</b> de ${brl(v / qtd, 2)}` : ""}</span></span><span class="v num">${brl(v, 2)}</span></li>`).join("")
    : `<li class="sub">Sem notas publicadas nos últimos dias.</li>`;
  const J = D.janelas || {}, rot = { deputados: "deputados", senadores: "senadores", municipios: "municípios" };
  const jt = Object.entries(J).map(([k, [a, b]]) => `${rot[k]} de ${dataCurta(a)} a ${dataCurta(b)}`);
  if (jt.length) $("#top-notas-sub").textContent = `as maiores notas emitidas na última semana com dados publicados · ${jt.join(" · ")}`;
  const ms = D.multi_esfera || [];
  $("#multi").innerHTML = ms.length ? ms.slice(0, 5).map(([raiz, nome, c14, tot, dep, sen, mun, filiais]) => {
    const q = [dep[0] ? `<span class="etq" style="--c:var(--dep)">DEP</span>${nf(dep[1])} deputado(s)` : "",
               sen[0] ? `<span class="etq" style="--c:var(--sen)">SEN</span>${nf(sen[1])} senador(es)` : "",
               mun[0] ? `<span class="etq" style="--c:var(--mun)">MUN</span>${nf(mun[1])} prefeitura(s)${mun[2] ? ` · ${nf(mun[2])} câmara(s)` : ""}` : ""].filter(Boolean).join(" · ");
    return `<li><span class="o"><button class="link" data-cnpj="${c14}">${esc(nome)}</button><span class="q">${q}${filiais > 1 ? ` · ${nf(filiais)} CNPJs (matriz e filiais)` : ""}</span></span><span class="v num">${curto(tot)}</span></li>`; }).join("")
    : `<li class="sub">Nenhuma empresa paga por mais de uma esfera em ${D.ano} até agora.</li>`;
}

// ficha rápida de uma empresa (índice de CNPJ do Mensageiro)
const GRUPOS = {};
async function cnpjGrupo(pref) {
  if (!GRUPOS[pref]) GRUPOS[pref] = fetch(`dados/cnpj/${pref}.json`, { cache: "no-cache" }).then((r) => (r.ok ? r.json() : {})).catch(() => ({}));
  return GRUPOS[pref];
}
async function abrirEmpresa(c14) {
  const g = await cnpjGrupo(c14.slice(0, 2)), x = g[c14], ano = (await carregarDestaques()).ano || "";
  const corpo = $("#empresa-corpo");
  if (!x) { corpo.innerHTML = `<h3>${fmtCnpj(c14)}</h3><p class="sub">Este CNPJ não recebeu da cota de deputados e senadores nem das prefeituras do Ceará em ${ano}.</p>`; }
  else {
    const [nome, dep, sen, mun, cidades, nCid] = x;
    const linha = (etq, cor, txt, v, lk) => `<tr><td><span class="etq" style="--c:${cor}">${etq}</span>${txt}${v && lk ? `<a href="${lk}">ver notas →</a>` : ""}</td><td class="v">${v ? brl(v, 2) : "—"}</td></tr>`;
    corpo.innerHTML = `<p class="sub">Empresa · ${ano}</p><h3>${esc(nome)}</h3><p class="sub">CNPJ ${fmtCnpj(c14)}</p>
      <table><tbody>
      ${linha("DEP", "var(--dep)", "Cota dos deputados federais", dep, `${SITES.dep}?ano=${ano}#forn-${c14}`)}
      ${linha("SEN", "var(--sen)", "Cota dos senadores", sen, `${SITES.sen}?ano=${ano}#forn-${c14}`)}
      ${linha("MUN", "var(--mun)", `Prefeituras do Ceará${nCid ? ` (${nf(nCid)} cidade(s))` : ""}`, mun, "")}
      ${cidades.map(([sim, cid, v]) => `<tr><td style="padding-left:18px"><a href="${SITES.mun}#municipio/${sim}" style="margin:0">${esc(cid)}</a></td><td class="v">${brl(v, 2)}</td></tr>`).join("")}
      </tbody></table>
      <p class="sub">Valores de ${ano} até agora, como publicados. O cadastro da empresa na Receita Federal (sócios, abertura, situação) está na ficha do fornecedor nos sites de deputados e senadores.</p>`;
  }
  $("#empresa").showModal();
}

// ---------------------------------------------------------------- busca
const TIPOS = { E: ["EMPRESA", "#5B6B7E"], D: ["DEP", "var(--dep)"], S: ["SEN", "var(--sen)"], P: ["PREF", "var(--mun)"], V: ["VER", "var(--mun)"], C: ["CIDADE", "#5B6B7E"] };
const ORDEM = { D: 0, S: 1, C: 2, P: 3, V: 4, E: 5 };
const norm = (s) => (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
let BUSCA = null;
async function carregarBusca() {
  if (BUSCA) return BUSCA;
  try { const r = await fetch("dados/busca.json", { cache: "no-cache" }); BUSCA = (await r.json()).map((x) => [...x, norm(x[1] + " " + x[2])]); }
  catch { BUSCA = []; }
  // empresas: as maiores do ano (busca por nome); por CNPJ, a busca usa o índice completo
  const D = await carregarDestaques();
  (D.empresas || []).forEach(([c, nome]) => BUSCA.push(["E", nome, fmtCnpj(c), c, norm(nome + " " + c)]));
  return BUSCA;
}
function link(x) {
  if (x[0] === "E") return "#";
  if (x[0] === "D") return `${SITES.dep}?ano=total#dep-${x[3]}`;
  if (x[0] === "S") return `${SITES.sen}?ano=${x[4]}#sen-${x[3]}`;
  return `${SITES.mun}#municipio/${x[3]}`;
}
async function buscar() {
  const q = norm($("#busca-q").value.trim()), ul = $("#busca-lista");
  if (q.length < 2) { ul.hidden = true; return []; }
  const dig = q.replace(/\D/g, "");
  if (dig.length >= 8 && dig.length >= q.replace(/[\s./-]/g, "").length - 1) {          // CNPJ
    const g = await cnpjGrupo(dig.slice(0, 2));
    const r = Object.entries(g).filter(([c]) => c.startsWith(dig)).slice(0, 12).map(([c, x]) => ["E", x[0], fmtCnpj(c), c]);
    ul.innerHTML = r.length ? r.map((x, i) => `<li><a href="#" data-cnpj="${x[3]}" class="${i ? "" : "ativo"}"><span class="t" style="--c:#5B6B7E">CNPJ</span><span>${esc(x[1])}<small>${x[2]}</small></span></a></li>`).join("")
      : `<li class="vazio">Nenhum pagamento a este CNPJ em ${(await carregarDestaques()).ano || "este ano"} nas três esferas.</li>`;
    ul.hidden = false;
    return r;
  }
  const L = await carregarBusca(), ps = q.split(/\s+/);
  const nomeN = (x) => x[x.length - 1];
  const r = L.filter((x) => ps.every((p) => nomeN(x).includes(p)))
    .sort((a, b) => (norm(b[1]).startsWith(q) - norm(a[1]).startsWith(q)) || ORDEM[a[0]] - ORDEM[b[0]] || (a[2].startsWith("vice") - b[2].startsWith("vice")) || a[1].localeCompare(b[1])).slice(0, 12);
  ul.innerHTML = r.length ? r.map((x, i) => { const [t, c] = TIPOS[x[0]];
      return `<li><a href="${link(x)}"${x[0] === "E" ? ` data-cnpj="${x[3]}"` : ""} class="${i ? "" : "ativo"}"><span class="t" style="--c:${c}">${t}</span><span>${esc(x[1])}<small>${esc(x[2])}</small></span></a></li>`; }).join("")
    : `<li class="vazio">Nada encontrado. Tente o nome de urna ou o nome da cidade.</li>`;
  ul.hidden = false;
  return r;
}

async function iniciar() {
  let T;
  try {
    const r = await fetch("dados/totais_hub.json", { cache: "no-cache" });
    if (!r.ok) throw new Error(r.status);
    T = await r.json();
  } catch {
    $("#contador").textContent = "—";
    $("#cont-nota").textContent = "Os totais ainda estão sendo preparados pelo robô. Volte em alguns minutos.";
    $("#cartoes").innerHTML = Object.keys(ESF).map((k) => cartao(k, null)).join("");
    return;
  }
  contador(T);
  comparar(T);
  const sl = $("#dava-pct"); if (sl) { if (T.dava) sl.value = Math.round(T.dava.percentual * 100); sl.oninput = () => { DAVA_PCT = sl.value / 100; dava(T); }; }
  $("#cartoes").innerHTML = ["deputados", "senadores", "municipios"].map((k) => cartao(k, T.esferas[k], T)).join("");
  dava(T);
  const at = Object.entries(T.esferas).map(([k, v]) => v.atualizado_em ? `${ESF[k]?.nome || (k === "municipios_ba" ? "Prefeituras da Bahia" : k)}: ${new Date(v.atualizado_em).toLocaleString("pt-BR")}` : "").filter(Boolean);
  $("#atualizacao").textContent = `Totais reunidos em ${new Date(T.gerado_em).toLocaleString("pt-BR")}. Última atualização de cada site — ${at.join(" · ")}.`;
}

$("#busca-q").addEventListener("input", buscar);
$("#busca-q").addEventListener("focus", () => { carregarBusca(); if ($("#busca-q").value.trim().length >= 2) buscar(); });
$("#busca").addEventListener("submit", async (e) => { e.preventDefault(); const ativo = document.querySelector("#busca-lista a.ativo");
  if (ativo) { ativo.click(); return; }
  const r = await buscar(); if (r.length) document.querySelector("#busca-lista a")?.click(); });
document.addEventListener("click", (e) => {
  const c = e.target.closest("[data-cnpj]"); if (!c) return;
  e.preventDefault(); $("#busca-lista").hidden = true; abrirEmpresa(c.dataset.cnpj);
});
$("#empresa-fechar").onclick = () => $("#empresa").close();
$("#empresa").addEventListener("click", (e) => { if (e.target.id === "empresa") $("#empresa").close(); });
document.addEventListener("click", (e) => { if (!e.target.closest("#busca")) $("#busca-lista").hidden = true; });
$("#busca-q").addEventListener("keydown", (e) => {
  const as = [...document.querySelectorAll("#busca-lista a")]; if (!as.length || !["ArrowDown", "ArrowUp"].includes(e.key)) return;
  e.preventDefault(); let i = as.findIndex((a) => a.classList.contains("ativo")); as[i]?.classList.remove("ativo");
  i = (i + (e.key === "ArrowDown" ? 1 : -1) + as.length) % as.length; as[i].classList.add("ativo"); as[i].scrollIntoView({ block: "nearest" });
});
$("#hamb").onclick = () => { const m = $("#menu"), a = m.classList.toggle("aberto"); $("#hamb").setAttribute("aria-expanded", String(a)); };
$("#menu").onclick = (e) => { if (e.target.tagName === "A") { $("#menu").classList.remove("aberto"); $("#hamb").setAttribute("aria-expanded", "false"); } };
iniciar();
iniciarEstados();
iniciarDestaques();
})();

// menu "Deputados": no toque (sem mouse), o botão abre e fecha a lista
(() => {
  const sm = document.getElementById("sub-dep"); if (!sm) return;
  const b = sm.querySelector(".sub-bot");
  b.addEventListener("click", (e) => { e.stopPropagation(); const a = sm.classList.toggle("aberto"); b.setAttribute("aria-expanded", String(a)); });
  document.addEventListener("click", (e) => { if (!sm.contains(e.target)) { sm.classList.remove("aberto"); b.setAttribute("aria-expanded", "false"); } });
})();
