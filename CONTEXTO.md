# CONTEXTO DO PROJETO — leia isto primeiro

**Para que serve:** quando uma conversa com o Claude ficar grande (cara), comece outra e peça "leia o
CONTEXTO.md do repositório `projetoquantocusta1-alt.github.io`". Ele tem o **essencial para continuar sem reler
conversas antigas**: como o projeto funciona e as armadilhas já descobertas.

- **O que fazer / pendências ficam nas GitHub Issues**, não aqui (assim este arquivo fica curto e barato de ler).
- O **histórico detalhado** do que já foi feito está no **git** (mensagens de commit) — não repetimos aqui.
- Registre neste arquivo só o que for **conhecimento durável** (uma fonte nova, uma regra, uma armadilha).

Última atualização: 2026-11-28.

---

## 1. O que é o projeto

"Quanto Custa?" — sites de transparência de gasto público em **quantocustaum.com** (GitHub Pages). Mostra quanto
custam os políticos e para onde vai o dinheiro, com **dados oficiais, atualizados todo dia por robôs, corrigidos
pela inflação (IPCA)**. Feito pela "Sociedade do Progresso" (sem nome de autor — regra 5).

O dono **não é programador**: responder sempre em **português simples**. Publicar na `main` é autorizado.

## 2. Repositórios (todos em github.com/projetoquantocusta1-alt)

| Repositório | O que é | Fonte |
|---|---|---|
| `projetoquantocusta1-alt.github.io` | **Hub** (raiz do site) + Índice de Governança | junta os outros |
| `quanto-custa-deputados` | Deputados federais | Câmara (dados abertos) |
| `quanto-custa-senadores` | Senadores (+ `sondar.py`/`sondagem.yml`, ver §6) | Senado |
| `quanto-custa-municipios` | **Página única das prefeituras** (seletor de estado) + **Ceará** | TCE-CE (nota a nota) |
| `quanto-custa-municipios-<uf>` | Prefeituras por estado — **18 estados** (NE + Centro-Oeste + Norte) | **SICONFI / Tesouro** |
| `quanto-custa-deputados-estaduais` | Deputados estaduais: **CE, BA, RN, MG** | portais das Assembleias |
| `quanto-custa-divida` | Dívida pública (BC: SGS, Demab, Focus, IF.data) | Banco Central |
| `quanto-custa-devedores` | Devedores da União (Dívida Ativa) | PGFN |
| `quanto-custa-nucleo` | núcleo comum | — |

Os 18 estados SICONFI: BA, PE, PB, RN, MA, PI, AL, SE (Nordeste) + GO, MT, MS (Centro-Oeste) + AC, AM, AP, PA, RO, RR, TO (Norte).
**Endereços:** `/`, `/indice/`, `/quanto-custa-deputados/`, `/quanto-custa-senadores/`, `/quanto-custa-municipios/`
(+`?uf=<uf>`), `/quanto-custa-deputados-estaduais/` (+`?uf=ba|rn|mg`), `/quanto-custa-divida/`, `/quanto-custa-devedores/`.

## 3. Regras do projeto (valem para tudo; detalhe em PLANO.md)

1. **Toda limitação dos dados é explicada no site** (na página e na Metodologia), com o motivo.
2. **Divergência nos dados oficiais é sempre informada**, dizendo de quem é a responsabilidade.
3. **Não publicar número que não dá para conferir** — na dúvida, fica de fora, com aviso.
4. **CPF nunca inteiro** — mascarado (`***.456.789-**`) em dados, páginas e brutos. Mascarador em
   `quanto-custa-nucleo/.../privacidade.py`, com **cópias idênticas** em `coletor/privacidade.py` de deputados,
   senadores, municipios e estaduais: **mudou um, copie nos outros.**
5. **Anonimato** — nenhum nome de autor nem link pessoal.
6. **robots.txt respeitado**; robôs consultam devagar (1 consulta/s).
7. Robôs gravam como `robo-quanto-custa`; **não enviar mudanças enquanto o robô do mesmo repo salva**.
8. **Não mudar as cores do mapa.** Vermelho dos indicadores: **#c4161c**. Marca: **"Quanto Custa"** (sem "Projeto").
9. **Linguagem simples no site** (qualquer pessoa entende); jargão técnico fica para o "modo acadêmico" no futuro.
10. Layouts leves: mostrar o essencial, abrir o resto sob demanda.

## 4. Como funciona cada parte

- **Hub** (`robo/mensageiro.py` + `robo/indice.py`): lê os JSON publicados dos outros repos (raw.githubusercontent,
  ou `--local /home/user` em teste) e gera `dados/totais_hub.json` (esferas, contador, dívida nacional),
  `dados/estados.json` (mapa), `dados/busca.json`, `dados/indice.json`. Página: `index.html`, `hub.js`, `hub.css`.
- **Prefeituras — Ceará:** TCE-CE, **nota a nota** (empenhos, fornecedores, pago). App: `quanto-custa-municipios/docs/app.js` (usa `E.sim`).
- **Prefeituras — 18 estados (SICONFI):** **código genérico** idêntico; só muda o bloco "ESTADO" do `config.py` e o
  bloco `CFG` no topo de `docs/uf.js`. A página única carrega `app.js` (CE) ou `../quanto-custa-municipios-<uf>/uf.js`.
  SICONFI dá só **totais por área** (sem fornecedor/gabinetes): função "Legislativa" = câmara; **liquidado**, não pago; bimestral.
- **Dívida das prefeituras (RGF/SICONFI):** a **dívida consolidada líquida (DCL)** vem do **RGF, Anexo 2** do SICONFI
  (`coletor/siconfi.py` → `rgf2()/ler_rgf2()`), buscada por **IBGE**, em **todos os 19 estados** (inclusive o CE, cujo
  TCE não tem dívida). Cache por ano em `dados_brutos/rgf/<ibge>.json`. `atualizar.py` grava o bloco `divida` em cada
  `m/<id>.json` (com previsão por tendência linear) e um `divida.json` (ranking, com população e dívida/habitante). UI:
  aba **"Dívida"** (ranking) + bloco na ficha. No hub, `divida_nacional()` junta tudo num painel nacional. A API já traz
  **% da DCL sobre a RCL e o limite de 120%** (Resolução 40/2001) prontos. Valores **nominais** (dívida não leva IPCA).
- **Deputados estaduais** (`quanto-custa-deputados-estaduais`): `docs/dados/<uf>/`; `docs/app.js` multi-estado ("Todos
  os estados"). O seletor é **dinâmico** (lê `estados.json`); **estado sem dados não entra**. Cada Assembleia tem coletor
  próprio (`coletor/alece.py`, `alba.py`, `alrn.py`, `almg.py`). Coleta a **Bahia por último** (mais lenta). Input `--uf`.
  - **CE (Alece):** verba VDP (CSV) + folha nominal. **BA (ALBA):** verba indenizatória nota a nota, sem folha (subsídio de lei).
  - **RN (ALRN):** API com token que o portal embute no código público; `coletor/alrn.py` **lê o token do site a cada run**.
  - **MG (ALMG):** verba indenizatória nota a nota do portal `almg.gov.br` (não da API); sem folha (subsídio = teto constitucional).
- **Índice de Transparência e Governança** (`/indice/`, prévia): nota 0–100 por órgão (Assembleias: critérios em
  `robo/indice_assembleias.json`; prefeituras: 3 critérios automáticos).

## 5. Regra de publicação de um estado SICONFI

Um estado entra no hub/Índice quando a **primeira coleta terminou** = `cobertura[ano-1] + faltas[ano-1] >= 0.98*total`.
Motivo: em vários estados, **parte dos municípios realmente não envia o relatório ao Tesouro** (confirmado: a API
responde vazio). Isso é o retrato real, não coleta parcial → publicamos **"com aviso"** (KPI "Sem relatório no Tesouro: N",
nota 0 no Índice com prova, mapa "X de Y enviaram"). Os que não enviaram vão para "Quem não prestou contas".

## 6. O container NÃO acessa sites do governo nem o quantocustaum.com

- **Coleta real:** só nos **runners do GitHub Actions** (os robôs). Daqui dá para disparar e ler logs (`mcp__github__*`).
- **Testar uma fonte nova (gov):** workflow **`sondagem.yml` do repo senadores** (inputs: `urls` separadas por espaço,
  `cabecalhos` JSON). Baixa URLs arbitrárias dos runners, lê xlsx/PDF/JSON como texto, **mascara CPF**. Saída em
  `quanto-custa-senadores/dados_brutos/sondagem/`.
- **Testar o SITE:** renderizar **localmente** — `python3 -m http.server`, diretório espelho com symlinks (p. ex.
  `/tmp/site/quanto-custa-municipios` → `.../docs` e `/tmp/site/quanto-custa-municipios-ba` → `.../docs`, lado a lado),
  Playwright abrindo `http://localhost:PORT/quanto-custa-municipios/?uf=xx`. Esconder `#bv` (modal de boas-vindas).
  Checar `pageerror` e rolagem lateral. Chromium/Playwright já instalados (ver instruções da sessão).

## 7. Robôs / horários (UTC) e como rodar

- **Hub** `mensageiro.yml`: 11:47, 15:07 (`--completo`), 21:37 (também roda `robo/indice.py`).
- **Deputados estaduais** `atualizar.yml`: 10:41. Inputs `forcar`, `uf` (ce/ba/rn/mg/vazio).
- **Prefeituras** (cada `-<uf>`) `atualizar.yml`: de madrugada + semanal domingo (TSE/IBGE/IPCA). CE (`quanto-custa-municipios`): idem.
- **Senadores** `sondagem.yml`: só manual. **Devedores**: segunda 14:41. **Dívida pública**: 13:17.

## 8. Convenções de trabalho (como o Claude deve agir)

- **Publicar na `main`** e force-sync da branch `claude/proposed-changes-bugs-f0f8xj`. **Não criar PR** sem pedido.
- **Rodapé de commit**: usar as linhas que o lembrete da sessão indicar (`Co-Authored-By` + `Claude-Session`).
- **Não reescrever commits do robô** (`robo-quanto-custa`, aparecem "Unverified" — é normal).
- **Robô empurra dados o tempo todo:** antes de `push`, faça `git fetch origin main && git merge --no-edit FETCH_HEAD`
  (o merge de dados é esperado; **nunca** force-push na `main`). `git reset --hard` costuma ser bloqueado.
- Ao mudar um arquivo servido (js/css), **suba o `?v=N`** nos HTML que o referenciam (cache). Para os estados SICONFI,
  a versão do `uf.js` fica no **ESTADOS do `quanto-custa-municipios/docs/index.html`**.
- **Auditoria de sempre** (quando o dono pedir): (1) robôs no Actions; (2) `python -m pytest -q` por repo; (3)
  `python robo/auditoria.py --local /home/user` (ERRO = corrigir, INFO = olhar); (4) render local (§6).
- **Registrar no CONTEXTO** só conhecimento durável; **pendências vão para as Issues**.

## 9. Armadilhas já descobertas (evitam retrabalho)

- **Portais de governo caem de madrugada.** O `almg.gov.br` não aceitava conexão às 23h–00h BRT (coleta vazia);
  **de dia (horário comercial BR) funciona**. Lição: re-rodar coletas de portais gov em horário comercial. Além disso,
  `coletor/http.py` dos estaduais **força IPv4** (`allowed_gai_family=AF_INET`) porque runners do GitHub às vezes não
  têm rota IPv6 (erro "Network is unreachable"/Errno 101).
- **XSS nos rótulos de KPI:** escapar o **dado não-confiável na origem** (nome de fornecedor via `esc()`/`quem()`),
  **não** o rótulo inteiro do cartão — alguns rótulos usam HTML de propósito (os `<span class="termo">` dos tooltips de
  jargão). Escapar o rótulo todo fez os `termo` aparecerem como código cru. (Nomes em `<canvas>`, como a geração de
  imagem do ranking, não são vetor de XSS: canvas é texto.)
- **Dívida: a DCL pode ser negativa** (cidade com mais caixa que dívida) — não cortar em zero; e a **previsão** mira
  `max(anos)+1` para não colidir com o ano corrente parcial. Os `>200%` da RCL que apareceram (ex.: Itapebi, Caetité)
  são **reais** (consistentes com a API), não erro.
- **Dívida por ano (`por_ano`):** o `divida.json` de cada estado traz, por cidade, `por_ano = {ano: [dcl, % da receita,
  população, fechado(1/0)]}` (população vem do próprio RGF). O ranking no site usa o **ano do filtro** via `por_ano`;
  `acima`/`alerta` saem do % (120% teto, 108% alerta). Dado antigo sem `por_ano` cai no ano mais recente (fallback no JS).
  Estado só passa a trocar de ano no filtro **depois de re-coletar** com o código novo (daí disparar os `atualizar.yml`).
- **Casos que NÃO são erro** (o dono mandou manter): câmara "zerada/negativa" (já excluída da soma); "liquidado >
  empenhado" (restos a pagar); custo por vereador alto nas capitais; empenhado do ano em andamento ≈ ano fechado
  (empenham o ano todo no começo); cobertura baixa de um estado (municípios que não entregaram, não é bug).

## 10. Estado atual (no ar)

Deputados federais; senadores; prefeituras de **19 estados** (CE + 18 SICONFI, = todo o NE, CO e N); deputados
estaduais **CE/BA/RN/MG**; **dívida das prefeituras** nos 19 estados (ficha + ranking, com filtro de ano) + painel
nacional no hub; no seletor de estado há **"Todos os municípios (só a dívida)"** = ranking nacional (`docs/todos.js`,
junta o `divida.json` dos 19); dívida pública; devedores da União; Índice de Governança (prévia). Pages ligado em todos.

## 11. Pendências e ideias → GitHub Issues

O que falta fazer e as ideias futuras ficam nas **Issues** do repositório `projetoquantocusta1-alt.github.io`.
Quando o dono apontar uma issue (ou um lote), resolver em sessão focada e **fechar a issue**.
