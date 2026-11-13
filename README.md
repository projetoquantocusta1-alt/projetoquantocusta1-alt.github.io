# Projeto Quanto Custa — hub

Página de entrada do projeto: https://projetoquantocusta1-alt.github.io/

- Mostra o contador do ano (deputados federais + senadores + câmaras e gabinetes dos municípios do Ceará) e leva aos três sites.
- A página não calcula nada: lê só `dados/totais_hub.json`.

## O Mensageiro (`robo/mensageiro.py`)
Robô do GitHub Actions (`.github/workflows/mensageiro.yml`), 3 vezes por dia, depois dos robôs dos outros sites.
Não consulta nenhum site do governo: lê os arquivos que os outros três repositórios já publicaram
(`raw.githubusercontent.com`) e grava `dados/totais_hub.json`. Se uma esfera não responder, mantém o último número bom.

Testes: `python -m pytest -q robo`. Teste com cópias locais: `python robo/mensageiro.py --local /pasta/com/os/repositorios`.

## Fases
1. Contador, cartões das esferas, "O que dava pra fazer?" (feito).
2. Mapa por estado e busca por nome.
3. Maiores notas da semana, fornecedores em mais de uma esfera, busca por CNPJ.
