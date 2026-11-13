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


def test_novas_senadores(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "ESTADO", tmp_path)
    base = {"2026/resumo.json": {"senadores": [{"id": 1, "nome": "Fulana", "uf": "CE"}]},
            "2026/notas/1.json": {"fornecedores": {"x": ["x", "EMPRESA"]},
                                  "notas": [["2026-10-01", 10, "Divulgação", "x", 100.0, "1", ""] for _ in range(1)]
                                  + [["2026-10-0%d" % i, 10, "Divulgação", "x", 50.0 + i, str(i), ""] for i in range(2, 9)]}}
    assert D.novas_senadores(F(base), 2026, date(2026, 11, 13), "s/") == []          # 1ª vez: só guarda
    base["2026/notas/1.json"]["notas"].append(["2026-11-10", 11, "Divulgação", "x", 999.0, "9", ""])
    nv = D.novas_senadores(F(base), 2026, date(2026, 11, 14), "s/")
    assert len(nv) == 1 and nv[0][1] == 999.0 and nv[0][0] == "SEN"
    assert D.novas_senadores(F(base), 2026, date(2026, 11, 25), "s/") == []        # passou a semana


def test_multi_esfera():
    fd = F({"2026/fornecedores.json": {"linhas": [["11222333000181", "ALFA LTDA", "", "PJ", 0, 100.0, 3, 2, {}]]}})
    fs = F({"2026/fornecedores.json": {"linhas": [["11222333000262", "ALFA FILIAL", "", "PJ", 40.0, 1, [[5, 40.0, 1]], {}, []],
                                                    ["99888777000166", "BETA", "", "PJ", 10.0, 1, [[5, 10.0, 1]], {}, []]]}})
    fm = F({})
    g, idx = D.fornecedores(fd, fs, fm, 2026)
    m = D.multi_esfera(g, {})
    assert len(m) == 1 and m[0][0] == "11222333" and m[0][3] == 140.0 and m[0][7] == 2
    assert set(idx) == {"11222333000181", "11222333000262", "99888777000166"}
