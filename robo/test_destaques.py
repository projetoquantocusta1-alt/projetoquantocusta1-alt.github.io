import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import destaques as D  # noqa: E402


class F:
    def __init__(self, d):
        self.d = d

    def get(self, k, padrao=None):
        return self.d.get(k, padrao)


def test_ultimas_da_semana():
    fs = F({"2026/resumo.json": {"senadores": [{"id": 1, "nome": "Fulana", "uf": "CE"}]},
            "2026/notas/1.json": {"fornecedores": {"x": ["x", "EMPRESA"]},
                                  "notas": [["2026-10-20", 10, "Divulgação", "x", 900.0, "1", ""],
                                            ["2026-11-02", 11, "Divulgação", "x", 50.0, "2", ""],
                                            ["2026-11-08", 11, "Divulgação", "x", 70.0, "3", ""]]}})
    v, jan = D._janela(D.ultimas_senadores(fs, 2026, "s/"), date(2026, 11, 13))
    assert jan == ["2026-11-02", "2026-11-08"] and sorted(x[1] for x in v) == [50.0, 70.0]
    fd = F({"2026/resumo.json": {"deputados": [{"id": 7, "nome": "Beltrano", "uf": "SP"}]},
            "2026/notas/7.json": {"f": [["c", "LOJA", "doc"]], "c": ["Combustível"], "n": [[1105, 12345, 0, 0, "1", "", 0], [1100, 999, 0, 0, "2", "", 0]]}})
    d = D.ultimas_deputados(fd, 2026, "d/")
    assert d == [["DEP", 123.45, "Combustível — LOJA", "Beltrano", "Deputado(a) · SP", "2026-11-05", "d/?ano=2026#dep-7"]]


def test_multi_esfera():
    fd = F({"2026/fornecedores.json": {"linhas": [["11222333000181", "ALFA LTDA", "", "PJ", 0, 100.0, 3, 2, {}]]}})
    fs = F({"2026/fornecedores.json": {"linhas": [["11222333000262", "ALFA FILIAL", "", "PJ", 40.0, 1, [[5, 40.0, 1]], {}, []],
                                                    ["99888777000166", "BETA", "", "PJ", 10.0, 1, [[5, 10.0, 1]], {}, []]]}})
    fm = F({})
    g, idx = D.fornecedores(fd, fs, fm, 2026)
    m = D.multi_esfera(g, {})
    assert len(m) == 1 and m[0][0] == "11222333" and m[0][3] == 140.0 and m[0][7] == 2
    assert set(idx) == {"11222333000181", "11222333000262", "99888777000166"}
