"""Robô dos deputados estaduais (Ceará / Alece).

Uso:
    python atualizar.py                 # baixa o que falta e monta o site
    python atualizar.py --so-montar     # só remonta o site com o que já está salvo
    python atualizar.py --minutos 60    # tempo máximo de coleta

Saídas (pastas configuráveis por variáveis de ambiente SAIDA e BRUTOS):
    BRUTOS/cadastro.json            nome parlamentar, nome completo, partido, foto (site da Alece)
    BRUTOS/meses/AAAA-MM.json       linhas da verba (VDP) e deputados da folha, por mês
    SAIDA/meta.json                 data, anos, IPCA, situação de cada mês, totais da Assembleia
    SAIDA/AAAA/resumo.json          um registro por deputado no ano
    SAIDA/AAAA/notas/<id>.json      notas (empenhos) da verba de cada deputado
    SAIDA/AAAA/fornecedores.json    quem recebeu da verba no ano
"""
import argparse
import json
import logging
import os
import re
import sys
import time
import traceback
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import config
from coletor import alece, http, ipca
from coletor.privacidade import limpar_json

RAIZ = Path(__file__).parent
SAIDA = Path(os.environ.get("SAIDA") or RAIZ / "docs" / "dados")
BRUTOS = Path(os.environ.get("BRUTOS") or RAIZ / "dados_brutos")
VERSAO = 1
log = logging.getLogger("qce")


def ler(p: Path, padrao=None):
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else padrao
    except json.JSONDecodeError:
        return padrao


def gravar(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(limpar_json(obj), ensure_ascii=False, separators=(",", ":")), "utf-8")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", alece.norm(s).lower()).strip("-")


def meses(ini: int, hoje: date):
    for a in range(ini, hoje.year + 1):
        for m in range(1, 13):
            if (a, m) <= (hoje.year, hoje.month):
                yield a, m


def idade_meses(a: int, m: int, hoje: date) -> int:
    return (hoje.year - a) * 12 + hoje.month - m


# ------------------------------------------------------------------ coleta
def atualizar_ipca():
    try:
        serie = ipca.baixar_ipca(config.ANO_INICIAL)
        gravar(BRUTOS / "ipca.json", ipca.fatores_por_ano(serie))
    except Exception as e:  # noqa: BLE001
        log.warning("IPCA indisponível (%s); mantém o anterior", e)


def atualizar_cadastro():
    cad = ler(BRUTOS / "cadastro.json", {}) or {}
    try:
        lista = alece.ler_lista(alece.baixar_lista())
    except Exception as e:  # noqa: BLE001
        log.warning("lista de deputados indisponível (%s); mantém a anterior", e)
        return cad
    for d in lista:
        k = alece.chave(d["nome"])
        x = cad.get(k, {})
        x.update({k2: v for k2, v in d.items() if v})
        if not x.get("nome_completo"):
            try:
                p = alece.ler_perfil(alece.baixar_perfil(d["slug"]))
                x["nome_completo"] = p.get("nome_completo") or ""
                if p.get("partido"):
                    x["partido"] = p["partido"]
            except Exception as e:  # noqa: BLE001
                log.warning("perfil %s: %s", d["slug"], e)
        x["atual"] = True
        x["visto_em"] = date.today().isoformat()
        cad[k] = x
    atuais = {alece.chave(d["nome"]) for d in lista}
    for k, x in cad.items():
        if k not in atuais:
            x["atual"] = False
    gravar(BRUTOS / "cadastro.json", cad)
    log.info("cadastro: %d deputados no site da Alece (%d no total guardado)", len(lista), len(cad))
    return cad


def coletar(hoje: date, limite_s: float, forcar: bool = False) -> int:
    t0, feitos = time.time(), 0
    for a, m in meses(config.ANO_INICIAL, hoje):
        if time.time() - t0 > limite_s:
            log.warning("tempo esgotado; o resto fica para a próxima execução")
            break
        arq = BRUTOS / "meses" / f"{a}-{m:02d}.json"
        velho = ler(arq)
        if velho and not forcar and not velho.get("vazio") and idade_meses(a, m, hoje) > config.MESES_REBAIXAR:
            continue
        try:
            vdp, recusadas = alece.ler_vdp(alece.baixar_vdp(a, m))
            folha = alece.ler_folha(alece.baixar_folha(a, m))
        except http.SiteForaDoAr as e:
            log.error("%s", e)
            break
        except Exception as e:  # noqa: BLE001
            log.warning("%d-%02d: falhou (%s)", a, m, e)
            continue
        vazio = not vdp and not folha["deputados"]
        if vazio and velho and not velho.get("vazio"):
            log.warning("%d-%02d: veio vazio agora, mas já tinha dados; mantém os antigos", a, m)
            continue
        gravar(arq, {"ano": a, "mes": m, "baixado_em": hoje.isoformat(), "vazio": vazio,
                     "vdp": vdp, "recusadas": recusadas, "folha": folha})
        feitos += 1
        log.info("%d-%02d: %d notas da verba (R$ %.2f), %d recusadas, %d deputados na folha",
                 a, m, len(vdp), sum(x["valor"] for x in vdp), len(recusadas), len(folha["deputados"]))
    return feitos


# ------------------------------------------------------------------ montagem
def montar(hoje: date):
    cad = ler(BRUTOS / "cadastro.json", {}) or {}
    ip = ler(BRUTOS / "ipca.json", {"fatores": {}, "referencia": None})
    por_ano: dict[int, list[dict]] = defaultdict(list)
    for p in sorted((BRUTOS / "meses").glob("*.json")):
        d = ler(p)
        if d:
            por_ano[d["ano"]].append(d)

    # nome completo (folha) -> id; nome parlamentar (verba) -> id
    id_por_completo = {alece.norm(x["nome_completo"]): x["slug"] for x in cad.values() if x.get("nome_completo") and x.get("slug")}
    id_por_parlamentar = {k: x["slug"] for k, x in cad.items() if x.get("slug")}
    info_por_id = {x["slug"]: x for x in cad.values() if x.get("slug")}
    situacao_meses, sem_casar, assembleia = {}, defaultdict(set), {}
    anos = sorted(por_ano)
    for ano in anos:
        deps: dict[str, dict] = {}
        notas: dict[str, list] = defaultdict(list)
        forn: dict[str, dict] = {}
        pessoal = defaultdict(lambda: {"bruta": 0.0, "n_meses": 0, "n_soma": 0})
        por_mes: dict[str, dict] = {}

        def dep(i, nome, completo=""):
            x = deps.get(i)
            if not x:
                inf = info_por_id.get(i, {})
                x = deps[i] = {"id": i, "nome": inf.get("nome") or nome.title(), "nome_completo": inf.get("nome_completo") or completo,
                               "partido": inf.get("partido", ""), "foto": inf.get("foto", ""), "atual": bool(inf.get("atual")),
                               "url": config.ALECE["perfil"].format(slug=i) if i in info_por_id else "",
                               "folha": 0.0, "meses_folha": 0, "verba": 0.0, "meses_verba": 0, "notas": 0,
                               "categorias": defaultdict(float), "situacao": ""}
            return x

        for mes in sorted(por_ano[ano], key=lambda d: d["mes"]):
            chave_mes = f"{ano}-{mes['mes']:02d}"
            situacao_meses[chave_mes] = {"verba": len(mes.get("vdp") or []), "folha": len((mes.get("folha") or {}).get("deputados") or []),
                                         "recusadas": len(mes.get("recusadas") or []),
                                         "recusadas_valor": round(sum(r.get("valor") or 0 for r in mes.get("recusadas") or []), 2)}
            folha = (mes.get("folha") or {}).get("deputados") or []
            por_mes[chave_mes] = {"folha": round(sum(f["bruta"] - f.get("teto", 0) + f.get("decimo", 0) for f in folha), 2),
                                  "verba": round(sum(r["valor"] for r in mes.get("vdp") or []), 2)}
            nomes_folha = [f["nome"] for f in folha]
            id_da_folha = {}
            for f in folha:
                i = id_por_completo.get(alece.norm(f["nome"]))
                if i:
                    id_da_folha[f["nome"]] = i
            # 2ª tentativa: todas as palavras do nome parlamentar dentro de um único nome completo da folha
            candidatos = {k: v for k, v in id_por_parlamentar.items() if v not in id_da_folha.values()}
            for r in mes.get("vdp") or []:
                k = alece.chave(r["deputado"])
                candidatos.setdefault(k, id_por_parlamentar.get(k) or slug(r["deputado"]))
            livres = [n for n in nomes_folha if n not in id_da_folha]
            for k, i in candidatos.items():
                pals = set(k.split())
                achados = [n for n in livres if pals and pals <= set(alece.palavras(n))]
                if len(achados) == 1 and i not in id_da_folha.values():
                    id_da_folha[achados[0]] = i
                    livres.remove(achados[0])
            # verba
            vistos = set()
            for r in mes.get("vdp") or []:
                k = alece.chave(r["deputado"])
                i = id_por_parlamentar.get(k)
                if not i:
                    completo = alece.casar_folha(r["deputado"], nomes_folha, cad)
                    i = id_da_folha.get(completo) if completo else None
                    if not i:
                        i = slug(completo) if completo else slug(r["deputado"])
                        if completo:
                            id_da_folha.setdefault(completo, i)
                        else:
                            sem_casar[ano].add(r["deputado"])
                x = dep(i, r["deputado"])
                x["verba"] += r["valor"]
                x["notas"] += 1
                x["categorias"][r["categoria"]] += r["valor"]
                vistos.add(i)
                notas[i].append([chave_mes, r["empenho"], r["categoria"], r["doc"], r["credor"], r["valor"], r["descricao"]])
                if r["doc"]:
                    fo = forn.setdefault(r["doc"], {"nome": r["credor"], "tipo": r["tipo"], "total": 0.0, "notas": 0, "deps": set()})
                    fo["total"] += r["valor"]
                    fo["notas"] += 1
                    fo["deps"].add(i)
            for i in vistos:
                deps[i]["meses_verba"] += 1
            # folha
            for f in folha:
                i = id_da_folha.get(f["nome"]) or slug(f["nome"])
                x = dep(i, f["nome"], f["nome"])
                if not x["nome_completo"]:
                    x["nome_completo"] = f["nome"]
                x["folha"] += f["bruta"] - f.get("teto", 0) + f.get("decimo", 0)
                x["meses_folha"] += 1
                x["situacao"] = f["situacao"]
            for cat, c in ((mes.get("folha") or {}).get("categorias") or {}).items():
                pa = pessoal[cat]
                pa["bruta"] += c["bruta"]
                pa["n_meses"] += 1
                pa["n_soma"] += c["n"]

        fator = (ip.get("fatores") or {}).get(str(ano)) or (ip.get("fatores") or {}).get(ano) or 1.0
        lista = []
        for x in deps.values():
            x["folha"], x["verba"] = round(x["folha"], 2), round(x["verba"], 2)
            x["total"] = round(x["folha"] + x["verba"], 2)
            x["categorias"] = {k: round(v, 2) for k, v in sorted(x["categorias"].items(), key=lambda kv: -kv[1])}
            lista.append(x)
        lista.sort(key=lambda x: -x["total"])
        cats = defaultdict(float)
        for x in lista:
            for k, v in x["categorias"].items():
                cats[k] += v
        fornecedores = sorted(([doc, f["nome"], f["tipo"], round(f["total"], 2), f["notas"], len(f["deps"])] for doc, f in forn.items()),
                              key=lambda r: -r[3])
        meses_com_verba = sorted(k for k, v in situacao_meses.items() if k.startswith(str(ano)) and v["verba"])
        resumo = {
            "versao": VERSAO, "ano": ano, "fator_ipca": fator, "meses_com_verba": meses_com_verba,
            "ultimo_mes": meses_com_verba[-1] if meses_com_verba else None,
            "totais": {"folha": round(sum(x["folha"] for x in lista), 2), "verba": round(sum(x["verba"] for x in lista), 2),
                       "total": round(sum(x["total"] for x in lista), 2), "deputados": len(lista)},
            "categorias": {k: round(v, 2) for k, v in sorted(cats.items(), key=lambda kv: -kv[1])},
            "por_mes": por_mes,
            "deputados": lista,
        }
        gravar(SAIDA / str(ano) / "resumo.json", resumo)
        pasta_notas = SAIDA / str(ano) / "notas"
        for velho in pasta_notas.glob("*.json"):
            if velho.stem not in notas:
                velho.unlink()
        for i, ns in notas.items():
            gravar(pasta_notas / f"{i}.json", sorted(ns, key=lambda n: (n[0], n[1])))
        gravar(SAIDA / str(ano) / "fornecedores.json", {"campos": ["doc", "nome", "tipo", "total", "notas", "deputados"], "linhas": fornecedores})
        assembleia[str(ano)] = {cat: {"bruta": round(p["bruta"], 2), "media_pessoas": round(p["n_soma"] / p["n_meses"]) if p["n_meses"] else 0,
                                      "meses": p["n_meses"]} for cat, p in sorted(pessoal.items(), key=lambda kv: -kv[1]["bruta"])}
        log.info("%d: %d deputados, folha R$ %.2f, verba R$ %.2f", ano, len(lista), resumo["totais"]["folha"], resumo["totais"]["verba"])

    gravar(SAIDA / "meta.json", {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "versao": VERSAO, "uf": config.ALECE["uf"], "casa": config.ALECE["nome"], "sigla": config.ALECE["sigla"],
        "anos": anos, "ipca": ip, "meses": situacao_meses,
        "pessoal_assembleia": assembleia,
        "sem_casar": {str(a): sorted(v) for a, v in sem_casar.items()},
        "fontes": {"verba": config.ALECE["vdp_pagina"], "folha": config.ALECE["folha_pagina"], "deputados": config.ALECE["lista_deputados"]},
    })


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-montar", action="store_true")
    ap.add_argument("--forcar", action="store_true", help="baixa de novo todos os meses")
    ap.add_argument("--minutos", type=float, default=90)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    hoje = date.today()
    if not args.so_montar:
        atualizar_ipca()
        atualizar_cadastro()
        coletar(hoje, args.minutos * 60, args.forcar)
    montar(hoje)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
