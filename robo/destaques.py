"""Fase 3 do hub: notas da semana, fornecedores em mais de uma esfera e índice de CNPJ.

Roda uma vez por dia (parte "pesada" do Mensageiro: lê as notas e os fornecedores
publicados pelos três sites). Saídas:
    dados/destaques.json      -> 5 maiores notas novas da semana (todas as esferas) e
                                 fornecedores pagos em mais de uma esfera no ano
    dados/cnpj/XX.json        -> índice de CNPJ do ano (XX = 2 primeiros dígitos)
    robo/estado/*.json        -> notas já vistas (senadores e municípios), para saber o que é novo

Deputados: as notas novas vêm prontas do próprio site (docs/dados/novas). Senadores e
municípios não publicam "notas novas": o Mensageiro guarda uma marca de cada nota que já
viu e considera nova a que aparece pela primeira vez. Na primeira execução ele só guarda
as marcas (a contagem começa no dia seguinte).
"""
import hashlib
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from privacidade import mascarar_cpf_no_texto as mascara

RAIZ = Path(__file__).resolve().parents[1]
ESTADO = RAIZ / "robo" / "estado"
DIAS = 7
MAX_NOVAS_GUARDADAS = 200


def r2(x):
    return round(float(x or 0), 2)


def _marca(*partes) -> str:
    return hashlib.sha1("|".join(str(p) for p in partes).encode()).hexdigest()[:12]


def _ler(p: Path, padrao):
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else padrao
    except json.JSONDecodeError:
        return padrao


def _gravar(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), "utf-8")


def _raiz(c: str) -> str:
    return c[:8]


# ------------------------------------------------------------------ notas novas
def novas_deputados(fd, hoje: date, site: str) -> list[list]:
    """[esfera, valor, o quê, quem, onde, data, link] das notas novas dos últimos 7 dias (do próprio site)."""
    out = []
    idx = fd.get("novas/indice.json") or {}
    for dia in idx.get("dias") or []:
        d = dia.get("data") if isinstance(dia, dict) else dia
        try:
            if (hoje - date.fromisoformat(d)).days >= DIAS:
                continue
        except (TypeError, ValueError):
            continue
        x = fd.get(f"novas/{d}.json") or {}
        cats, forn, deps = x.get("c") or [], x.get("f") or [], x.get("dep") or {}
        for n in x.get("n") or []:
            dep = deps.get(str(n[0])) or ["", "", "", ""]
            f = forn[n[1]] if n[1] < len(forn) else ["", "", ""]
            out.append(["DEP", round(n[4] / 100, 2), f"{cats[n[2]] if n[2] < len(cats) else ''} — {f[1]}",
                        f"{dep[0]}", f"Deputado(a) · {dep[2]}", n[3], f"{site}?pag=novas"])
    return out


def _novas_por_marca(nome: str, notas: list[tuple[str, list]], hoje: date) -> list[list]:
    """notas = [(marca, linha)]. Devolve as linhas vistas pela primeira vez nos últimos 7 dias."""
    p = ESTADO / f"vistas_{nome}_{hoje.year}.json"
    vistas = set(_ler(p, []))
    recentes_p = ESTADO / f"novas_{nome}.json"
    recentes = _ler(recentes_p, [])
    primeira = not p.exists()
    novas = [ln + [hoje.isoformat()] for m, ln in notas if m not in vistas]
    if not primeira and len(novas) < 0.3 * max(1, len(notas)):      # se "tudo" virou novo, o site foi refeito: recomeça
        recentes += sorted(novas, key=lambda x: -x[1])[:MAX_NOVAS_GUARDADAS]
    limite = (hoje - timedelta(days=DIAS - 1)).isoformat()
    recentes = [x for x in recentes if x[-1] >= limite]
    _gravar(p, sorted(vistas | {m for m, _ in notas}))
    _gravar(recentes_p, recentes)
    return [x[:-1] for x in recentes]


def novas_senadores(fs, ano: int, hoje: date, site: str) -> list[list]:
    r = fs.get(f"{ano}/resumo.json") or {}
    notas = []
    for s in r.get("senadores") or []:
        d = fs.get(f"{ano}/notas/{s['id']}.json") or {}
        fz = d.get("fornecedores") or {}
        for n in d.get("notas") or []:
            f = fz.get(n[3]) or ["", ""]
            link = f"{site}?ano={ano}#sen-{s['id']}" if isinstance(s["id"], int) else site
            # a marca não usa a chave do fornecedor (ela pode mudar quando o site refaz o ano)
            notas.append((_marca(s["id"], n[0], n[1], n[2], n[4], n[5]),
                          ["SEN", r2(n[4]), f"{n[2]} — {f[1]}", s.get("nome", ""), f"Senador(a) · {s.get('uf', '')}", n[0], link]))
    return _novas_por_marca("sen", notas, hoje)


def novas_municipios(fm, ano: int, hoje: date, site: str) -> list[list]:
    res = fm.get("resumo.json") or {}
    notas = []
    for m in res.get("municipios") or []:
        if str(ano) not in (m.get("anos") or {}):
            continue
        d = fm.get(f"n/{m['sim']}/{ano}.json") or {}
        fz, orgs = d.get("forn") or [], d.get("orgaos") or {}
        for e in d.get("emp") or []:
            papel = (orgs.get(e[0]) or ["", ""])[1]
            onde = {"camara": "Câmara", "prefeito": "Gabinete do prefeito", "vice": "Gabinete do vice"}.get(papel, "Órgão")
            f = fz[e[4]] if e[4] < len(fz) else [""]
            v = r2((e[5] or 0) - (e[6] or 0))
            hist = (e[8] or "").strip()
            oque = f"{hist[:60]}{'…' if len(hist) > 60 else ''} — {f[0]}" if hist else f[0]
            notas.append((_marca(m["sim"], e[0], e[1], e[2], e[5]),
                          ["MUN", v, oque, m["nome"].title(), f"{onde} de {m['nome'].title()}", e[1], f"{site}#municipio/{m['sim']}"]))
    return _novas_por_marca("mun", notas, hoje)


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
        for ln in (fm.get(f"f/{sim}/{ano}.json") or {}).get("linhas") or []:
            nome, c, tipo, valor = ln[0], ln[1], ln[2], ln[4]
            if tipo != "PJ" or len(c or "") != 14:
                continue
            x = item(c, nome)
            x["mun"][0] += valor
            x["mun"][1].add(sim)
            if valor > x["maior"]:
                x["maior"], x["nome"] = valor, nome
            y = i14(c, nome)
            y["mun"] += valor
            y["cidades"][sim] += valor
        nd = fm.get(f"n/{sim}/{ano}.json") or {}
        orgs = nd.get("orgaos") or {}
        for e in nd.get("emp") or []:
            if (orgs.get(e[0]) or ["", ""])[1] == "camara":
                f = (nd.get("forn") or [])[e[4]] if e[4] < len(nd.get("forn") or []) else None
                if f and len(f[1] or "") == 14 and _raiz(f[1]) in g:
                    g[_raiz(f[1])]["mun"][2].add(sim)
    return g, idx14


def multi_esfera(g: dict, nomes_mun: dict, limite: int = 20) -> list[list]:
    out = []
    for raiz, x in g.items():
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
    notas = []
    for nome, fn in (("deputados", lambda: novas_deputados(fd, hoje, sites["deputados"])),
                     ("senadores", lambda: novas_senadores(fs, ano, hoje, sites["senadores"])),
                     ("municipios", lambda: novas_municipios(fm, ano, hoje, sites["municipios"]))):
        try:
            v = fn()
            notas += v
            status[f"notas_{nome}"] = f"ok ({len(v)} novas na semana)"
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
    dest = {"ano": ano, "gerado_em": hoje.isoformat(), "notas_semana": sorted(notas, key=lambda x: -x[1])[:5],
            "notas_semana_total": len(notas), "multi_esfera": multi, "cnpjs": len(idx14), "status": status,
            # para a busca por nome de empresa: as maiores de cada esfera
            "empresas": sorted([[c, y["nome"], r2(y["dep"] + y["sen"] + y["mun"])] for c, y in idx14.items()],
                               key=lambda z: -z[2])[:600]}
    _gravar(saida / "destaques.json", dest)
    return dest
