# Projeto Quanto Custa — Deputados estaduais

Quanto custa cada deputado estadual: salário bruto (folha de pagamento nominal) e verba de gabinete,
nota a nota, com fornecedores e valores corrigidos pela inflação. Começa pelo **Ceará** (Assembleia
Legislativa do Ceará — Alece). Endereço: https://quantocustaum.com/quanto-custa-deputados-estaduais/

## Como funciona

- `atualizar.py` — robô diário (GitHub Actions). Baixa, mês a mês desde 2023:
  - a **verba de desempenho parlamentar (VDP)** — CSV do Portal da Transparência da Alece;
  - a **folha de pagamento** — CSV nominal (deputados nominalmente; demais categorias só em totais);
  - o **cadastro** dos deputados (nome parlamentar, nome completo, partido, foto) no site da Alece.
- `coletor/alece.py` — leitores da Alece. Atenção: o mês vai com dois dígitos (`mes=06`);
  com `mes=6` o portal devolve o arquivo vazio.
- Saídas em `SAIDA` (padrão `docs/dados`) e `BRUTOS` (padrão `dados_brutos`).

## Enquanto o repositório próprio não existe

Por enquanto o robô roda dentro do repositório do hub (`projetoquantocusta1-alt.github.io`):
código em `robo-estaduais/`, site em `quanto-custa-deputados-estaduais/`, workflow
`.github/workflows/estaduais.yml`. Para mudar para um repositório próprio
`quanto-custa-deputados-estaduais` (mesmo endereço no site):

1. copiar `robo-estaduais/*` para a raiz do repositório novo e o site para `docs/`;
2. copiar `.github/workflows/estaduais.yml` (tirar `working-directory` e as variáveis `SAIDA`/`BRUTOS`);
3. ligar o GitHub Pages (branch `main`, pasta `/docs`);
4. apagar as duas pastas e o workflow do hub.

Privacidade: CPF de pessoas físicas sempre mascarado (`***.456.789-**`); da folha, só deputados
aparecem com nome — servidores entram apenas em totais por categoria.
