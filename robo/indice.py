"""Índice de Transparência e Governança Pública (prévia).

Gera dados/indice.json com uma nota de 0 a 100 para:
  - Assembleias Legislativas avaliadas (robo/indice_assembleias.json, com as provas; a pontualidade é calculada
    aqui, a partir dos meses que a Assembleia já publicou);
  - prefeituras e câmaras do Ceará (TCE-CE) e dos estados pelo Tesouro Nacional (SICONFI), calculadas sozinhas a partir
    do que os robôs encontraram: entrega no prazo, números que fecham e anos anteriores completos.

Uso:
    python robo/indice.py                      # lê os dados publicados no GitHub
    python robo/indice.py --local /home/user   # teste com cópias locais dos repositórios
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mensageiro import SICONFI, Fonte  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "indice.json"
ASSEMBLEIAS = Path(__file__).resolve().parent / "indice_assembleias.json"
INICIO = 2017  # primeiro ano com dados municipais nos dois estados

PESOS_ASSEMBLEIA = [
    ("acesso", "Acesso", 15, "O site responde ao robô e a quem está fora? Sem bloqueio, erro ou certificado inválido."),
    ("formato", "Formato aberto", 15, "Planilha, arquivo de dados ou API vale mais que página a página ou PDF."),
    ("detalhe", "Detalhe", 20, "Nota a nota, com o CNPJ do fornecedor; folha com o nome de cada pessoa."),
    ("pontualidade", "Pontualidade", 20, "O mês passado já está publicado? Perde pontos a cada mês de atraso."),
    ("consistencia", "Consistência", 15, "Os números fecham? Sem linhas estranhas misturadas nem totais que não batem."),
    ("cadastro", "Cadastro", 5, "Cada deputado com um código fixo e o nome escrito sempre igual."),
    ("historico", "Histórico", 5, "Anos anteriores disponíveis e no mesmo formato."),
    ("estabilidade", "Estabilidade", 5, "Endereços que não mudam, campos explicados, sem armadilhas."),
]
PESOS_MUNICIPIO = [
    ("pontualidade", "Entrega no prazo", 35, "O ano atual já foi entregue ao tribunal de contas ou ao Tesouro até o período que a maioria das cidades já entregou?"),
    ("consistencia", "Números que fecham", 35, "Em cada ano, os números da câmara conferem? (notas x balancete no Ceará; câmara zerada ou fora do padrão nos estados pelo Tesouro)"),
    ("historico", "Anos anteriores", 30, f"De {INICIO} até o ano passado, quantos anos foram entregues completos?"),
]
MESES = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
BIMESTRES = ["", "jan–fev", "mar–abr", "mai–jun", "jul–ago", "set–out", "nov–dez"]
LIMITE_DIFERENCA = 0.01  # Ceará: diferença entre notas e balancete acima de 1% do gasto da câmara


def faixa(n: float | None) -> str:
    return "sem" if n is None else "boa" if n >= 80 else "regular" if n >= 50 else "ruim"


def tit(n: str) -> str:
    return " ".join(p if (i and p in {"de", "da", "do", "das", "dos", "e"}) else p.capitalize()
                    for i, p in enumerate(str(n or "").lower().split()))


def lista(anos: list) -> str:
    anos = sorted(anos)
    if not anos:
        return ""
    # agrupa anos seguidos: 2017–2020, 2023
    grupos, ini, ant = [], anos[0], anos[0]
    for a in anos[1:] + [None]:
        if a is not None and a == ant + 1:
            ant = a
            continue
        grupos.append(str(ini) if ini == ant else f"{ini}–{ant}")
        if a is not None:
            ini = ant = a
    return ", ".join(grupos)


# ------------------------------------------------------------------ Assembleias
def pontualidade_assembleia(meta: dict | None, hoje: date) -> tuple[int | None, str]:
    """20 pontos se o mês passado já está publicado; perde 5 por mês de atraso."""
    meses = sorted(k for k, v in ((meta or {}).get("meses") or {}).items() if (v or {}).get("verba"))
    if not meses:
        return None, "Não foi possível ler os meses publicados hoje."
    a, m = map(int, meses[-1].split("-"))
    alvo = (hoje.year * 12 + hoje.month - 1) - 1  # mês passado
    atraso = max(0, alvo - (a * 12 + m - 1))
    pts = max(0, 20 - 5 * atraso)
    txt = f"Último mês com a verba publicada: {MESES[m]} de {a}."
    txt += " Em dia." if not atraso else f" Atraso de {atraso} {'mês' if atraso == 1 else 'meses'}."
    return pts, txt


def assembleias(fe: Fonte, hoje: date) -> dict:
    cfg = json.loads(ASSEMBLEIAS.read_text("utf-8"))
    out = []
    for a in cfg["avaliadas"]:
        crit = dict(a["criterios"])
        crit["pontualidade"] = list(pontualidade_assembleia(fe.get(f"{a['repo_uf']}/meta.json"), hoje))
        linhas, pts, max_ = [], 0, 0
        for cid, nome, peso, _ in PESOS_ASSEMBLEIA:
            p, prova = crit.get(cid, [None, "Ainda não avaliado."])
            linhas.append([cid, p, peso, prova])
            if p is not None:
                pts += p
                max_ += peso
        nota = round(100 * pts / max_) if max_ else None
        out.append({"id": a["id"], "sigla": a["sigla"], "nome": a["nome"], "uf": a["uf"], "fonte": a["fonte"],
                    "avaliado_em": a["avaliado_em"], "nota": nota, "faixa": faixa(nota), "criterios": linhas,
                    "fora_da_conta": [c for c, p, _, _ in linhas if p is None]})
    out.sort(key=lambda x: -(x["nota"] or -1))
    return {"avaliadas": out, "sem_nota": cfg["sem_nota"]}


# ------------------------------------------------------------------ municípios
def nota_municipio(pts: list[float]) -> int:
    return round(sum(pts))


def municipios_ce(fm: Fonte, ano: int) -> list[dict]:
    r = fm.get("resumo.json") or {}
    if not r.get("municipios"):
        return []
    ix = {k: i for i, k in enumerate(r["campos"])}
    v = lambda l, k: l[ix[k]] if k in ix and ix[k] < len(l) else None  # noqa: E731
    # mês de referência: o mês que a maioria das cidades já tem no ano atual
    meses = Counter(int(v(m["anos"][str(ano)], "mes_ref") or 0) % 100 for m in r["municipios"] if str(ano) in m["anos"])
    esperado = meses.most_common(1)[0][0] if meses else 12
    out = []
    for m in r["municipios"]:
        A = m["anos"]
        provas = []
        # entrega no prazo (ano atual)
        l = A.get(str(ano))
        if not l:
            p1 = 0.0
            provas.append(["ruim", f"Nada de {ano} no TCE-CE."])
        else:
            mes = int(v(l, "mes_ref") or 0) % 100
            pref = v(l, "gasto_total") is not None
            cam = v(l, "situacao_camara") != "sem_balancete"
            frac = min(1.0, mes / esperado) if esperado else 1.0
            p1 = 35 * (0.5 * pref + 0.5 * cam) * frac
            if not pref:
                provas.append(["ruim", f"A prefeitura não enviou o balancete de {ano} ao TCE-CE (só a câmara enviou)."])
            if not cam:
                provas.append(["ruim", f"A câmara não enviou o balancete de {ano} ao TCE-CE; o valor vem só das notas de empenho."])
            if mes < esperado:
                provas.append(["atencao", f"Dados de {ano} só até {MESES[mes]}; a maioria das cidades já tem até {MESES[esperado]}."])
            if pref and cam and mes >= esperado:
                provas.append(["bom", f"Prefeitura e câmara com os balancetes de {ano} enviados até {MESES[mes]}."])
        # números que fecham
        presentes = [a for a in range(INICIO, ano + 1) if str(a) in A]
        ruins = []
        for a in presentes:
            la = A[str(a)]
            cam = v(la, "camara") or 0
            dif = abs(v(la, "diferenca_camara") or 0)
            if v(la, "situacao_camara") == "diferenca" and cam and dif / cam > LIMITE_DIFERENCA:
                ruins.append(a)
        p2 = 35 * (1 - len(ruins) / len(presentes)) if presentes else 0.0
        if ruins:
            provas.append(["ruim", f"Notas de empenho da câmara e balancete não batem (diferença de mais de 1%) em {lista(ruins)}."])
        elif presentes:
            provas.append(["bom", "Notas de empenho da câmara e balancete conferem em todos os anos."])
        # anos anteriores
        fechados = list(range(INICIO, ano))
        falta = [a for a in fechados if str(a) not in A or v(A[str(a)], "gasto_total") is None
                 or v(A[str(a)], "situacao_camara") == "sem_balancete"]
        p3 = 30 * (1 - len(falta) / len(fechados))
        if falta:
            provas.append(["ruim", f"Anos sem os balancetes completos no TCE-CE: {lista(falta)}."])
        else:
            provas.append(["bom", f"Todos os anos de {INICIO} a {ano - 1} completos no TCE-CE."])
        pts = [round(p1, 1), round(p2, 1), round(p3, 1)]
        nota = nota_municipio(pts)
        out.append({"uf": "CE", "nome": tit(m["nome"]), "id": m.get("sim"), "nota": nota, "faixa": faixa(nota),
                    "pts": pts, "provas": provas})
    return out


def municipios_siconfi(fb: Fonte, ano: int, uf: str) -> list[dict]:
    r, meta = fb.get("resumo.json") or {}, fb.get("meta.json") or {}
    if not r.get("municipios"):
        return []
    # primeira coleta ainda em andamento: o estado entra quando o ano passado tiver ao menos 90% das cidades
    total = meta.get("total_municipios") or len(r["municipios"])
    if (meta.get("cobertura") or {}).get(str(ano - 1), 0) < 0.9 * total:
        return []
    ix = {k: i for i, k in enumerate(r["campos"])}
    v = lambda l, k: l[ix[k]] if k in ix and ix[k] < len(l) else None  # noqa: E731
    esperado = int((meta.get("periodo_mais_comum") or {}).get(str(ano)) or 6)
    out = []
    for m in r["municipios"]:
        A = m["anos"]
        provas = []
        l = A.get(str(ano))
        if not l:
            p1 = 0.0
            provas.append(["ruim", f"Nenhum relatório de {ano} (RREO) entregue ao Tesouro; a maioria das cidades já entregou até {BIMESTRES[esperado]}."])
        else:
            b = int(v(l, "periodo") or 0)
            p1 = 35 * min(1.0, b / esperado)
            if b < esperado:
                provas.append(["atencao", f"Relatório de {ano} entregue só até {BIMESTRES[b]}; a maioria das cidades já entregou até {BIMESTRES[esperado]}."])
            else:
                provas.append(["bom", f"Relatório de {ano} entregue ao Tesouro até {BIMESTRES[b]}, junto com a maioria."])
        presentes = [a for a in range(INICIO, ano + 1) if str(a) in A]
        zer = [a for a in presentes if v(A[str(a)], "alerta") == "zerada"]
        fora = [a for a in presentes if v(A[str(a)], "alerta") == "fora_do_padrao"]
        p2 = 35 * (1 - (len(zer) + len(fora)) / len(presentes)) if presentes else 0.0
        if zer:
            provas.append(["ruim", f"Câmara veio zerada no relatório da prefeitura em {lista(zer)}."])
        if fora:
            provas.append(["ruim", f"Valor da câmara fora do padrão no relatório em {lista(fora)}."])
        if presentes and not (zer or fora):
            provas.append(["bom", "O valor da câmara confere em todos os relatórios entregues."])
        fechados = list(range(INICIO, ano))
        falta = [a for a in fechados if str(a) not in A]
        parcial = [a for a in fechados if str(a) in A and int(v(A[str(a)], "periodo") or 0) < 6]
        p3 = 30 * (1 - (len(falta) + 0.5 * len(parcial)) / len(fechados))
        if falta:
            provas.append(["ruim", f"Anos sem relatório entregue ao Tesouro: {lista(falta)}."])
        if parcial:
            provas.append(["atencao", f"Anos entregues só em parte (sem o último bimestre): {lista(parcial)}."])
        if not (falta or parcial):
            provas.append(["bom", f"Todos os anos de {INICIO} a {ano - 1} entregues completos ao Tesouro."])
        pts = [round(p1, 1), round(p2, 1), round(p3, 1)]
        nota = nota_municipio(pts)
        out.append({"uf": uf, "nome": m["nome"], "id": m.get("ibge"), "nota": nota, "faixa": faixa(nota),
                    "pts": pts, "provas": provas})
    return out


def resumo(ms: list[dict]) -> dict:
    out = {}
    for uf in sorted({m["uf"] for m in ms}) + [""]:
        s = [m for m in ms if not uf or m["uf"] == uf]
        c = Counter(m["faixa"] for m in s)
        out[uf or "todos"] = {"n": len(s), "media": round(sum(m["nota"] for m in s) / len(s)) if s else None,
                              "boa": c["boa"], "regular": c["regular"], "ruim": c["ruim"]}
    return out


def montar(local: Path | None = None, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    ano = hoje.year
    fe = Fonte("quanto-custa-deputados-estaduais", local)
    fm = Fonte("quanto-custa-municipios", local)
    ms = municipios_ce(fm, ano)
    for u in SICONFI:
        ms += municipios_siconfi(Fonte(f"quanto-custa-municipios-{u.lower()}", local), ano, u)
    ms.sort(key=lambda m: (m["nota"], m["nome"]))
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"), "ano": ano, "inicio": INICIO,
        "pesos": {"assembleias": [list(p) for p in PESOS_ASSEMBLEIA], "municipios": [list(p) for p in PESOS_MUNICIPIO]},
        "assembleias": assembleias(fe, hoje),
        "municipios": ms, "resumo_municipios": resumo(ms),
        "fontes": {"CE": "Tribunal de Contas do Estado do Ceará (TCE-CE)", **{u: "Tesouro Nacional (SICONFI), RREO" for u in SICONFI}},
        "nomes_uf": {"CE": "Ceará", **SICONFI},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", type=Path, help="pasta com cópias dos repositórios (teste)")
    args = ap.parse_args(argv)
    out = montar(args.local)
    if not out["municipios"] or not out["assembleias"]["avaliadas"]:
        print("Dados incompletos; arquivo anterior mantido.")
        return 1
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print("indice.json:", {k: v for k, v in out["resumo_municipios"].items()},
          [(a["sigla"], a["nota"]) for a in out["assembleias"]["avaliadas"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
