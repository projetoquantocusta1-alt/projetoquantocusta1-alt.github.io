# CONTEXTO DO PROJETO — leia isto primeiro

**Para que serve este arquivo:** quando uma conversa com o Claude ficar grande (cara), comece outra e peça
"leia o CONTEXTO.md do repositório projetoquantocusta1-alt.github.io". Ele tem tudo para continuar sem reler
conversas antigas. **Mantenha este arquivo atualizado** ao fim de cada mudança grande ou auditoria.

Última atualização: 2026-11-20.

---

## 1. O que é o projeto

"Quanto Custa?" — sites de transparência de gasto público, em **quantocustaum.com** (GitHub Pages). Mostra quanto
custam os políticos e para onde vai o dinheiro, com **dados oficiais, atualizados todo dia por robôs, corrigidos
pela inflação (IPCA)**. Feito pela "Sociedade do Progresso" (sem nome de autor — ver regra 5).

O dono **não é programador**: responder sempre em **português simples**. Publicar na `main` é autorizado.

## 2. Repositórios (todos em github.com/projetoquantocusta1-alt)

| Repositório | O que é | Fonte dos dados |
|---|---|---|
| `projetoquantocusta1-alt.github.io` | **Hub** (raiz do quantocustaum.com) + Índice de Governança | junta os outros sites |
| `quanto-custa-deputados` | Deputados federais | Câmara dos Deputados (dados abertos) |
| `quanto-custa-senadores` | Senadores (+ `sondar.py`/`sondagem.yml`, ver §6) | Senado Federal |
| `quanto-custa-municipios` | **Página única das prefeituras** (seletor de estado) + Ceará | TCE-CE (nota a nota) |
| `quanto-custa-municipios-ba`/`-pe`/`-pb`/`-rn` | Prefeituras por estado | **SICONFI / Tesouro Nacional** |
| `quanto-custa-deputados-estaduais` | Deputados estaduais: CE (Alece), BA (ALBA), RN (ALRN) | portais das Assembleias |
| `quanto-custa-nucleo` | núcleo comum | — |

**Endereços:** `/` (hub), `/indice/`, `/quanto-custa-deputados/`, `/quanto-custa-senadores/`,
`/quanto-custa-municipios/` (+`?uf=ba|pe|pb|rn`), `/quanto-custa-deputados-estaduais/` (+`?uf=ba|rn`).

## 3. Regras do projeto (valem para tudo; detalhe em PLANO.md)

1. **Toda limitação dos dados é explicada no site, com o motivo** (na página e na Metodologia).
2. **Divergência nos dados oficiais é sempre informada**, dizendo de quem é a responsabilidade.
3. **Não publicar número que não dá para conferir** — na dúvida, fica de fora, com aviso.
4. **CPF nunca inteiro** — sempre mascarado (`***.456.789-**`), em dados, páginas e brutos. O mascarador fica em
   `quanto-custa-nucleo/quanto_custa/privacidade.py` e tem **cópias idênticas** em `coletor/privacidade.py` de
   deputados, senadores, municipios e deputados-estaduais: **mudou um, copie para os outros quatro.**
5. **Anonimato** — nenhum nome de autor nem link pessoal ("Sociedade do Progresso" pode).
6. **robots.txt respeitado**; robôs consultam devagar (pausa entre consultas).
7. Robôs gravam como `robo-quanto-custa`; **não enviar mudanças enquanto o robô do mesmo repositório salva**.
8. **Não mudar as cores do mapa.**
9. **Buscar sempre melhorar a experiência do usuário**; layouts fluidos e estilosos, leves (mostrar o essencial,
   abrir o resto sob demanda).

## 4. Como funciona cada parte

- **Hub** (`robo/mensageiro.py` + `robo/indice.py`): lê os JSON publicados dos outros repos (via raw.githubusercontent
  ou `--local /home/user` em teste) e gera `dados/totais_hub.json`, `dados/estados.json` (mapa), `dados/busca.json`,
  `dados/indice.json`. Página: `index.html`, `hub.js`, `hub.css`; Índice em `indice/`.
- **Prefeituras — Ceará:** TCE-CE, **nota a nota** (empenhos, fornecedores, pago). App em `quanto-custa-municipios/docs/app.js`.
- **Prefeituras — BA/PE/PB/RN (SICONFI):** mesmo **código genérico**. O único que muda por estado é o bloco "ESTADO"
  em `config.py` (Python) e o bloco `CFG` no começo de `docs/uf.js`. A página única carrega `app.js` (CE) ou
  `../quanto-custa-municipios-XX/uf.js` (outros). SICONFI só tem **totais por área** (sem fornecedor, sem gabinetes).
  - Função **"Legislativa"** (somando exceto-intra + intra) = **câmara**. "DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS)" =
    gasto total da prefeitura. Conferido com o TCE-CE (Fortaleza/Sobral 2025), **centavo por centavo**.
  - SICONFI dá **liquidado**, não **pago**, por função → mostramos empenhado, liquidado e "a liquidar". Bimestral,
    prazo de 30 dias após o bimestre.
- **Deputados estaduais** (`quanto-custa-deputados-estaduais`): `docs/dados/<uf>/`; `docs/app.js` multi-estado com
  visão "Todos os estados". Coleta a **Bahia por último** (é a mais lenta). Aceita `--uf` (botão Run workflow).
  **Estado sem dados não entra no seletor.**
  - **CE (Alece):** verba VDP (CSV) + folha nominal. Desde 2023 (sistema antigo mistura aposentadorias/pensões).
  - **BA (ALBA):** verba indenizatória nota a nota (lista + detalhe; a página começa na 0). **Sem folha nominal** —
    só o subsídio de lei (R$ 34.774,64/mês).
  - **RN (ALRN):** cota parlamentar pela API `api-transparencia.al.rn.leg.br`. A API exige um **token** que o portal
    embute no código público; `coletor/alrn.py` **lê o token do próprio site a cada execução** (não guardamos no repo,
    porque o token carrega usuário/senha embutidos). Sem folha nominal. **Partido fica em branco** (a fonte só dá um
    código, não o nome do partido) — pendência menor/opcional.
- **Índice de Transparência e Governança Pública** (`/indice/`, prévia): nota 0–100 por órgão.
  - Assembleias: 8 critérios, notas e provas em `robo/indice_assembleias.json` (só a pontualidade é automática).
    Hoje com nota: Alece (77) e ALBA (77). Outras: "sem acesso" / "em avaliação".
  - Prefeituras/câmaras: 3 critérios automáticos (entrega no prazo 35, números que fecham 35, anos anteriores 30).

## 5. Regra de publicação de um estado SICONFI (importante)

Um estado entra no hub/Índice quando a **primeira coleta terminou** = `cobertura[ano-1] + faltas[ano-1] >= 0.98*total`
(NÃO é mais "90% de cobertura"). Motivo: no **RN, ~metade dos municípios realmente não envia o relatório ao Tesouro**
(confirmado testando a API: resposta vazia). Isso é o retrato real, não coleta parcial — então publicamos **"com
aviso"**: KPI "Sem relatório no Tesouro: N", nota 0 no Índice com prova, e o mapa diz "X de Y enviaram ao Tesouro"
(não "em coleta"). Os que não enviaram vão para a lista "Quem não prestou contas".

## 6. O container NÃO acessa sites do governo nem o quantocustaum.com

- **Coleta real:** só nos **runners do GitHub Actions** (os robôs). Daqui dá para disparar e ler logs com as
  ferramentas `mcp__github__*`.
- **Testar uma fonte nova (gov):** usar o workflow **`sondagem.yml` do repo senadores** (inputs: `urls` separadas por
  espaço; `cabecalhos` JSON opcional). Ele baixa URLs arbitrárias dos runners, lê xlsx/PDF/JSON como texto e **mascara
  CPF**. Resultado em `quanto-custa-senadores/dados_brutos/sondagem/`.
- **Testar o SITE:** renderizar **localmente** — servidor `python3 -m http.server`, um diretório espelho com symlinks
  (`quanto-custa-municipios` → `.../docs`, etc.), e no Playwright reescrever `https://quantocustaum.com/...` →
  `http://localhost:PORT/...`. Esconder `#bv,.bv-fundo` (modal de boas-vindas). Checar `pageerror` e `scrollWidth`.

## 7. Robôs / horários (UTC) e como rodar

- **Hub** `mensageiro.yml`: 11:47, 15:07 (`--completo`: destaques/fornecedores/CNPJ), 21:37. O passo também roda
  `robo/indice.py`. Botão "Run workflow" disponível.
- **Deputados estaduais** `atualizar.yml`: 10:41. Inputs: `forcar`, `uf` (ce/ba/rn/vazio). Ex.: rodar só o RN →
  `run_workflow` com `{"uf":"rn"}`.
- **Prefeituras** (cada `-ba/-pe/-pb/-rn`) `atualizar.yml`: de madrugada + semanal domingo (TSE/IBGE/IPCA).
- **Senadores** `sondagem.yml`: só manual (ver §6).

## 8. Convenções de trabalho (como o Claude deve agir)

- **Rodapé de commit**: usar as linhas que o lembrete da sessão indicar (`Co-Authored-By: ...` + `Claude-Session: <link>`;
  o modelo muda de uma sessão para outra).
- **Auditoria de sempre** (quando o dono pedir "rode a auditoria de sempre"): (1) robôs — últimas execuções no Actions;
  (2) testes — `python -m pytest -q` em cada repositório; (3) valores — `python robo/auditoria.py --local /home/user`
  (refaz as contas a partir dos dados dos sites, procura CPF inteiro; ERRO = corrigir, INFO = casos para olhar);
  o Mensageiro com `--local` deve reproduzir `dados/totais_hub.json` igualzinho (só muda o horário);
  (4) páginas — renderização local (§6), no computador e no celular.
- **Publicar na `main`** e force-sync da branch `claude/proposed-changes-bugs-f0f8xj`. **Não criar PR** sem pedido.
- **Não reescrever commits do robô** (`robo-quanto-custa`): aparecem como "Unverified", é normal; deixar como estão.
- **Não enviar enquanto um robô do mesmo repo está salvando** (regra 7).
- O **remote-tracking local às vezes fica desatualizado** — usar `FETCH_HEAD` após `git fetch` para ver o topo real.
- Ao mudar um arquivo servido (js/css), **subir o `?v=N`** nos HTML que o referenciam (cache).
- `git reset --hard` costuma ser bloqueado pelo modo automático — usar `git merge --ff-only FETCH_HEAD`.

## 9. Estado atual (2026-11-20, depois da auditoria)

- **No ar:** deputados federais, senadores, prefeituras **CE/BA/PE/PB/RN**, deputados estaduais **CE/BA/RN**,
  Índice de Governança (prévia). Pages ligado em todos.
- **19/11:** todos os robôs rodaram com sucesso; dados frescos; as 12 páginas principais renderizam sem erro de JS;
  fluxos (busca, abrir cidade, "mostrar mais", mapa, abas, fichas) testados e OK no computador e no celular.
- **Auditoria de 20/11** (`robo/auditoria.py`): 111 checagens, 0 erros, 30 informativos; 92 testes ok; 14 páginas
  sem erro no computador e no celular; Mensageiro reproduz os totais publicados.
  - **CPF corrigido em 20/11:** o mascarador deixava passar CPF com algo colado depois (`...-31-2`, `...-53.366...`),
    CPF sem pontuação depois da palavra "CPF" (inclusive de **menores** numa nota de banda de música, CE) e o
    "nº do documento" das notas dos deputados (não passava pelo mascarador). Mascarador novo + 12 arquivos limpos
    (só as regras novas foram aplicadas nos arquivos, para não mexer em números de processo).
- **Auditoria de valores anterior (19/11):** 73 checagens, 0 erros. Casos conhecidos que **NÃO são erro** (o dono mandou manter):
  câmara "zerada ou negativa" (já excluída da soma); "liquidado > empenhado" (restos a pagar, legítimo); custo por
  vereador alto nas capitais (câmara inteira ÷ vereadores).

## 10. Em aberto / ideias anotadas

- **Avisos pendentes (aguardando o dono, depois de explicado o impacto):** cota negativa de 4 deputados em 2013
  (devolução maior que o gasto), emenda paga > empenhada (Vinícius Gurgel 2018, restos a pagar), receitas do CE em
  que transferências + própria passam da total em 1–2% (Baixio, Brejo Santo, Catarina…; provável dedução do Fundeb),
  e trocar "(1.175 cidades)" do hub por "(1.038 de 1.175 cidades com dados de 2026)".
- **Vereadores a conferir no TSE:** número par ou acima do limite constitucional (Aracati 16, Cascavel 10,
  Arcoverde 10, Parnamirim 18, Boa Nova…); a auditoria lista todos em INFO. Afeta o custo por vereador.
- 17 cidades SICONFI não estão nem na cobertura nem em "faltas" do ano (3 BA, 5 PE, 4 PB, 5 RN).

- **Partido em branco** nos deputados estaduais do RN (a fonte só dá código) — opcional preencher.
- **TCM-BA** não responde aos runners → BA/PE/PB/RN ficam sem nota a nota (só SICONFI). Testar os TCEs desses estados
  no futuro (daí entram fornecedores e gabinetes).
- **Assembleias ainda sem robô:** **Paraíba (ALPB)** — site responde de forma intermitente; quando pegar no ar,
  montar o robô (tem planilhas mensais parecidas com a do Ceará). **Pernambuco (ALEPE)** — não respondeu ao robô.
- **Ideia: "Shows e eventos (cultura)"** — mostrar gasto com shows (quem, onde, valor, data). Só é possível **onde há
  nota a nota** (hoje, **Ceará**). Cuidados: muitas vezes o pagamento é a uma **produtora**, não ao artista; mostrar a
  descrição oficial e o link, sem afirmar superfaturamento. BA/PE/PB/RN só com o TCE de cada estado.
- **Índice de Governança** (prévia já publicada): avaliar mais Assembleias, avaliar portais de transparência
  municipais, guardar o histórico das notas.
- Pendência antiga (CE prefeituras): gabinete do prefeito, população, fornecedores (itens "A3/A6/A8").

## 11. Histórico recente (resumo)

- **17/11:** og.png novo; Índice de Governança (prévia) publicado; lista "Quem não prestou contas" com abas por estado
  e botão "mostrar mais"; Pernambuco e Paraíba (prefeituras) entram; código das prefeituras virou genérico por estado.
- **18/11:** Rio Grande do Norte — deputados estaduais (ALRN, token lido do site) e prefeituras (SICONFI) publicados;
  regra passou de "90%" para "primeira coleta terminou"; Bahia passa a coletar por último; PE corrigido para 184
  municípios; rodapé do Índice sem fonte repetida.
- **19–20/11:** auditoria geral (valores 0 erros; layout e fluxos OK); criado este CONTEXTO.md.
- **20/11 (tarde):** nova auditoria guardada em `robo/auditoria.py`; correção do CPF (ver §9); design: no hub, o texto
  longo das câmaras foi para "Como calculamos ▾"; nas prefeituras BA/PE/PB/RN o aviso do SICONFI virou uma linha que
  abre ao tocar.
