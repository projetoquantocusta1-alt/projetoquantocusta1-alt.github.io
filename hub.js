/* Projeto Quanto Custa — hub. Só lê dados/totais_hub.json (feito pelo Mensageiro). */
(() => {
"use strict";
const $ = (s) => document.querySelector(s);
const nf = (v, d = 0) => (v || 0).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const brl = (v, d = 0) => "R$ " + nf(v, d);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const curto = (v) => { const a = Math.abs(v || 0);
  if (a >= 1e9) return "R$ " + nf(v / 1e9, 2) + " bi";
  if (a >= 1e6) return "R$ " + nf(v / 1e6, a >= 1e8 ? 0 : 1) + " mi";
  if (a >= 1e3) return "R$ " + nf(v / 1e3, 0) + " mil";
  return brl(v, 2); };
const pct = (x) => nf(x * 100, 1) + "%";
const dataLocal = (iso) => { const [a, m, d] = iso.split("-").map(Number); return new Date(a, m - 1, d).getTime(); };

const ESF = {
  deputados: { cor: "var(--dep)", k: "Câmara dos Deputados", nome: "Deputados federais", ir: "Ver deputados, notas e presença" },
  senadores: { cor: "var(--sen)", k: "Senado Federal", nome: "Senadores", ir: "Ver senadores e cada nota" },
  municipios: { cor: "var(--mun)", k: "Prefeituras e câmaras", nome: "Prefeitos e vereadores", ir: "Ver minha cidade, nota a nota", tag: "Ceará" },
};

function valorAgora(c, t) {
  if (!c) return 0;
  const ini = dataLocal(c.inicio);
  return Math.min(c.teto || c.ja, c.ja + Math.max(0, (t - ini) / 1000) * (c.por_seg || 0));
}

function contador(T) {
  const cs = Object.values(T.contador || {});
  const porSeg = cs.reduce((s, c) => s + (c.por_seg || 0), 0);
  $("#cont-rot .ano").textContent = T.ano;
  $("#cont-ritmo").innerHTML = porSeg ? `+ <b>${brl(porSeg, 2)}</b> por segundo · <b>${curto(porSeg * 86400)}</b> por dia` : "";
  const mun = T.esferas.municipios;
  $("#cont-nota").textContent = "Valor estimado em tempo real: soma o que já foi registrado e avança no ritmo de gasto do ano." +
    (mun && mun.em_coleta ? ` Municípios do Ceará: ${mun.cobertura} de ${mun.total_municipios} já têm dados de ${T.ano} (o robô ainda está coletando).` : "");
  const el = $("#contador");
  const passo = () => { el.textContent = brl(cs.reduce((s, c) => s + valorAgora(c, Date.now()), 0)); requestAnimationFrame(passo); };
  passo();
}

function barras(hist) {
  const h = (hist || []).slice(-12), mx = Math.max(...h.map((x) => x[1]), 1);
  return `<div class="barras" aria-hidden="true">${h.map(([a, v, completo]) =>
    `<i class="${completo ? "" : "parcial"}" style="height:${Math.max(4, (v / mx) * 100)}%" title="${a}: ${brl(v)}${completo ? "" : " (parcial)"}"></i>`).join("")}</div>`;
}

function cartao(id, x, T) {
  const e = ESF[id];
  if (!x) return `<article class="cartao" style="--c:${e.cor}"><div class="k">${e.k}</div><h3>${e.nome}</h3><p class="sub">Dados indisponíveis no momento.</p></article>`;
  let quem, inds, aviso = "", valorRot = `em ${x.ano}`;
  if (id === "deputados") {
    quem = `${nf(x.cadeiras)} deputados · desde ${x.desde}`;
    inds = [[`por deputado, por ano (${x.por_cadeira?.ano ?? "—"})`, x.por_cadeira ? curto(x.por_cadeira.valor) : "—"],
            [`faltas no Plenário em ${x.ano}`, x.faltas_plenario != null ? pct(x.faltas_plenario) : "—"]];
  } else if (id === "senadores") {
    quem = `${nf(x.cadeiras)} senadores · desde ${x.desde}`;
    inds = [[`cota (CEAPS) em ${x.ano}`, curto(x.cota_ano)], ["maior cota do ano", x.maior_cota ? `${curto(x.maior_cota.valor)}` : "—"]];
    if (x.maior_cota) inds[1][0] = `maior cota do ano · ${esc(x.maior_cota.nome)}`;
  } else {
    quem = `${nf(x.total_municipios)} municípios${x.vereadores ? ` · ${nf(x.vereadores)} vereadores` : ""} · desde ${x.desde}`;
    valorRot = `câmaras + gabinetes em ${x.ano}`;
    inds = [[`por vereador, por ano (${x.por_vereador?.ano ?? "—"})`, x.por_vereador ? curto(x.por_vereador.valor) : "—"],
            [`municípios com dados de ${x.ano}`, `${nf(x.cobertura)} de ${nf(x.total_municipios)}`]];
    if (x.em_coleta) aviso = `<p class="aviso">Em coleta: o robô do TCE-CE ainda está buscando os dados das ${nf(x.total_municipios)} cidades. Os valores crescem nos próximos dias.</p>`;
  }
  const valor = id === "municipios" && !x.cobertura ? "—" : curto(x.total_ano);
  return `<article class="cartao" style="--c:${e.cor}">
    <div class="k"><span>${e.k}</span>${e.tag ? `<span class="tag">${e.tag}</span>` : ""}</div>
    <h3>${e.nome}</h3><p class="quem">${quem}</p>
    <div class="valor"><b class="num">${valor}</b><span>${valorRot}${x.meses && x.meses < 12 ? " (até agora)" : ""}</span></div>
    ${barras(x.historico)}
    ${aviso}
    <div class="inds">${inds.map(([r, v]) => `<div class="ind"><small>${r}</small><b class="num">${v}</b></div>`).join("")}</div>
    <a class="ir" href="${esc(x.url)}"><span>${e.ir}</span><span aria-hidden="true">→</span></a>
  </article>`;
}

function dava(T) {
  const D = T.dava, R = window.REFERENCIAS;
  if (!D || !R) { $("#dava").hidden = true; return; }
  const exc = D.excesso, n = (x) => (x >= 10 ? nf(Math.floor(x)) : nf(x, 1));
  $("#dava-valor").textContent = curto(exc);
  $("#dava-txt").textContent = `${nf(D.percentual * 100)}% do que deputados e senadores gastaram em ${D.ano} com transporte, alimentação, hospedagem e divulgação do mandato daria para:`;
  const it = Object.fromEntries(R.itens.map((x) => [x.id, x]));
  const cards = [
    ["escola", "escolas de tempo integral funcionando 1 ano"],
    ["ubs", "UBS construídas e funcionando 1 ano"],
    ["hospital", "hospital de 100 leitos por 1 ano"],
  ].filter(([id]) => it[id]).map(([id, rot]) => [n(exc / (it[id].construcao + it[id].ano_funcionando)), rot]);
  cards.push([nf(exc / R.bolsa_familia.por_familia_ano / 1000, 1) + " mil", "famílias a mais no Bolsa Família"]);
  $("#dava-itens").innerHTML = cards.map(([v, r]) => `<div class="dava-item"><b class="num">${v}</b><span>${r}</span></div>`).join("");
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
  $("#cartoes").innerHTML = ["deputados", "senadores", "municipios"].map((k) => cartao(k, T.esferas[k], T)).join("");
  dava(T);
  const at = Object.entries(T.esferas).map(([k, v]) => v.atualizado_em ? `${ESF[k].nome}: ${new Date(v.atualizado_em).toLocaleString("pt-BR")}` : "").filter(Boolean);
  $("#atualizacao").textContent = `Totais reunidos em ${new Date(T.gerado_em).toLocaleString("pt-BR")}. Última atualização de cada site — ${at.join(" · ")}.`;
}

$("#hamb").onclick = () => { const m = $("#menu"), a = m.classList.toggle("aberto"); $("#hamb").setAttribute("aria-expanded", String(a)); };
$("#menu").onclick = (e) => { if (e.target.tagName === "A") { $("#menu").classList.remove("aberto"); $("#hamb").setAttribute("aria-expanded", "false"); } };
iniciar();
})();
