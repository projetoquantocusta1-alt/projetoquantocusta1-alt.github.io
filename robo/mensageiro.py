"""O Mensageiro: junta os números finais dos três sites num arquivo levíssimo para o hub.

Não consulta nenhum site do governo. Só lê o que os robôs dos três repositórios já
publicaram (pelo endereço público do GitHub) e grava dados/totais_hub.json.

Uso:
    python robo/mensageiro.py                       # lê do GitHub
    python robo/mensageiro.py --local /pasta/com/os/3/repositorios   # teste com cópias locais

Se uma esfera não responder, mantém o último número bom dela (do arquivo anterior).
"""
import argparse
from collections import Counter
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "totais_hub.json"
SAIDA_ESTADOS = RAIZ / "dados" / "estados.json"
SAIDA_BUSCA = RAIZ / "dados" / "busca.json"
CONTA = "projetoquantocusta1-alt"
REPOS = {"deputados": "quanto-custa-deputados", "senadores": "quanto-custa-senadores", "municipios": "quanto-custa-municipios",
         "municipios_ba": "quanto-custa-municipios-ba"}
SITE = "https://quantocustaum.com/{repo}/"
RAW = "https://raw.githubusercontent.com/" + CONTA + "/{repo}/main/docs/dados/{caminho}"
USER_AGENT = "ProjetoQuantoCusta/1.0 (painel de transparencia com dados abertos)"
CADEIRAS = {"deputados": 513, "senadores": 81}

# "O que dava pra fazer?": mesma regra provisória dos sites (80% destes grupos da cota)
EXCESSO_PCT = 0.80
GRUPOS_DEP = r"passage|ve[ií]cul|combust|fretamento|t[aá]xi|ped[aá]gio|sem nota|aliment|hosped|divulga"
GRUPOS_SEN = r"locomo|passage|divulga"


# ------------------------------------------------------------------ leitura
class Fonte:
    """Lê os JSON publicados de um repositório (GitHub ou pasta local)."""

    def __init__(self, repo: str, local: Path | None = None):
        self.repo, self.local, self.cache = repo, local, {}

    def get(self, caminho: str, padrao=None):
        if caminho in self.cache:
            return self.cache[caminho]
        try:
            if self.local:
                p = self.local / self.repo / "docs" / "dados" / caminho
                v = json.loads(p.read_text("utf-8"))
            else:
                req = urllib.request.Request(RAW.format(repo=self.repo, caminho=caminho), headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=60) as r:
                    v = json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            v = padrao
        self.cache[caminho] = v
        return v


def r2(x):
    return round(float(x or 0), 2)


def segundos_restantes(ano: int, mes_inicio: int) -> float:
    """Segundos entre o 1º dia do mês seguinte aos dados e o fim do ano."""
    ini = datetime(ano, mes_inicio + 1, 1) if mes_inicio < 12 else datetime(ano + 1, 1, 1)
    return max(1.0, (datetime(ano + 1, 1, 1) - ini).total_seconds())


def ritmo(ano: int, ja: float, meses: int, restante: float | None = None) -> dict:
    """Contador: valor = ja + por_seg × (agora − inicio), até o teto (previsão do ano)."""
    if meses <= 0:
        return {"ja": r2(ja), "inicio": f"{ano}-01-01", "por_seg": 0.0, "teto": r2(ja)}
    if meses >= 12:
        return {"ja": r2(ja), "inicio": f"{ano + 1}-01-01", "por_seg": 0.0, "teto": r2(ja)}
    if restante is None:
        restante = ja / meses * (12 - meses)
    return {"ja": r2(ja), "inicio": f"{ano}-{meses + 1:02d}-01",
            "por_seg": round(restante / segundos_restantes(ano, meses), 4), "teto": r2(ja + restante)}


def soma_categorias(cats: dict, regex: str) -> float:
    rx = re.compile(regex, re.I)
    return sum(v for k, v in (cats or {}).items() if rx.search(k))


# ------------------------------------------------------------------ esferas
def deputados(f: Fonte, ano: int) -> dict:
    meta = f.get("meta.json") or {}
    hist = (f.get("historico.json") or {}).get("anos") or []
    r = f.get(f"{ano}/resumo.json")
    if not r:
        raise ValueError(f"deputados: sem resumo de {ano}")
    p = r.get("previsao_camara") or {}
    md = r.get("meses_decorridos") or 0
    ja = p.get("ja_gasto") or r.get("total_camara") or 0
    cont = ritmo(ano, ja, md, p.get("restante") if md < 12 else None)
    if p.get("total_ano"):
        cont["teto"] = r2(p["total_ano"])
    fechados = [a for a in hist if a.get("meses_decorridos") == 12 and a["ano"] < ano]
    ult = max(fechados, key=lambda a: a["ano"]) if fechados else None
    pres = f.get(f"{ano}/presenca.json") or {}
    dias = sum(v.get("dias", 0) for v in (pres.get("deputados") or {}).values())
    faltas = sum(v.get("faltas", 0) for v in (pres.get("deputados") or {}).values())
    base = soma_categorias(ult.get("categorias"), GRUPOS_DEP) * (ult.get("fator_ipca") or 1) if ult else 0
    return {
        "ano": ano, "total_ano": r2(ja), "previsto_ano": cont["teto"], "meses": md, "contador": cont,
        "historico": [[a["ano"], r2(a.get("total_corrigido") or a.get("total")), a.get("meses_decorridos") == 12] for a in sorted(hist, key=lambda a: a["ano"])],
        "desde": min((a["ano"] for a in hist), default=ano),
        "cadeiras": CADEIRAS["deputados"],
        "por_cadeira": {"ano": ult["ano"], "valor": r2(ult["total_corrigido"] / CADEIRAS["deputados"])} if ult else None,
        "faltas_plenario": round(faltas / dias, 4) if dias else None,
        "dava": {"ano": ult["ano"], "base": r2(base)} if ult else None,
        "atualizado_em": meta.get("atualizado_em"), "url": SITE.format(repo=REPOS["deputados"]),
    }


def senadores(f: Fonte, ano: int) -> dict:
    meta = f.get("meta.json") or {}
    anos = sorted(meta.get("anos") or [])
    r = f.get(f"{ano}/resumo.json")
    if not r:
        raise ValueError(f"senadores: sem resumo de {ano}")
    md = r.get("meses_decorridos") or 0
    pv = r.get("previsao") or {}
    # usa a previsão do próprio site dos senadores (salário dos meses que faltam + 13º + cota no ritmo do ano)
    cont = ritmo(ano, r.get("total") or 0, md, pv.get("restante") if pv.get("restante") is not None and md < 12 else None)
    hist, ult = [], None
    for a in anos:
        x = f.get(f"{a}/resumo.json")
        if not x:
            continue
        fechado = bool(x.get("fechado")) or a < ano
        hist.append([a, r2((x.get("total") or 0) * (x.get("fator_ipca") or 1)), fechado])
        if fechado and a < ano:
            ult = x
    maior = max(r.get("senadores") or [], key=lambda s: (s.get("custos") or {}).get("ceaps", 0), default=None)
    base = 0.0
    if ult:
        for s in ult.get("senadores") or []:
            base += soma_categorias(s.get("categorias"), GRUPOS_SEN)
        base *= ult.get("fator_ipca") or 1
    return {
        "ano": ano, "total_ano": r2(r.get("total")), "previsto_ano": cont["teto"], "meses": md, "contador": cont,
        "historico": hist, "desde": anos[0] if anos else ano, "cadeiras": CADEIRAS["senadores"],
        "cota_ano": r2(r.get("total_ceaps")),
        "maior_cota": {"nome": maior.get("nome"), "valor": r2(maior["custos"]["ceaps"])} if maior else None,
        "por_cadeira": {"ano": ult["ano"], "valor": r2(ult["total"] * (ult.get("fator_ipca") or 1) / CADEIRAS["senadores"])} if ult else None,
        "dava": {"ano": ult["ano"], "base": r2(base)} if ult else None,
        "atualizado_em": meta.get("gerado_em"), "url": SITE.format(repo=REPOS["senadores"]),
    }


def municipios(f: Fonte, ano: int, mes_atual: int) -> dict:
    """Câmaras municipais do Ceará (o contador e os cartões) e, à parte, os órgãos "Gabinete do Prefeito/Vice".

    O órgão Gabinete do Prefeito no TCE-CE inclui comunicação, cerimonial, procuradoria e programas: não é o
    custo do prefeito. Por isso não entra no "custo dos políticos"; aparece numa linha própria.
    Só anos com os 184 municípios entram no histórico; o ano corrente entra como parcial.
    """
    meta = f.get("meta.json") or {}
    res = f.get("resumo.json") or {}
    campos = res.get("campos") or []
    ix = {c: i for i, c in enumerate(campos)}
    fatores = {str(k): v for k, v in ((meta.get("ipca") or {}).get("fatores") or {}).items()}
    total_mun = meta.get("total_municipios") or len(res.get("municipios") or []) or 184
    por_ano: dict[str, dict] = {}
    diverg: dict[str, list] = {}   # câmaras que não enviaram o balancete ou cujas notas não batem (ano atual)
    ritmo_mensal = ja = pago_ano = 0.0
    for m in res.get("municipios") or []:
        for a, ln in (m.get("anos") or {}).items():
            q = por_ano.setdefault(a, {"camara": 0.0, "gabinetes": 0.0, "n": 0, "vereadores": 0, "pop": 0, "pop_n": 0})
            cam = ln[ix["camara"]] or 0
            q["camara"] += cam
            q["gabinetes"] += (ln[ix["gab_prefeito"]] or 0) + (ln[ix["gab_vice"]] or 0)
            q["n"] += 1
            q["vereadores"] += ln[ix["n_vereadores"]] or 0
            if ln[ix["populacao"]]:
                q["pop"] += ln[ix["populacao"]]
                q["pop_n"] += 1
            if int(a) == ano:
                if "situacao_camara" in ix:
                    sit, dif = ln[ix["situacao_camara"]], ln[ix["diferenca_camara"]] if "diferenca_camara" in ix else None
                elif "conferido" in ix and ln[ix["conferido"]] == 0:
                    # resumo ainda sem a situação: olha o arquivo do município (só os que não conferem)
                    det = ((f.get(f"m/{m.get('sim')}.json") or {}).get("anos") or {}).get(a) or {}
                    c = (det.get("conferencia") or {}).get("camara") or {}
                    fonte = ((det.get("orgaos") or {}).get("camara") or {}).get("fonte_gasto") or "balancete"
                    sit = "sem_balancete" if fonte != "balancete" else ("diferenca" if c and not c.get("ok") else None)
                    dif = c.get("diferenca")
                else:
                    sit = dif = None
                if sit in ("sem_balancete", "diferenca"):
                    diverg.setdefault(sit, []).append([m.get("nome"), dif])
            if int(a) == ano:
                meses = (ln[ix["mes_ref"]] or 0) % 100
                if meses:
                    # ritmo do ano pelo PAGO: contratos e folha são empenhados de uma vez no começo do ano e pagos
                    # mês a mês, então o empenhado corre na frente e inflaria a previsão. Sem balancete (pago
                    # desconhecido), usa o empenhado das notas.
                    pg = ln[ix["camara_pago"]] if "camara_pago" in ix and ln[ix["camara_pago"]] is not None else cam
                    ritmo_mensal += pg / meses
                    ja += cam
                    pago_ano += pg
    completos = sorted(int(a) for a, q in por_ano.items() if q["n"] >= total_mun)
    atual = por_ano.get(str(ano), {"camara": 0.0, "gabinetes": 0.0, "n": 0, "vereadores": 0})
    md = max(0, mes_atual - 1)
    ja_est = ritmo_mensal * md if md else ja
    cont = ritmo(ano, ja_est, md, ritmo_mensal * (12 - md))
    hist = [[a, r2(por_ano[str(a)]["camara"] * fatores.get(str(a), 1)), a < ano] for a in completos]
    if atual["n"] and ano not in completos:
        hist.append([ano, r2(atual["camara"] * fatores.get(str(ano), 1)), False])
    # vereadores e custo por vereador: último ano completo (o atual, se já estiver completo)
    ref = max(completos) if completos else None
    fechado = max((a for a in completos if a < ano), default=None)
    q_ref = por_ano[str(ref)] if ref else None
    q_f = por_ano[str(fechado)] if fechado else None
    desde = completos[0] if completos else None
    serie_completa = bool(completos) and completos == list(range(2017, ano + 1))
    return {
        "ano": ano, "em_coleta": atual["n"] < total_mun or not serie_completa,
        "cobertura": atual["n"], "total_municipios": total_mun, "anos_completos": completos,
        "total_ano": r2(ja_est), "registrado_ano": r2(ja), "pago_ano": r2(pago_ano), "previsto_ano": cont["teto"], "contador": cont,
        "gabinetes_registrado_ano": r2(atual["gabinetes"]),
        "divergencias": {k: sorted(v) for k, v in diverg.items()},
        "historico": hist, "desde": desde,
        "vereadores": int(q_ref["vereadores"]) if q_ref else None, "vereadores_ano": ref,
        # custo da câmara inteira (vereadores, servidores e despesas) dividido pelo número de vereadores
        "por_vereador": {"ano": fechado, "valor": r2(q_f["camara"] * fatores.get(str(fechado), 1) / q_f["vereadores"])} if q_f and q_f["vereadores"] else None,
        "populacao": int(q_ref["pop"]) if q_ref and q_ref["pop_n"] >= total_mun else None,
        "atualizado_em": meta.get("gerado_em"), "url": SITE.format(repo=REPOS["municipios"]),
        "_conferir": {"vereadores_fonte": int(q_ref["vereadores"]) if q_ref else None},
    }


def municipios_siconfi(f: Fonte, ano: int, mes_atual: int, uf: str) -> dict:
    """Câmaras municipais de um estado coletado pelo SICONFI (Tesouro Nacional; hoje, a Bahia).

    O relatório do Tesouro (RREO) é bimestral e traz o empenhado e o LIQUIDADO por função (não o pago). O contador
    avança no ritmo do liquidado (o empenhado corre na frente: folha e contratos são empenhados no começo do ano).
    Um ano entra como completo no histórico quando todas as prefeituras entregaram o 6º bimestre."""
    meta = f.get("meta.json") or {}
    res = f.get("resumo.json") or {}
    ix = {c: i for i, c in enumerate(res.get("campos") or [])}
    if not ix:
        raise RuntimeError("sem resumo")
    fatores = {str(k): v for k, v in ((meta.get("ipca") or {}).get("fatores") or {}).items()}
    total_mun = meta.get("total_municipios") or len(res.get("municipios") or [])
    por_ano: dict[str, dict] = {}
    ritmo_mensal = ja = liq_ano = 0.0
    for m in res.get("municipios") or []:
        for a, ln in (m.get("anos") or {}).items():
            q = por_ano.setdefault(a, {"camara": 0.0, "n": 0, "n6": 0, "vereadores": 0, "per": []})
            cam = ln[ix["camara"]] or 0
            q["camara"] += cam
            q["n"] += 1
            q["n6"] += 1 if ln[ix["periodo"]] == 6 else 0
            q["vereadores"] += ln[ix["n_vereadores"]] or 0
            q["per"].append(ln[ix["periodo"]])
            if int(a) == ano and ln[ix["periodo"]]:
                meses = ln[ix["periodo"]] * 2
                liq = ln[ix["camara_liquidado"]] or 0
                ritmo_mensal += liq / meses
                ja += cam
                liq_ano += liq
    completos = sorted(int(a) for a, q in por_ano.items() if q["n6"] >= total_mun)
    atual = por_ano.get(str(ano), {"camara": 0.0, "n": 0, "per": []})
    md = max(0, mes_atual - 1)
    cont = ritmo(ano, ritmo_mensal * md if md else liq_ano, md, ritmo_mensal * (12 - md))
    # ano "completo" no gráfico: todas as prefeituras que entregaram mandaram o ano inteiro (as que não entregaram
    # são listadas no site); o ano em andamento é sempre parcial
    hist = [[int(a), r2(q["camara"] * fatores.get(a, 1)), int(a) < ano and q["n6"] == q["n"]] for a, q in sorted(por_ano.items())]
    fechado = max((int(a) for a, q in por_ano.items() if int(a) < ano and q["vereadores"]), default=None)
    q_f = por_ano.get(str(fechado)) if fechado else None
    per = Counter(atual["per"]).most_common(1)
    return {
        "uf": uf, "ano": ano, "cobertura": atual["n"], "total_municipios": total_mun, "anos_completos": completos,
        "registrado_ano": r2(ja), "liquidado_ano": r2(liq_ano), "total_ano": cont["ja"], "contador": cont,
        "bimestre": per[0][0] if per else None, "faltas_ano": (meta.get("faltas") or {}).get(str(ano), []),
        "historico": hist, "desde": min((int(a) for a in por_ano), default=None),
        "vereadores": int(q_f["vereadores"]) if q_f else None,
        "por_vereador": {"ano": fechado, "valor": r2(q_f["camara"] * fatores.get(str(fechado), 1) / q_f["vereadores"])} if q_f and q_f["vereadores"] else None,
        "atualizado_em": meta.get("gerado_em"), "url": SITE.format(repo=REPOS["municipios"]) + f"?uf={uf.lower()}",
        "fonte": "SICONFI (Tesouro Nacional)",
    }


# ------------------------------------------------------------------ validações (antes de publicar)
def robo_rodando(repo: str) -> bool:
    """True se algum robô do repositório está rodando agora (API pública do GitHub)."""
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{CONTA}/{repo}/actions/runs?status=in_progress&per_page=20",
                                     headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            runs = json.loads(r.read().decode()).get("workflow_runs") or []
        return any("pages" not in (x.get("name") or "").lower() for x in runs)
    except Exception:  # noqa: BLE001 — sem resposta do GitHub: não bloqueia
        return False


def validar(nome: str, x: dict, ano: int) -> list[str]:
    """Problemas que impedem publicar a esfera (o hub mantém o último número bom)."""
    erros = []
    hist = [h for h in x.get("historico") or [] if h[2] and h[0] < ano]
    for (a0, v0, _), (a1, v1, _) in zip(hist, hist[1:]):
        # coleta incompleta aparece como queda forte (ou salto absurdo se o ano anterior estava pela metade)
        if a1 == a0 + 1 and v0 > 0 and (v1 < 0.5 * v0 or v1 > 2.5 * v0):
            erros.append(f"{a1}: variação de {100 * (v1 / v0 - 1):+.0f}% sobre {a0} (coleta incompleta?)")
    if nome == "municipios":
        c = x.get("_conferir") or {}
        if x.get("vereadores") != c.get("vereadores_fonte"):
            erros.append("vereadores diferente da soma da fonte")
        if x.get("cobertura", 0) < x.get("total_municipios", 0) and not x.get("em_coleta"):
            erros.append("cobertura incompleta sem aviso de coleta")
    return erros


# ------------------------------------------------------------------ fase 2: estados e busca
def estados(fd: Fonte, fs: Fonte, fm: Fonte, ano: int, fb: Fonte | None = None) -> dict:
    """Por UF, no ano atual: deputados, senadores e (só no CE) câmaras e gabinetes municipais, emendas e população."""
    uf: dict[str, dict] = {}

    def e(u):
        return uf.setdefault(u, {"dep": [0, 0.0, 0], "sen": [0, 0.0, 0]})   # [pessoas, custo, meses]
    for d in (fd.get(f"{ano}/resumo.json") or {}).get("deputados") or []:
        if d.get("uf"):
            x = e(d["uf"])["dep"]
            x[0] += 1 if d.get("em_exercicio") else 0
            x[1] += d.get("custo_mandato") or 0
            x[2] += d.get("meses") or 0
    for d in (fs.get(f"{ano}/resumo.json") or {}).get("senadores") or []:
        if d.get("uf") and isinstance(d.get("id"), int):
            x = e(d["uf"])["sen"]
            x[0] += 1
            x[1] += d.get("custo") or 0
            x[2] += d.get("meses") or 0
    # municípios (por enquanto só o Ceará)
    res = fm.get("resumo.json") or {}
    ix = {c: i for i, c in enumerate(res.get("campos") or [])}
    meta = fm.get("meta.json") or {}
    if ix:
        n = cust = gab = em = pop = 0
        for m in res.get("municipios") or []:
            ln = (m.get("anos") or {}).get(str(ano))
            if not ln:
                continue
            n += 1
            cust += ln[ix["camara"]] or 0
            gab += (ln[ix["gab_prefeito"]] or 0) + (ln[ix["gab_vice"]] or 0)
            em += ln[ix["emendas"]] or 0 if "emendas" in ix else 0
            pop += ln[ix["populacao"]] or 0 if "populacao" in ix else 0
        x = e("CE")
        x["mun"] = {"com_dados": n, "total": meta.get("total_municipios") or 184, "custo": r2(cust), "gabinetes": r2(gab), "emendas": r2(em),
                    "populacao": int(pop) or None}
    # Bahia (SICONFI): só a câmara; gabinetes e emendas não existem nessa fonte
    rb = (fb.get("resumo.json") or {}) if fb else {}
    ixb = {c: i for i, c in enumerate(rb.get("campos") or [])}
    if ixb:
        n = cust = pop = 0
        for m in rb.get("municipios") or []:
            ln = (m.get("anos") or {}).get(str(ano))
            if ln:
                n += 1
                cust += ln[ixb["camara"]] or 0
                pop += ln[ixb["populacao"]] or 0
        e("BA")["mun"] = {"com_dados": n, "total": (fb.get("meta.json") or {}).get("total_municipios") or 417, "custo": r2(cust),
                          "gabinetes": None, "emendas": None, "populacao": int(pop) or None, "fonte": "SICONFI"}
    out = {}
    for u, x in uf.items():
        d, s_ = x["dep"], x["sen"]
        pessoas_meses = d[2] + s_[2]
        o = {"dep": {"n": d[0], "custo": r2(d[1])}, "sen": {"n": s_[0], "custo": r2(s_[1])},
             # cor do mapa: custo médio de um político federal do estado por mês
             "por_mes": r2((d[1] + s_[1]) / pessoas_meses) if pessoas_meses else None}
        if "mun" in x:
            o["mun"] = x["mun"]
            tot = d[1] + s_[1] + x["mun"]["custo"]
            if x["mun"]["populacao"] and x["mun"]["com_dados"] >= x["mun"]["total"]:
                o["por_habitante"] = r2(tot / x["mun"]["populacao"])
        out[u] = o
    return {"ano": ano, "ufs": out}


def busca(fd: Fonte, fs: Fonte, fm: Fonte) -> list[list]:
    """Índice enxuto de nomes: [tipo, nome, detalhe, chave]. Tipos: D deputado, S senador, C cidade, P prefeito(a), V vereador(a)."""
    out, vistos = [], set()
    for d in (fd.get("total/resumo.json") or {}).get("deputados") or []:
        out.append(["D", d.get("nome", ""), f"{d.get('partido', '')}-{d.get('uf', '')}", d["id"]])
    for a in sorted((fs.get("meta.json") or {}).get("anos") or [], reverse=True):
        for s_ in (fs.get(f"{a}/resumo.json") or {}).get("senadores") or []:
            if isinstance(s_.get("id"), int) and s_["id"] not in vistos:
                vistos.add(s_["id"])
                out.append(["S", s_.get("nome", ""), f"{s_.get('partido', '')}-{s_.get('uf', '')}".strip("-"), s_["id"], a])
    for m in (fm.get("resumo.json") or {}).get("municipios") or []:
        sim = m["sim"]
        out.append(["C", m["nome"].title(), "Ceará", sim])
        det = fm.get(f"m/{sim}.json") or {}
        mand = det.get("mandatos") or {}
        if not mand:
            continue
        ult = mand[max(mand, key=int)]
        cidade = m["nome"].title()
        for papel, tipo in (("prefeito", "P"), ("vice", "P")):
            p = ult.get(papel)
            if p:
                rot = "prefeito(a)" if papel == "prefeito" else "vice-prefeito(a)"
                out.append([tipo, (p.get("urna") or p.get("nome") or "").title(), f"{rot} de {cidade} · {p.get('partido', '')}", sim])
        for v in ult.get("vereadores") or []:
            if v:
                out.append(["V", (v.get("urna") or v.get("nome") or "").title(), f"vereador(a) de {cidade} · {v.get('partido', '')}", sim])
    return out


# ------------------------------------------------------------------ principal
def montar(local: Path | None = None, hoje: date | None = None, anterior: dict | None = None) -> dict:
    hoje = hoje or date.today()
    ano = hoje.year
    anterior = anterior or {}
    out = {"gerado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"), "ano": ano, "esferas": {}, "status": {}}
    fazer = {"deputados": lambda f: deputados(f, ano), "senadores": lambda f: senadores(f, ano),
             "municipios": lambda f: municipios(f, ano, hoje.month),
             "municipios_ba": lambda f: municipios_siconfi(f, ano, hoje.month, "BA")}
    for nome, fn in fazer.items():
        try:
            if not local and robo_rodando(REPOS[nome]):
                raise RuntimeError("robô da esfera ainda rodando")
            x = fn(Fonte(REPOS[nome], local))
            erros = validar(nome, x, ano)
            if erros:
                raise RuntimeError("validação: " + "; ".join(erros))
            x.pop("_conferir", None)
            out["esferas"][nome] = x
            out["status"][nome] = "ok"
        except Exception as e:  # noqa: BLE001
            velho = (anterior.get("esferas") or {}).get(nome)
            if velho and velho.get("ano") == ano:
                out["esferas"][nome] = velho
                out["status"][nome] = f"mantido o último número bom ({e})"
            else:
                out["status"][nome] = f"indisponível ({e})"
    es = out["esferas"]
    out["contador"] = {k: v["contador"] for k, v in es.items()}
    # o contador principal é o Congresso Nacional; os municípios do Ceará têm contador próprio
    out["total_ano"] = r2(sum(es[k]["total_ano"] for k in ("deputados", "senadores") if k in es))
    mun = [es[k] for k in ("municipios", "municipios_ba") if k in es]
    out["total_ano_municipios"] = r2(sum(x["total_ano"] for x in mun)) if mun else None
    bases = [es[k]["dava"] for k in ("deputados", "senadores") if es.get(k, {}).get("dava")]
    if bases:
        base = sum(b["base"] for b in bases)
        out["dava"] = {"ano": min(b["ano"] for b in bases), "base": r2(base), "excesso": r2(base * EXCESSO_PCT),
                       "percentual": EXCESSO_PCT}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", type=Path, help="pasta com cópias dos 3 repositórios (teste)")
    ap.add_argument("--completo", action="store_true", help="também a parte pesada: notas da semana, fornecedores e CNPJ")
    args = ap.parse_args(argv)
    anterior = {}
    if SAIDA.exists():
        try:
            anterior = json.loads(SAIDA.read_text("utf-8"))
        except json.JSONDecodeError:
            pass
    out = montar(args.local, anterior=anterior)
    ano = date.today().year
    fontes = [Fonte(REPOS[k], args.local) for k in ("deputados", "senadores", "municipios")]
    fonte_ba = Fonte(REPOS["municipios_ba"], args.local)
    for nome, fn, caminho in (("estados", lambda: estados(*fontes, ano, fonte_ba), SAIDA_ESTADOS), ("busca", lambda: busca(*fontes), SAIDA_BUSCA)):
        try:
            v = fn()
            if v and (nome != "estados" or v["ufs"]):
                caminho.parent.mkdir(parents=True, exist_ok=True)
                caminho.write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")), "utf-8")
                print(f"{caminho.name}: ok")
        except Exception as e:  # noqa: BLE001 — mantém o arquivo anterior
            print(f"{nome}: falhou ({e}); arquivo anterior mantido")
    if not out["esferas"]:
        print("Nenhuma esfera respondeu; arquivo anterior mantido.", out["status"])
        return 1
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), "utf-8")
    if args.completo:
        import destaques
        try:
            d = destaques.gerar(*fontes, ano, date.today(), {k: SITE.format(repo=v) for k, v in REPOS.items()}, SAIDA.parent)
            print("destaques.json:", d["status"], f"{len(d['multi_esfera'])} fornecedores em mais de uma esfera, {d['cnpjs']} CNPJs")
        except Exception as e:  # noqa: BLE001
            print(f"destaques: falhou ({e}); arquivos anteriores mantidos")
    print("totais_hub.json:", {k: v["total_ano"] for k, v in out["esferas"].items()}, out["status"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
