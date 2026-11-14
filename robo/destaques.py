"""Fase 3 do hub: notas da semana, fornecedores em mais de uma esfera e índice de CNPJ.

Roda uma vez por dia (parte "pesada" do Mensageiro: lê as notas e os fornecedores
publicados pelos três sites). Saídas:
    dados/destaques.json      -> 5 maiores notas da última semana com notas publicadas (todas as esferas) e
                                 fornecedores pagos em mais de uma esfera no ano
    dados/cnpj/XX.json        -> índice de CNPJ do ano (XX = 2 primeiros dígitos)

"Notas da semana": em cada esfera, as notas emitidas nos 7 dias que terminam na nota mais
recente já publicada (cada esfera publica com um atraso diferente). Folha de pessoal das
prefeituras não entra (vem em lote, sem nome).
"""
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from privacidade import mascarar_cpf_no_texto as mascara

RAIZ = Path(__file__).resolve().parents[1]
DIAS = 7


def r2(x):
    return round(float(x or 0), 2)


def _gravar(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), "utf-8")


def _raiz(c: str) -> str:
    return c[:8]


# ------------------------------------------------------------------ últimas notas da semana
def _janela(notas: list[list], hoje: date) -> tuple[list[list], list[str]]:
    """Notas emitidas nos 7 dias que terminam na nota mais recente já publicada (até hoje).
    Cada esfera publica com atraso diferente; assim a lista nunca fica vazia."""
    datas = [n[5] for n in notas if n[5] and n[5] <= hoje.isoformat()]
    if not datas:
        return [], []
    fim = max(datas)
    ini = (date.fromisoformat(fim) - timedelta(days=DIAS - 1)).isoformat()
    return [n for n in notas if n[5] and ini <= n[5] <= fim], [ini, fim]


def ultimas_deputados(fd, ano: int, site: str) -> list[list]:
    out = []
    for d in (fd.get(f"{ano}/resumo.json") or {}).get("deputados") or []:
        x = fd.get(f"{ano}/notas/{d['id']}.json") or {}
        forn, cats = x.get("f") or [], x.get("c") or []
        for n in x.get("n") or []:
            mmdd = n[0]
            if not mmdd % 100:
                continue                     # nota sem dia de emissão
            f = forn[n[2]] if n[2] < len(forn) else ["", ""]
            out.append(["DEP", round(n[1] / 100, 2), f"{cats[n[3]] if n[3] < len(cats) else ''} — {f[1]}", d.get("nome", ""),
                        f"Deputado(a) · {d.get('uf', '')}", f"{ano}-{mmdd // 100:02d}-{mmdd % 100:02d}", f"{site}?ano={ano}#dep-{d['id']}"])
    return out


def ultimas_senadores(fs, ano: int, site: str) -> list[list]:
    out = []
    for s in (fs.get(f"{ano}/resumo.json") or {}).get("senadores") or []:
        d = fs.get(f"{ano}/notas/{s['id']}.json") or {}
        fz = d.get("fornecedores") or {}
        link = f"{site}?ano={ano}#sen-{s['id']}" if isinstance(s["id"], int) else site
        for n in d.get("notas") or []:
            f = fz.get(n[3]) or ["", ""]
            out.append(["SEN", r2(n[4]), f"{n[2]} — {f[1]}", s.get("nome", ""), f"Senador(a) · {s.get('uf', '')}", n[0], link])
    return out


def ultimas_municipios(fm, ano: int, site: str) -> list[list]:
    out = []
    for m in (fm.get("resumo.json") or {}).get("municipios") or []:
        if str(ano) not in (m.get("anos") or {}):
            continue
        d = fm.get(f"n/{m['sim']}/{ano}.json") or {}
        fz, orgs = d.get("forn") or [], d.get("orgaos") or {}
        for e in d.get("emp") or []:
            if (e[3] or "")[1:2] == "1":
                continue                     # folha de pessoal (vem em lote, sem nome)
            papel = (orgs.get(e[0]) or ["", ""])[1]
            onde = {"camara": "Câmara", "prefeito": "Gabinete do prefeito", "vice": "Gabinete do vice"}.get(papel, "Órgão")
            f = fz[e[4]] if e[4] < len(fz) else [""]
            hist = (e[8] or "").strip()
            oque = f"{hist[:60]}{'…' if len(hist) > 60 else ''} — {f[0]}" if hist else f[0]
            out.append(["MUN", r2((e[5] or 0) - (e[6] or 0)), oque, m["nome"].title(), f"{onde} de {m['nome'].title()}", e[1],
                        f"{site}#municipio/{m['sim']}"])
    return out


# ------------------------------------------------------------------ fornecedores
def fornecedores(fd, fs, fm, ano: int) -> dict:
    """{raiz do CNPJ: {...}} com o que cada esfera pagou no ano. Agrupa filiais pela raiz (8 dígitos)."""
    g: dict[str, dict] = {}

    def item(c14, nome):
        x = g.setdefault(_raiz(c14), {"nome": nome, "cnpjs": set(), "dep": [0.0, 0], "sen": [0.0, 0],
                                      "mun": [0.0, set(), set()], "maior": 0.0})
        x["cnpjs"].add(c14)
        return x
    idx14: dict[str, dict] = {}

    def i14(c14, nome):
        return idx14.setdefault(c14, {"nome": nome, "dep": 0.0, "sen": 0.0, "mun": 0.0, "cidades": defaultdict(float)})

    for ln in (fd.get(f"{ano}/fornecedores.json") or {}).get("linhas") or []:
        c, nome, tipo, valor, ndep = ln[0], ln[1], ln[3], ln[5], ln[7]
        if tipo != "PJ" or len(c) != 14 or not c.isdigit():
            continue
        x = item(c, nome)
        x["dep"][0] += valor
        x["dep"][1] = max(x["dep"][1], ndep)
        if valor > x["maior"]:
            x["maior"], x["nome"] = valor, nome
        i14(c, nome)["dep"] += valor
    for ln in (fs.get(f"{ano}/fornecedores.json") or {}).get("linhas") or []:
        c, nome, tipo, valor, sens = ln[0], ln[1], ln[3], ln[4], ln[6]
        if tipo != "PJ" or len(c) != 14 or not c.isdigit():
            continue
        x = item(c, nome)
        x["sen"][0] += valor
        x["sen"][1] = max(x["sen"][1], len(sens))
        if valor > x["maior"]:
            x["maior"], x["nome"] = valor, nome
        i14(c, nome)["sen"] += valor
    for m in (fm.get("resumo.json") or {}).get("municipios") or []:
        if str(ano) not in (m.get("anos") or {}):
            continue
        sim = m["sim"]
        # índice de CNPJ (busca): o que a prefeitura inteira pagou
        for ln in (fm.get(f"f/{sim}/{ano}.json") or {}).get("linhas") or []:
            nome, c, tipo, valor = ln[0], ln[1], ln[2], ln[4]
            if tipo != "PJ" or len(c or "") != 14:
                continue
            y = i14(c, nome)
            y["mun"] += valor
            y["cidades"][sim] += valor
        # fornecedores em mais de uma esfera: só o que a CÂMARA e os GABINETES pagaram (mesmo escopo dos políticos)
        nd = fm.get(f"n/{sim}/{ano}.json") or {}
        orgs, fz = nd.get("orgaos") or {}, nd.get("forn") or []
        for e in nd.get("emp") or []:
            f = fz[e[4]] if e[4] < len(fz) else None
            if not f or len(f[1] or "") != 14:
                continue
            liq = (e[5] or 0) - (e[6] or 0)
            x = item(f[1], f[0])
            x["mun"][0] += liq
            x["mun"][1].add(sim)
            if (orgs.get(e[0]) or ["", ""])[1] == "camara":
                x["mun"][2].add(sim)
            if liq > x["maior"]:
                x["maior"], x["nome"] = liq, f[0]
    return g, idx14


# serviços tarifados e instituições cujo pagamento por várias esferas é esperado (não informa nada)
_ESPERADOS = re.compile(r"\b(ENEL|COELCE|ENERGISA|EQUATORIAL|NEOENERGIA|CEMIG|COPEL|LIGHT|CELPE|COSERN|CPFL|ELETRO|ENERGIA ELETRICA|"
                        r"COMPANHIA ENERGETICA|CAGECE|SANEAMENTO|SABESP|COMPESA|CAERN|AGUA E ESGOTO|BANCO|CAIXA ECONOMICA|BANRISUL|"
                        r"CORREIOS|EMPRESA BRASILEIRA DE CORREIOS|SANTA CASA|HOSPITAL|IRMANDADE|BENEFICENCIA|"
                        r"TAM LINHAS|LATAM|GOL LINHAS|AZUL LINHAS|VRG|AVIANCA|TELEFONICA|TELEMAR|OI S|CLARO|TIM S|"
                        r"RECEITA FEDERAL|PREVIDENCIA|INSTITUTO NACIONAL DO SEGURO|MUNICIPIO DE|PREFEITURA|GOVERNO DO ESTADO|"
                        r"CELULAR FUNCIONAL|CAMARA DOS DEPUTADOS|SENADO FEDERAL|CAMARA MUNICIPAL)\b")


def esperado(nome: str) -> bool:
    n = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().upper()
    return bool(_ESPERADOS.search(n))


def multi_esfera(g: dict, nomes_mun: dict, limite: int = 20) -> list[list]:
    """Empresas pagas por mais de uma esfera (municípios: só câmara e gabinetes), sem os serviços tarifados,
    bancos, Correios, companhias aéreas, hospitais e órgãos públicos."""
    out = []
    for raiz, x in g.items():
        if esperado(x["nome"]):
            continue
        esf = (x["dep"][0] > 0) + (x["sen"][0] > 0) + (x["mun"][0] > 0)
        if esf < 2:
            continue
        tot = x["dep"][0] + x["sen"][0] + x["mun"][0]
        out.append([raiz, x["nome"], sorted(x["cnpjs"])[0], r2(tot),
                    [r2(x["dep"][0]), x["dep"][1]], [r2(x["sen"][0]), x["sen"][1]],
                    [r2(x["mun"][0]), len(x["mun"][1]), len(x["mun"][2])], len(x["cnpjs"])])
    return sorted(out, key=lambda z: -z[3])[:limite]


def indice_cnpj(idx14: dict, nomes_mun: dict) -> dict[str, dict]:
    """{XX: {cnpj14: [nome, deputados, senadores, municípios, [[sim, cidade, valor] x5]]}}."""
    grupos: dict[str, dict] = defaultdict(dict)
    for c, y in idx14.items():
        cid = sorted(y["cidades"].items(), key=lambda t: -t[1])[:5]
        grupos[c[:2]][c] = [y["nome"], r2(y["dep"]), r2(y["sen"]), r2(y["mun"]),
                            [[s, nomes_mun.get(s, s), r2(v)] for s, v in cid], len(y["cidades"])]
    return grupos


def gerar(fd, fs, fm, ano: int, hoje: date, sites: dict, saida: Path) -> dict:
    status = {}
    notas, janelas = [], {}
    for nome, fn in (("deputados", lambda: ultimas_deputados(fd, ano, sites["deputados"])),
                     ("senadores", lambda: ultimas_senadores(fs, ano, sites["senadores"])),
                     ("municipios", lambda: ultimas_municipios(fm, ano, sites["municipios"]))):
        try:
            v, jan = _janela(fn(), hoje)
            notas += v
            if jan:
                janelas[nome] = jan
            status[f"notas_{nome}"] = f"ok ({len(v)} notas de {jan[0]} a {jan[1]})" if jan else "sem notas"
        except Exception as e:  # noqa: BLE001
            status[f"notas_{nome}"] = f"erro ({e})"
    nomes_mun = {m["sim"]: m["nome"].title() for m in (fm.get("resumo.json") or {}).get("municipios") or []}
    g, idx14 = fornecedores(fd, fs, fm, ano)
    multi = multi_esfera(g, nomes_mun)
    grupos = indice_cnpj(idx14, nomes_mun)
    if grupos:
        for p in (saida / "cnpj").glob("*.json"):
            if p.stem not in grupos:
                p.unlink()
        for k, v in grupos.items():
            _gravar(saida / "cnpj" / f"{k}.json", v)
    notas = [[e, v, mascara(o), mascara(q), onde, d, u] for e, v, o, q, onde, d, u in notas]
    # notas iguais (mesma pessoa, fornecedor, dia e valor) viram uma linha "2 notas"
    grp = {}
    for n in notas:
        k = (n[0], n[2], n[3], n[5], n[1])
        if k in grp:
            grp[k][7] += 1
        else:
            grp[k] = n + [1]
    notas = [n[:1] + [round(n[1] * n[7], 2)] + n[2:7] + [n[7]] for n in grp.values()]
    dest = {"ano": ano, "gerado_em": hoje.isoformat(), "notas_semana": sorted(notas, key=lambda x: -x[1])[:5],
            "notas_semana_total": len(notas), "janelas": janelas, "multi_esfera": multi, "cnpjs": len(idx14), "status": status,
            # para a busca por nome de empresa: as maiores de cada esfera
            "empresas": sorted([[c, y["nome"], r2(y["dep"] + y["sen"] + y["mun"])] for c, y in idx14.items()],
                               key=lambda z: -z[2])[:600]}
    _gravar(saida / "destaques.json", dest)
    return dest
