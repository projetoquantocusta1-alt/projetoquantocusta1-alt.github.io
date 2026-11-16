import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mensageiro as M  # noqa: E402


def _g(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), "utf-8")


def test_montar(tmp_path):
    d = tmp_path / "quanto-custa-deputados" / "docs" / "dados"
    _g(d / "meta.json", {"atualizado_em": "x"})
    _g(d / "historico.json", {"anos": [{"ano": 2025, "meses_decorridos": 12, "total": 100, "total_corrigido": 1026, "fator_ipca": 1.0,
                                        "categorias": {"Passagens aéreas": 50, "Telefonia": 10, "Divulgação do mandato": 30}},
                                       {"ano": 2026, "meses_decorridos": 10, "total": 90, "total_corrigido": 91}]})
    _g(d / "2026" / "resumo.json", {"meses_decorridos": 10, "total_camara": 90, "previsao_camara": {"ja_gasto": 90, "restante": 18, "total_ano": 108}})
    s = tmp_path / "quanto-custa-senadores" / "docs" / "dados"
    _g(s / "meta.json", {"anos": [2025, 2026]})
    _g(s / "2025" / "resumo.json", {"ano": 2025, "fechado": True, "total": 81, "fator_ipca": 1.0,
                                    "senadores": [{"nome": "A", "custos": {"ceaps": 5}, "categorias": {"Passagens aéreas, aquáticas e terrestres": 10, "Consultorias": 3}}]})
    _g(s / "2026" / "resumo.json", {"ano": 2026, "meses_decorridos": 10, "total": 20, "total_ceaps": 8,
                                    "senadores": [{"nome": "B", "custos": {"ceaps": 6}}]})
    m = tmp_path / "quanto-custa-municipios" / "docs" / "dados"
    _g(m / "meta.json", {"total_municipios": 2, "ipca": {"fatores": {}}})
    campos = ["mes_ref", "populacao", "gasto_total", "camara", "gab_prefeito", "gab_vice", "n_vereadores"]
    _g(m / "resumo.json", {"campos": campos, "municipios": [{"anos": {"2026": [202605, 0, 0, 50, 0, 0, 9]}}, {"anos": {}}]})
    out = M.montar(tmp_path, hoje=date(2026, 11, 13))
    es = out["esferas"]
    assert es["deputados"]["contador"]["teto"] == 108 and es["deputados"]["faltas_plenario"] is None
    assert es["senadores"]["maior_cota"] == {"nome": "B", "valor": 6} and es["senadores"]["dava"]["base"] == 10
    mun = es["municipios"]
    assert mun["em_coleta"] and mun["cobertura"] == 1 and mun["total_ano"] == 100 and mun["previsto_ano"] == 120
    assert out["dava"]["base"] == 90 and out["dava"]["excesso"] == 72
    assert out["total_ano"] == 90 + 20 and out["total_ano_municipios"] == 100   # Congresso à parte do Ceará


def test_mantem_ultimo_bom(tmp_path):
    anterior = {"esferas": {"senadores": {"ano": 2026, "total_ano": 5, "contador": {"ja": 5, "inicio": "2026-11-01", "por_seg": 0, "teto": 5}}}}
    out = M.montar(tmp_path, hoje=date(2026, 11, 13), anterior=anterior)
    assert out["esferas"]["senadores"]["total_ano"] == 5 and out["status"]["senadores"].startswith("mantido")


def test_validacoes():
    ok = {"historico": [[2024, 100.0, True], [2025, 155.0, True], [2026, 10.0, False]]}
    assert M.validar("deputados", ok, 2026) == []
    ruim = {"historico": [[2024, 100.0, True], [2025, 30.0, True]]}
    assert M.validar("senadores", ruim, 2026)
    mun = {"historico": [], "vereadores": 316, "_conferir": {"vereadores_fonte": 2190}, "cobertura": 184, "total_municipios": 184, "em_coleta": False}
    assert any("vereadores" in e for e in M.validar("municipios", mun, 2026))


def test_municipios_previsao_pelo_ritmo_do_pago(tmp_path):
    """Câmara empenha o ano quase todo em janeiro: a previsão segue o pago, não o empenhado."""
    m = tmp_path / "quanto-custa-municipios" / "docs" / "dados"
    _g(m / "meta.json", {"total_municipios": 2, "ipca": {"fatores": {}}})
    campos = ["mes_ref", "populacao", "gasto_total", "camara", "gab_prefeito", "gab_vice", "n_vereadores", "camara_pago"]
    _g(m / "resumo.json", {"campos": campos, "municipios": [
        {"anos": {"2026": [202606, 0, 0, 100, 0, 0, 9, 60]}},     # empenhou 100, pagou 60 em 6 meses -> 120 no ano
        {"anos": {"2026": [202606, 0, 0, 30, 0, 0, 9, None]}},    # sem balancete: usa o empenhado -> 60 no ano
    ]})
    mun = M.montar(tmp_path, hoje=date(2026, 7, 10))["esferas"]["municipios"]
    assert mun["previsto_ano"] == 180 and mun["registrado_ano"] == 130 and mun["pago_ano"] == 90
