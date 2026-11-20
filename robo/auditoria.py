"""Auditoria de valores do Quanto Custa? — checagens independentes sobre os JSON publicados.

Refaz as contas a partir dos dados de cada site (sem usar o código do Mensageiro) e procura CPF inteiro.
Uso (com os repositórios lado a lado numa pasta):
    python robo/auditoria.py --local /home/user
Sai com código 1 se alguma checagem der ERRO. INFO = casos para olhar, já conhecidos ou explicados no site.
"""
import argparse, json, os, re, glob, sys
from pathlib import Path
from collections import Counter, defaultdict

_ap = argparse.ArgumentParser(); _ap.add_argument("--local", type=Path, default=Path("/home/user"))
R = _ap.parse_args().local
J = lambda p: json.load(open(p, encoding="utf-8"))
res = []  # (status, nome, detalhe)
def chk(nome, ok, det=""):
    res.append(("OK" if ok else "ERRO", nome, det))
def info(nome, det):
    res.append(("INFO", nome, det))
def perto(a, b, tol=1.0):
    return abs((a or 0) - (b or 0)) <= tol

HUB = J(R / "projetoquantocusta1-alt.github.io/dados/totais_hub.json")
E = HUB["esferas"]
ANO = HUB["ano"]

# ---------------- deputados federais
D = R / "quanto-custa-deputados/docs/dados"
hist = {a["ano"]: a for a in J(D / "historico.json")["anos"]}
erros_dep = defaultdict(list)
for ano in range(2009, ANO + 1):
    r = J(D / f"{ano}/resumo.json")
    soma = sum(d["custo_mandato"] for d in r["deputados"])
    if not perto(soma, r["total_camara"], len(r["deputados"]) * 0.01 + 1): erros_dep["total=soma"].append((ano, soma, r["total_camara"]))
    for d in r["deputados"]:
        if not perto(sum(d["custos"].values()), d["custo_mandato"], 0.05): erros_dep["custo=componentes"].append((ano, d["nome"]))
        if any(v < 0 for v in d["custos"].values()): erros_dep["negativo"].append((ano, d["nome"]))
        if (d.get("emendas_pago") or 0) > (d.get("emendas_empenhado") or 0) + 0.01: erros_dep["emenda paga>empenhada"].append((ano, d["nome"]))
        if (d.get("cota_sem_nota") or 0) > d["custos"].get("cota_parlamentar", 0) + 0.01: erros_dep["sem_nota>cota"].append((ano, d["nome"]))
        if d.get("meses", 0) > r["meses_decorridos"]: erros_dep["meses>decorridos"].append((ano, d["nome"]))
    h = hist.get(ano)
    if not h or not perto(h["total"], r["total_camara"], 1): erros_dep["historico=resumo"].append((ano, h and h["total"], r["total_camara"]))
    elif not perto(h["total"] * h["fator_ipca"], h["total_corrigido"], h["total"] * 1e-6 + 1): erros_dep["corrigido=total×IPCA"].append(ano)
for n in ["total=soma", "custo=componentes", "meses>decorridos", "historico=resumo", "corrigido=total×IPCA"]:
    chk(f"Deputados: {n} (2009–{ANO})", not erros_dep[n], str(erros_dep[n][:3]))
# casos reais da fonte (devolução maior que o gasto no ano; restos a pagar de emendas): olhar, não é erro de conta
for n in ["negativo", "emenda paga>empenhada", "sem_nota>cota"]:
    info(f"Deputados: {n} (2009–{ANO})", f"{len(erros_dep[n])}: {erros_dep[n][:3]}")
hh = {a: v for a, v, _ in E["deputados"]["historico"]}
chk("Deputados: histórico do hub = historico.json corrigido", all(perto(hh[a], hist[a]["total_corrigido"], 0.02) for a in hist))
ult = max(a for a in hist if hist[a]["meses_decorridos"] == 12 and a < ANO)
chk("Deputados: custo por cadeira = total do último ano fechado ÷ 513", perto(E["deputados"]["por_cadeira"]["valor"], hist[ult]["total_corrigido"] / 513, 0.02))
chk("Deputados: previsto do ano ≥ gasto até agora", E["deputados"]["previsto_ano"] >= E["deputados"]["total_ano"])
chk("Deputados: contador começa no gasto do ano", perto(E["deputados"]["contador"]["ja"], E["deputados"]["total_ano"], 0.01))

# ---------------- senadores
S = R / "quanto-custa-senadores/docs/dados"
erros_sen = defaultdict(list)
for ano in range(2009, ANO + 1):
    p = S / f"{ano}/resumo.json"
    if not p.exists(): erros_sen["ano faltando"].append(ano); continue
    r = J(p)
    if not perto(sum(s["custo"] for s in r["senadores"]), r["total"], len(r["senadores"]) * 0.01 + 1): erros_sen["total=soma"].append(ano)
    if not perto(sum(s["custos"].get("ceaps", 0) for s in r["senadores"]), r["total_ceaps"], len(r["senadores"]) * 0.01 + 1): erros_sen["CEAPS=soma"].append(ano)
    for s in r["senadores"]:
        if not perto(sum(s["custos"].values()), s["custo"], 0.05): erros_sen["custo=componentes"].append((ano, s["nome"]))
        if s.get("categorias") and not perto(sum(s["categorias"].values()), s["custos"].get("ceaps", 0), 0.1): erros_sen["categorias=CEAPS"].append((ano, s["nome"]))
        if s.get("mensal_ceaps") and not perto(sum(s["mensal_ceaps"]), s["custos"].get("ceaps", 0), 0.1): erros_sen["meses=CEAPS"].append((ano, s["nome"]))
        if any(v < 0 for v in s["custos"].values()): erros_sen["negativo"].append((ano, s["nome"]))
for n in ["ano faltando", "total=soma", "CEAPS=soma", "custo=componentes", "categorias=CEAPS", "meses=CEAPS", "negativo"]:
    chk(f"Senadores: {n} (2009–{ANO})", not erros_sen[n], str(erros_sen[n][:3]))
chk("Senadores: total do hub = resumo do ano", perto(E["senadores"]["total_ano"], J(S / f"{ANO}/resumo.json")["total"], 0.01))
chk("Senadores: previsto do ano ≥ gasto até agora", E["senadores"]["previsto_ano"] >= E["senadores"]["total_ano"])
chk("Senadores: maior cota ≤ cota total do ano", E["senadores"]["maior_cota"]["valor"] <= E["senadores"]["cota_ano"])

# ---------------- vereadores x população (CF art. 29, IV)
FAIXAS = [(15000, 9), (30000, 11), (50000, 13), (80000, 15), (120000, 17), (160000, 19), (300000, 21), (450000, 23), (600000, 25),
          (750000, 27), (900000, 29), (1050000, 31), (1200000, 33), (1350000, 35), (1500000, 37), (1800000, 39), (2400000, 41),
          (3000000, 43), (4000000, 45), (5000000, 47), (6000000, 49), (7000000, 51), (8000000, 53), (10**12, 55)]
def teto_ver(pop):
    for lim, n in FAIXAS:
        if pop <= lim: return n

TOTAL_IBGE = {"CE": 184, "BA": 417, "PE": 185, "PB": 223, "RN": 167}

def municipios(uf, pasta, chave):
    r = J(pasta / "resumo.json"); ix = {c: i for i, c in enumerate(r["campos"])}
    ms = r["municipios"]
    chk(f"Prefeituras {uf}: nº de municípios no arquivo ({len(ms)}) = IBGE ({TOTAL_IBGE[uf]}) ou explicado", len(ms) == TOTAL_IBGE[uf] or (uf == "PE" and len(ms) == 184), f"{len(ms)}")
    chk(f"Prefeituras {uf}: sem município repetido", len({m['ibge'] for m in ms}) == len(ms))
    camara_maior, neg, liq_maior, ver_fora, pop0, saltos, por_ver_alto = [], [], [], [], [], [], []
    soma = defaultdict(float)
    for m in ms:
        anos = m["anos"]
        for a, ln in anos.items():
            g = ln[ix["gasto_total"]]; c = ln[ix["camara"]] or 0
            soma[a] += c
            if g is not None and c > g + 0.01 and g > 0: camara_maior.append((m["nome"], a, c, g))
            if c < 0 and not ("alerta" in ix and ln[ix["alerta"]]): neg.append((m["nome"], a))   # com alerta = já avisado e fora da soma
            liqk = "camara_liquidado" if "camara_liquidado" in ix else ("camara_pago" if "camara_pago" in ix else None)
            if liqk and ln[ix[liqk]] is not None and ln[ix[liqk]] > c + 0.01: liq_maior.append((m["nome"], a))
            pop, nv = ln[ix["populacao"]], ln[ix["n_vereadores"]]
            if not pop: pop0.append((m["nome"], a))
            elif nv:
                # o nº de vereadores é fixado antes da eleição (2016, 2020, 2024) e vale o mandato todo:
                # compara com a maior população desde 4 anos antes da eleição (o Censo 2022 baixou muitas)
                ini = (2016 if int(a) <= 2020 else 2020 if int(a) <= 2024 else 2024) - 4
                pmax = max([anos[k][ix["populacao"]] or 0 for k in anos if ini <= int(k) <= int(a)] + [pop])
                if nv > teto_ver(pmax) or nv < 9 or nv % 2 == 0: ver_fora.append((m["nome"], a, pmax, nv))
            if nv and c and int(a) < ANO and c / nv > 1_500_000: por_ver_alto.append((m["nome"], a, round(c / nv)))
        ks = sorted(k for k in anos if int(k) < ANO)
        for x, y in zip(ks, ks[1:]):
            c1, c2 = anos[x][ix["camara"]] or 0, anos[y][ix["camara"]] or 0
            if c1 > 100000 and c2 > 100000 and (c2 / c1 > 3 or c1 / c2 > 3): saltos.append((m["nome"], x, y, round(c2 / c1, 2)))
    chk(f"Prefeituras {uf}: câmara nunca maior que o gasto total da prefeitura", not camara_maior, f"{len(camara_maior)}: {camara_maior[:3]}")
    chk(f"Prefeituras {uf}: nenhum gasto de câmara negativo publicado", not neg, f"{len(neg)}: {neg[:3]}")
    info(f"Prefeituras {uf}: liquidado/pago > empenhado (restos a pagar, já explicado)", f"{len(liq_maior)} casos")
    # a população anterior a 2017 não está nos dados, então o limite fica só como pista: conferir no TSE
    info(f"Prefeituras {uf}: vereadores acima do limite da Constituição ou em número par (conferir no TSE)", f"{len(ver_fora)}: {ver_fora[:4]}")
    chk(f"Prefeituras {uf}: população preenchida", not pop0, f"{len(pop0)}: {pop0[:3]}")
    info(f"Prefeituras {uf}: saltos de mais de 3× no gasto da câmara de um ano para outro", f"{len(saltos)}: {saltos[:4]}")
    info(f"Prefeituras {uf}: câmara acima de R$ 1,5 mi por vereador/ano", f"{len(por_ver_alto)}: {sorted(por_ver_alto, key=lambda x: -x[2])[:3]}")
    h = E.get(chave)
    if h:
        chk(f"Prefeituras {uf}: total registrado no hub = soma das câmaras de {ANO}", perto(h["registrado_ano"], soma[str(ANO)], 1), f"{h['registrado_ano']} x {round(soma[str(ANO)], 2)}")
        chk(f"Prefeituras {uf}: total_municipios do hub = arquivo", h["total_municipios"] == len(ms), f"{h['total_municipios']} x {len(ms)}")
        chk(f"Prefeituras {uf}: cobertura ≤ total", h["cobertura"] <= h["total_municipios"])
        if "liquidado_ano" in h: info(f"Prefeituras {uf}: liquidado/registrado no ano", f"{h['liquidado_ano']:,.0f} / {h['registrado_ano']:,.0f}")
    return ms, ix

municipios("CE", R / "quanto-custa-municipios/docs/dados", "municipios")
for uf in ["BA", "PE", "PB", "RN"]:
    municipios(uf, R / f"quanto-custa-municipios-{uf.lower()}/docs/dados", f"municipios_{uf.lower()}")

# CE: receitas e gabinetes
r = J(R / "quanto-custa-municipios/docs/dados/resumo.json"); ix = {c: i for i, c in enumerate(r["campos"])}
rec_err, gab_err = [], []
for m in r["municipios"]:
    for a, ln in m["anos"].items():
        rt = ln[ix["receita_total"]] or 0
        partes = sum((ln[ix[k]] or 0) for k in ("transf_uniao", "transf_estado", "receita_propria"))
        if rt and partes > rt * 1.01 + 1: rec_err.append((m["nome"], a, round(partes / rt, 3)))
        g = ln[ix["gasto_total"]] or 0
        if g and (ln[ix["gab_prefeito"]] or 0) + (ln[ix["gab_vice"]] or 0) > g: gab_err.append((m["nome"], a))
info("Prefeituras CE: transferências + receita própria > receita total (provável dedução do Fundeb)", f"{len(rec_err)}: {rec_err[:4]}")
chk("Prefeituras CE: gabinetes ≤ gasto total", not gab_err, str(gab_err[:3]))

# ---------------- deputados estaduais
EST = R / "quanto-custa-deputados-estaduais/docs/dados"
for e in J(EST / "estados.json")["estados"]:
    for ano in e["anos"]:
        p = EST / e["id"] / str(ano) / "resumo.json"
        if not p.exists(): chk(f"Estaduais {e['uf']} {ano}: arquivo existe", False); continue
        r = J(p); t = r["totais"]
        chk(f"Estaduais {e['uf']} {ano}: total = folha + verba", perto(t["total"], t["folha"] + t["verba"], 1))
        chk(f"Estaduais {e['uf']} {ano}: categorias somam a verba", perto(sum(r["categorias"].values()), t["verba"], 5), f"{sum(r['categorias'].values()):.2f} x {t['verba']}")
        pm = r.get("por_mes") or {}
        chk(f"Estaduais {e['uf']} {ano}: meses somam o total", perto(sum((v.get("folha") or 0) + (v.get("verba") or 0) for v in pm.values()), t["total"], 5))
        deps = r.get("deputados") or []
        if deps and isinstance(deps, list) and isinstance(deps[0], dict):
            ks = [k for k in ("total", "custo", "custo_total") if k in deps[0]]
            if ks:
                sd = sum(d.get(ks[0]) or 0 for d in deps)
                chk(f"Estaduais {e['uf']} {ano}: soma dos deputados = total", perto(sd, t["total"], 5), f"{sd:.2f} x {t['total']}")
        if t.get("deputados", 0) > e["vagas"] * 1.6: info(f"Estaduais {e['uf']} {ano}: {t['deputados']} pessoas para {e['vagas']} vagas", "suplentes/trocas")

# ---------------- hub: soma geral e mapa
chk("Hub: total federal = deputados + senadores", perto(HUB["total_ano"], E["deputados"]["total_ano"] + E["senadores"]["total_ano"], 0.02))
mun = [E[k]["total_ano"] for k in E if k.startswith("municipios")]
chk("Hub: total das prefeituras = soma dos estados", perto(HUB["total_ano_municipios"], sum(mun), 0.05))
EJ = J(R / "projetoquantocusta1-alt.github.io/dados/estados.json")
info("Hub: estados.json", json.dumps(EJ, ensure_ascii=False)[:300])

# ---------------- CPF inteiro (regra 4)
# mesmas regras do mascarador do núcleo: CPF com pontuação completa (fora de número maior) ou depois da palavra "CPF"
sys.path.insert(0, str(R / "quanto-custa-nucleo"))
from quanto_custa.privacidade import _CPF_PONTUADO, _CPF_ROTULADO
class _Cpf:
    def finditer(self, t):
        yield from _CPF_ROTULADO.finditer(t); yield from _CPF_PONTUADO.finditer(t)
cpf = _Cpf()
achados = []
for repo in R.glob("quanto-custa-*"):
    for pasta in ("docs", "dados_brutos"):
        for p in (repo / pasta).rglob("*"):
            if p.is_file() and p.suffix in (".json", ".csv", ".html", ".js", ".txt", ".md") and p.stat().st_size < 60_000_000:
                t = p.read_text("utf-8", "ignore")
                for m in cpf.finditer(t): achados.append(f"{p.relative_to(R)}: {m.group()[:4]}…")
for p in (R / "projetoquantocusta1-alt.github.io").rglob("*.json"):
    for m in cpf.finditer(p.read_text("utf-8", "ignore")): achados.append(str(p))
chk("Privacidade: nenhum CPF inteiro em dados, páginas e brutos", not achados, f"{len(achados)}: {achados[:5]}")

ok = sum(1 for s, *_ in res if s == "OK"); er = [x for x in res if x[0] == "ERRO"]
for s, n, d in res:
    if s != "OK": print(f"[{s}] {n} — {d}")
print(f"\n{ok + len(er)} checagens: {ok} ok, {len(er)} com erro; {sum(1 for x in res if x[0]=='INFO')} informativos")
sys.exit(1 if er else 0)
