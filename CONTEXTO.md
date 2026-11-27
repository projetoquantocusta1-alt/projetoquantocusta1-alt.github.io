# CONTEXTO DO PROJETO — leia isto primeiro

**Para que serve este arquivo:** quando uma conversa com o Claude ficar grande (cara), comece outra e peça
"leia o CONTEXTO.md do repositório projetoquantocusta1-alt.github.io". Ele tem tudo para continuar sem reler
conversas antigas. **REGRA: toda e qualquer mudança (código, dados, layout, regra, auditoria) é registrada aqui**, no histórico (§11), no mesmo passo em que é publicada no GitHub. Sem exceção.

Última atualização: 2026-11-26.

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
| `quanto-custa-municipios-ba`/`-pe`/`-pb`/`-rn`/`-ma`/`-pi`/`-al`/`-se` | Prefeituras por estado (Nordeste completo) | **SICONFI / Tesouro Nacional** |
| `quanto-custa-deputados-estaduais` | Deputados estaduais: CE (Alece), BA (ALBA), RN (ALRN) | portais das Assembleias |
| `quanto-custa-divida` | **Dívida pública** (dívida, juros, vencimentos, previsão, bancos) | **Banco Central** (SGS, Demab, Focus, IF.data) |
| `quanto-custa-devedores` | **Devedores da União** (Dívida Ativa: empresas, estados, tipos, situação) | **PGFN** (dados abertos, trimestral) |
| `quanto-custa-nucleo` | núcleo comum | — |

**Endereços:** `/` (hub), `/indice/`, `/quanto-custa-deputados/`, `/quanto-custa-senadores/`,
`/quanto-custa-municipios/` (+`?uf=ba|pe|pb|rn`), `/quanto-custa-deputados-estaduais/` (+`?uf=ba|rn`), `/quanto-custa-divida/`, `/quanto-custa-devedores/`.

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
- **Prefeituras — BA/PE/PB/RN/MA/PI/AL/SE (SICONFI):** mesmo **código genérico** (todo o Nordeste). O único que muda por estado é o bloco "ESTADO"
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
- **Devedores** `atualizar.yml`: segunda 14:41 (só refaz quando a PGFN publica trimestre novo; input `forcar=sim`). Leva ~20 min (10 GB).
- **Dívida pública** `atualizar.yml`: 13:17 (todo dia; o Banco Central atualiza as séries uma vez por mês e o IF.data a cada trimestre).

## 8. Convenções de trabalho (como o Claude deve agir)

- **Registrar toda mudança no CONTEXTO.md** (§11), junto com o commit que a publica — é regra do dono.

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

## 9. Estado atual (2026-11-26, depois da auditoria das 2h)

- **Auditoria de 26/11 (2h de Brasília, agendada pelo dono):** robôs ok (Mensageiro 22:27 UTC ok; prefeituras AL/PI já de 26/11,
  as outras rodam de madrugada); 120 testes ok; `robo/auditoria.py` 111 ok / 0 erros / 30 informativos; 20 páginas sem erro de JS
  nem rolagem lateral (computador e celular). Correções nos deputados estaduais: ver §11 (26/11).

- **Auditoria de 25/11:** robôs ok (deputados, senadores, municípios CE + 8 estados e estaduais gravaram em 25/11; dívida e
  devedores em 24/11, como previsto); 114 testes ok; `robo/auditoria.py` com os dados de hoje: 111 ok / 0 erros / 30 informativos
  (os 2 "erros" da primeira passada eram só o hub de ontem 22h vs. dados novos da manhã; o Mensageiro das 11:47 resolve); nenhum
  CPF inteiro; 20 páginas sem erro de JS e sem rolagem lateral no computador e no celular. Achados e correções: ver §11 (25/11).

- **No ar:** deputados federais, senadores, prefeituras de **todo o Nordeste (9: CE, BA, PE, PB, RN, MA, PI, AL, SE)**, deputados estaduais **CE/BA/RN**,
  Índice de Governança (prévia). Pages ligado em todos.
- **19/11:** todos os robôs rodaram com sucesso; dados frescos; as 12 páginas principais renderizam sem erro de JS;
  fluxos (busca, abrir cidade, "mostrar mais", mapa, abas, fichas) testados e OK no computador e no celular.
- **Auditoria de 21/11:** robôs ok (todos gravaram em 21/11, já com o mascarador novo); 103 testes ok; Mensageiro
  reproduz os totais; `robo/auditoria.py` 111 ok / 0 erros / 30 informativos; nenhum CPF inteiro; mapa = totais
  (deputados e senadores somam igual ao hub); IPCA com a mesma referência (10/2026) em todos os sites; 14 páginas sem
  erro (computador e celular); cidades de cada estado abrem certo; 29 links internos do hub sem quebra.
  Achados novos: **busca do hub só tem o Ceará** e **sitemap sem os deputados estaduais** (ver §10).
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
- **Busca do hub só conhece o Ceará** (`dados/busca.json`: 184 cidades, prefeitos e vereadores só do CE). "Recife",
  "Mossoró" etc. dão "Nada encontrado"; deputados estaduais também não entram. Falta incluir cidades de BA/PE/PB/RN
  (link `?uf=xx#municipio/<ibge>`) e os deputados estaduais (CE/BA/RN) no Mensageiro.
- **sitemap.xml** não tem `/quanto-custa-deputados-estaduais/`.

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

- **26/11 (auditoria das 2h):** **deputados estaduais, "Todos os estados": o contador em tempo real começava em 1º/out para os 3
  estados** (usava o mês do estado mais atrasado, o RN, com dados só até set), embora CE (folha até out) e BA (até nov) já tivessem
  publicado mais meses → mostrava ~R$ 86,7 mi, uns R$ 3,6 mi a mais que a soma dos três estados. Agora cada estado corre a partir
  do mês seguinte à última folha DELE (`ult_por_uf` na junção dos resumos) e o "Todos" = CE + BA + RN (R$ 83,1 mi às 2h). A nota
  diz "dados até Nov/2026 (Rio Grande do Norte: até Set/2026)". Também: campo de busca "Nome do deputado" (cortava no celular) e
  aviso "dados sendo coletados" com cantos normais no celular (era uma pílula de 4 linhas). `app.js?v=14`, `estaduais.css?v=5`.
- **26/11 (manhã, pedido do dono): hub inteiro em "valores de hoje" no ano em andamento.** Antes, os valores de 2026 do hub
  (contadores, cartão das câmaras, gabinetes, cota dos senadores, mapa e painel do estado) eram os da época, enquanto as barras e os
  sites mostram em valores de hoje (ex.: gabinetes do CE R$ 653 mi no hub x R$ 662,1 mi na página do CE). Agora o Mensageiro grava
  `fator_ano` (o `fator_ipca` do resumo do ano dos deputados, IPCA até 10/2026) em `totais_hub.json` (e `fator_ipca` na esfera dos
  deputados) e o `hub.js` multiplica na hora de mostrar (`hoje()`; sem o campo, usa total corrigido ÷ total da época). **Os números
  gravados nos JSON continuam da época** → `robo/auditoria.py` não mudou (111 ok). Cartão e mapa continuam batendo entre si (os dois
  corrigidos). O mapa só muda de escala, não de cores. Site dos deputados: o contador "Só em 2026" (e por segundo, por dia, previsão)
  também passou para valores de hoje (`app.js?v=27`), como o resto da página. Conferido: Congresso no hub = deputados + senadores
  dos sites. `hub.js?v=30`.

- **25/11 (auditoria de sempre + experiência do usuário):** (1) **Dívida pública: "Valores de hoje" corrigia só até set/2026**
  (os outros sites usam 10/2026): a tabela mensal termina no último mês da dívida, e o IPCA de outubro ficava de fora. O robô
  agora grava `mensal.ipca_extra` (IPCA dos meses depois do último dado da dívida) e o `app.js` usa esses meses na correção
  (`app.js?v=4`). Passa a valer na próxima rodada do robô (13:17 UTC). (2) **Topo de Deputados e Senadores: "Dados atualizados
  em 25/11/202…" saía cortado** no computador (1366 px). O texto agora quebra em duas linhas curtas à direita (`tema.css`,
  idêntico em deputados, senadores, estaduais, dívida e devedores; `?v` subidos); senadores e estaduais sem os segundos na hora.
  (3) **Deputados: dois números diferentes para "2026" lado a lado** (contador R$ 1,05 bi — estimativa em tempo real — e
  "Custo total R$ 991,91 mi"): os quadros agora dizem "registrado em 2026 até out" (custo, por cadeira e cota; `app.js?v=26`).
  (4) **Hub: cartões de Deputados e Senadores mostravam o valor de 2026 sem correção** (R$ 979 mi e R$ 66,6 mi) enquanto a barra
  do mesmo cartão e os sites mostram em valores de hoje (R$ 992 mi e R$ 67,5 mi). O cartão passou a usar o valor da barra
  (`hub.js?v=29`; o Mensageiro não mudou; o cartão das prefeituras continua igual ao mapa, de propósito). (5) Senadores: "R$ 84,48 mi"
  da previsão não se parte mais em duas linhas.
  **Conferido no fim do dia (25/11):** o robô da dívida rodou às 14:28 UTC (agendamento do GitHub atrasou ~1h10) e gravou
  `ipca_extra` = out/2026 (0,14%); a página mostra "IPCA até out/2026". Rodada manual às 19:45 ok (sem mudança). Auditoria de
  novo: 111 ok / 0 erros; 20 páginas sem erro (computador e celular). Obs.: a Selic meta do BC falhou na coleta e o robô
  manteve o valor anterior (13,75%), como previsto no código.

- **24/11 (madrugada, experiência do usuário — parte 2, pedida pelo dono):** a parte 1 (abaixo) foi **publicada na `main`** dos 15
  repositórios do site (o `quanto-custa-educacao` não tem `main`; ficou só na branch de trabalho). Depois: (1) **barrinhas dos
  cartões do hub** mostram o primeiro e o último ano embaixo; tocar (ou passar o mouse) numa barra mostra "ano: valor" (antes só
  havia `title`, que não funciona no celular). (2) **"5 maiores notas"**: o texto "descrição — fornecedor" (gerado em
  `robo/destaques.py`) é separado no navegador (`notaTxt` no `hub.js`): fornecedor em negrito, descrição embaixo, menor e sem caixa
  alta. O robô não mudou. (3) **Índice, Sobre e Privacidade ganharam o mesmo menu do hub** (☰ no celular, "Políticos ▾", "Dívidas ▾",
  Índice, Sobre, Privacidade; página atual sublinhada). Novo arquivo **`menu.js`** na raiz: monta o menu nas páginas com
  `<nav id="menu" data-auto>` e cuida do ☰ e dos submenus **também no hub** (essa parte saiu do `hub.js`). **Mudou um link do
  menu? Mudar no `index.html` do hub E no `menu.js`.** Essas páginas passaram de `hub.css?v=13` para `?v=18` (o 404 também).
  (4) Menu: "Deputados estaduais — por enquanto, Ceará, Bahia e Rio Grande do Norte" (dizia só CE e BA). (5) **Sobre**: a frase do que o
  site cobre dizia "só o Ceará"; agora lista tudo (federais, senadores, estaduais CE/BA/RN, prefeituras dos 9 estados, dívida,
  devedores), e as fontes incluem Tesouro (SICONFI), Assembleias e PGFN. Versões: `hub.css?v=18`, `hub.js?v=28`, `menu.js?v=1`.
- **24/11 (madrugada, experiência do usuário):** revisão das páginas no computador e no celular (renderização local, sem erros de JS
  nem rolagem lateral). Correções: (1) **"Projeto Quanto Custa" ainda aparecia nos sites** (rodapé, boas-vindas, contador de visitas,
  selo "PROJETO QUANTO CUSTA · BAHIA" dos 8 estados SICONFI, compartilhamento de cartão) — trocado por "Quanto Custa" em deputados,
  senadores, municípios (CE + 8 estados), deputados estaduais, núcleo e educação; `?v` subidos. (2) Hub: **"Como calculamos" ficou
  recolhível** (abre ao tocar, e sozinho quando se chega por `#metodo` / menu "Metodologia") e foi **atualizado**: falava só do Ceará;
  agora explica as câmaras dos 8 estados do SICONFI, que o painel do mapa mostra câmaras nos 9 estados, e por que o contador das
  câmaras (pago/liquidado) pode ficar um pouco abaixo do "registrado" dos cartões (ex.: 7,76 bi x 7,79 bi). Mesma explicação curta
  embaixo do contador. (3) Hub no celular: "Quem não prestou contas" e "5 maiores notas" sem coluna apertada (etiqueta em cima, nomes
  na largura toda; valor abaixo do texto); página inicial ~15% mais curta. (4) Cartões do rodapé do hub com seta (indicam que são
  links). (5) Busca dos deputados: texto do campo "Nome do deputado" (antes cortava no celular).
- **24/11 (noite, cruzamento):** aba **"Recebem dinheiro público"** na página dos devedores + quadro "Recebe dinheiro público?"
  na ficha de cada empresa (ideia do dono). O robô dos devedores passou a rodar **toda semana** completo (PGFN ~20 min + cruzamento):
  baixa por *sparse checkout* os fornecedores dos outros sites (deputados `docs/dados/*/fornecedores/`, senadores
  `*/fornecedores.json`, estaduais `*/*/fornecedores.json`, municípios CE `docs/dados/f/`) e o zip de emendas do Portal da
  Transparência (`EmendasParlamentares_PorFavorecido.csv`: CNPJ de quem recebeu, autor, mês, valor). Junta pela **raiz do CNPJ**
  com TODOS os devedores da PGFN (não só os maiores). Fora do cruzamento: **órgãos e entes públicos** (prefeituras, estados,
  fundos, INSS — regex `PUBLICO` em `coletor/cruzamento.py`) e, nas emendas, naturezas jurídicas públicas/economia mista (o
  **Banco do Brasil e a Caixa só repassam** as emendas como agentes; sem o filtro, o BB aparecia com R$ 94 bi). Prefeituras do CE:
  quem pagou = a prefeitura da pasta (não a cidade do fornecedor). Valores recebidos = da época, todos os anos de cada fonte.
  Saída: `cruzamento.json` (as 2.500 maiores dívidas + as 2.500 que mais receberam) e `cruz/XX.json` (detalhe de todas, por raiz).
  Texto sempre diz que **não indica irregularidade** (certidão positiva com efeito de negativa para parcelada/garantida/suspensa).
  Resultado (3º tri/2026): **63.967** empresas devedoras recebem dinheiro público; devem R$ 510 bi (R$ 114 bi em cobrança) e
  receberam R$ 86,8 bi (emendas R$ 17,3 bi, 11.904 empresas; prefeituras CE R$ 67,4 bi; cota deputados R$ 1,8 bi; senadores R$ 174 mi;
  estaduais R$ 70 mi). `totais.emendas_por_natureza` no `cruzamento.json` mostra o que foi filtrado.
  **Próximo passo combinado:** aviso "deve R$ X à União" na ficha de fornecedor dos sites de deputados e senadores; depois, contratos federais.
- **24/11 (noite, depois):** **nova página "Devedores da União"** (`quanto-custa-devedores`, `/quanto-custa-devedores/`), mesmo
  visual. Fonte: dados abertos da **PGFN** (`dadosabertos.pgfn.gov.br/<AAAA>_trimestre_<NN>/`: `Dados_abertos_Sistema_SIDA.zip`
  1,4 GB, `Previdenciario.zip`, `FGTS.zip`; ~10 GB de CSV, 53,6 milhões de linhas; ";" latin-1). **Regras:** soma só
  `TIPO_DEVEDOR=PRINCIPAL` (corresponsáveis repetem o valor da mesma inscrição); empresas pela **raiz do CNPJ** (matriz+filiais);
  **pessoas físicas só nos totais** (decisão do dono, LGPD); CPF já vem mascarado; nome de MEI passa pelo mascarador. Situação
  agrupada: Em cobrança / Parcelada ou negociada (Benefício Fiscal, Em negociação) / Garantia / Suspensa por decisão judicial. Não há
  município nos arquivos (só UF) → sem ranking por cidade. Números do 3º tri/2026: total **R$ 3,57 tri** (36,3 mi inscrições), empresas
  R$ 3,38 tri, PF R$ 190 bi, em cobrança R$ 2,29 tri, 7,04 mi empresas devedoras; maior: Petrobras R$ 90,2 bi. Arquivos: `resumo.json`
  (5 KB gz, inclui os 10 maiores), `empresas.json` (3.000 maiores, só abre na aba Empresas), `estados.json` (60 maiores por UF).
  Hub: as abas "Dívida pública" e "Devedores da União" foram juntas no submenu **"Dívidas"** (`#sub-div`). **Pendente do dono:**
  ligar o GitHub Pages do repositório novo (branch `main`, pasta `/docs`). **Ideia para depois:** setor de cada empresa (CNAE) com o
  cadastro da Receita, como já é feito nos fornecedores dos deputados.
- **24/11 (noite):** página da dívida posta **no padrão visual dos outros sites** (pedido do dono): menu com 7 itens e grupo
  "A dívida ▾" (Composição, Vencimentos, Previsão), como os grupos dos deputados; "Dados atualizados em …" curto; topo com os
  quadrinhos `.contador-linha` (juros em 12 meses, por segundo, por dia, quanto a dívida cresce por dia), como nos deputados; 4
  indicadores no início; "O que dava pra fazer?" com cartões de números grandes abreviados (ex.: "129,2 mi"). A pedido do dono,
  voltou o 5º cartão "R$ X para cada brasileiro" (juros de 12 meses ÷ população).
- **24/11 (fim da tarde):** menu do hub: **Deputados (federais/estaduais), Senadores e Prefeitos e vereadores viraram uma só aba,
  "Políticos"** (submenu `#sub-pol`, mesmo funcionamento do antigo "Deputados"; no celular aparece o rótulo "POLÍTICOS" com os 4 itens).
  O menu voltou a caber em uma linha no computador. `hub.css`/`hub.js` com `?v` novo.
- **24/11 (tarde):** **nova página "Quanto Custa a Dívida Pública"** (`quanto-custa-divida`, endereço `/quanto-custa-divida/`), no mesmo
  visual dos outros sites. Robô `atualizar.py` (diário, 13:17 UTC) gera `docs/dados/divida.json` (~100 KB), `bancos.json` (~250 KB, só
  abre na aba Bancos) e `meta.json`. Fontes, todas do **Banco Central**: séries do SGS (dívida bruta 13761/13762, dívida líquida
  4478/4513 e por esfera, juros nominais 4616 e por esfera, primário 4649, nominal 4583, PIB 12 meses 4382, Selic 4189/432, IPCA 433,
  dívida mobiliária 4151/4152/4154, prazo médio 10618, indexadores 4173–4180/12001), cronograma de vencimentos (Demab), Focus e
  IF.data (balanço de cada banco/financeira). Abas: Início (dívida "agora" em tempo real = último dado oficial + ritmo médio de 12
  meses, marcado como estimativa; juros por segundo), Evolução, Juros, Composição, Vencimentos, Previsão (projeção simples com faixa
  de 90% + Focus), Bancos, O que dava pra fazer (juros de 12 meses) e Metodologia. **Decisão do dono:** "ranking com aviso" — não
  existe dado público de quanto o governo deve a cada empresa (sigilo bancário; o Tesouro só publica por grupo de detentor e o
  **Tesouro Transparente recusa os robôs**, inclusive os do GitHub). O ranking usa a carteira de títulos e valores mobiliários do
  IF.data (inclui títulos privados → é um teto), a renda com títulos declarada (12 meses = 2 semestres; o IF.data acumula jan–jun e
  jul–dez, e mar/set são só do trimestre) e uma coluna de juros estimados (carteira × custo médio da dívida), sempre marcada.
  IF.data vem em **reais** (não em mil). IBGE (população) não respondeu ao robô → usa a estimativa oficial de 1º/7/2025.
  Hub: link "Dívida pública" no menu e no sitemap. GitHub Pages ligado pelo dono (branch `main`, pasta `/docs`); página no ar,
  conferida pelos runners em 24/11.
- **17/11:** og.png novo; Índice de Governança (prévia) publicado; lista "Quem não prestou contas" com abas por estado
  e botão "mostrar mais"; Pernambuco e Paraíba (prefeituras) entram; código das prefeituras virou genérico por estado.
- **18/11:** Rio Grande do Norte — deputados estaduais (ALRN, token lido do site) e prefeituras (SICONFI) publicados;
  regra passou de "90%" para "primeira coleta terminou"; Bahia passa a coletar por último; PE corrigido para 184
  municípios; rodapé do Índice sem fonte repetida.
- **19–20/11:** auditoria geral (valores 0 erros; layout e fluxos OK); criado este CONTEXTO.md.
- **22/11:** **Nordeste fechado nas prefeituras** — MA, PI, AL, SE entram (SICONFI). A validação do hub (salto
  ano-a-ano) passou a **pular os estados do SICONFI** (o conjunto de cidades que presta contas muda a cada ano).
  Auditoria: 102 checagens, 0 erros. SE tem 75/75; MA/PI/RN têm muitos que não prestam contas (publicado "com aviso").
- **20/11 (tarde):** nova auditoria guardada em `robo/auditoria.py`; correção do CPF (ver §9); design: no hub, o texto
  longo das câmaras foi para "Como calculamos ▾"; nas prefeituras BA/PE/PB/RN o aviso do SICONFI virou uma linha que
  abre ao tocar.
- **23/11:** conferido que o bug da validação "coleta incompleta" só afetou o **Maranhão** — nos outros 7 estados do
  SICONFI (BA, PE, PB, RN, PI, AL, SE) o salto ano-a-ano das câmaras nunca passou do limite antigo, então nunca foram
  barrados nem ficaram com número velho. Correção (pular SICONFI na validação) cobre todos daqui para frente.
- **23/11 (tarde):** cartão "Prefeitos e vereadores" do hub ficou mais limpo — removida a lista por estado (nomes +
  valores) e os 9 quadros "por vereador" por estado; ficam o total, a etiqueta "N estados", UM quadro com a média por
  vereador dos estados e o aviso do SICONFI (mantido). Detalhe por estado continua na página das cidades (hub.js).
- **24/11 (noite):** **SEO + marca.** Tirado "Projeto" do título de TODAS as abas (hub: "Quanto Custa — quanto
  custam os políticos do Brasil"; cada site "<descrição> — Quanto Custa", no HTML e no `document.title` do `uf.js`
  dos 8 estados do SICONFI). Adicionados **dados estruturados schema.org** no hub (Organization, WebSite e
  **Dataset** com o DOI e a licença CC BY — ajuda a aparecer no Google e na Busca de Conjuntos de Dados),
  `canonical` e og/twitter. `sitemap.xml` passou a incluir os deputados estaduais. **Pendência do dono (off-page):**
  cadastrar o site no **Google Search Console** e enviar o sitemap (maior impacto para aparecer nas buscas). Também tirado "Projeto" do contador de visitas ("visitas ao Quanto Custa").
- **24/11 (noite, depois):** **o nome passou a ser "Quanto Custa" em TUDO** (decisão do dono: "quero deixar tudo
  Quanto Custa"). Tirado "Projeto" também do rodapé de todas as páginas, da página Sobre, da Privacidade, do 404, do
  JSON-LD (removido o `alternateName`), do texto de fontes do Índice, do `README`, dos comentários do `hub.js`/`hub.css`
  e — o mais importante — da **citação acadêmica e dos metadados do release**: `CITATION.cff` (title "Quanto Custa"),
  `.zenodo.json` (title e descrição/ABNT), `LICENCA-DADOS.md`, `LICENSE` (copyright "Sociedade do Progresso — Quanto
  Custa") e a seção "Como citar" do Sobre. **A autoria continua "Sociedade do Progresso".** Não existe mais o nome
  "Projeto Quanto Custa" em lugar nenhum — é só "Quanto Custa". **Release `v1.2` publicada em 24/11** (o dono publicou),
  então o Zenodo relê o `.zenodo.json` e a ficha passa a mostrar "Quanto Custa"; o concept DOI 10.5281/zenodo.24486227
  não muda. Release: https://github.com/projetoquantocusta1-alt/projetoquantocusta1-alt.github.io/releases/tag/v1.2
- **24/11:** projeto virou **aberto + acadêmico de forma explícita**. Licenças: **código MIT** (arquivo `LICENSE`),
  **dados CC BY 4.0** (`LICENCA-DADOS.md`). Adicionados `CITATION.cff` e uma seção **"Como citar"** na página Sobre
  (ABNT + curta, com data de acesso). **DOI gerado (Zenodo): 10.5281/zenodo.24486227** (https://doi.org/10.5281/zenodo.24486227), release v1.0 do hub; já preenchido no `CITATION.cff`, na seção "Como citar" e no `LICENCA-DADOS.md`. Adicionado `.zenodo.json` (título, descrição, palavras-chave, licença) para a ficha do Zenodo ficar completa; **a ficha só se atualiza numa NOVA release** (o Zenodo lê o arquivo na hora da release). Concept DOI não muda; o site usa o concept DOI. Pendência: o arquivo `LICENSE` (MIT) ainda só está no hub; propagar aos outros repositórios.
- **26/11:** o dono trouxe um **relatório de análise em PDF** (feito por outra IA) sugerindo uma **seção de "dívida
  pública"** e melhorias de UX, com nota preliminar 88/100. **Conclusão (avaliada e descartada pelo dono):** o
  relatório foi escrito **sem abrir a versão atual do site** (ele mesmo admite que "o acesso automatizado não
  carregou"); a **seção de dívida pública NÃO existe** no projeto — conferido no código de todos os repositórios, as
  únicas menções a "dívida"/"Tesouro" são notas fiscais e o SICONFI municipal. Os indicadores citados (DBGG, DLSP,
  juros nominais, amortização) **existem de verdade** (séries do Tesouro Nacional e do Banco Central), mas entrar em
  dívida pública **mudaria o foco do projeto** (de "custo dos políticos" para macroeconomia) e aumentaria o custo de
  manutenção. Montei só um **PNG de rascunho** de como ficaria (nada mexido no site). **O dono não quis seguir com
  nenhuma das ideias** — foi só para ouvir minha opinião. Nenhuma mudança de código feita.
- **26/11 — IDEIA FUTURA (não fazer agora):** tornar o **Índice de Transparência e Governança Pública** mais
  **acadêmico/rigoroso**. Motivação: o dono vai estudar mais sobre índices de governança pública e recebeu um
  **excelente feedback de um doutor**; quer aprimorar essa parte aos poucos, com foco acadêmico. Direções conversadas
  (para quando o dono quiser): (1) ancorar a metodologia em referências/frameworks existentes (ex.: Escala Brasil
  Transparente da CGU, Open Budget Index, Worldwide Governance Indicators); (2) deixar explícito o **construto** medido
  e separar bem **transparência** de **governança** (são conceitos diferentes); (3) justificar pesos e método de
  agregação, tratar dados faltantes, e fazer **análise de sensibilidade** (o ranking muda muito se os pesos mudam?);
  (4) **nota metodológica/apêndice técnico** versionado, com limitações explícitas ("o que o índice NÃO mede"); (5)
  validação externa (já feito no Ceará conferindo com o TCE-CE centavo a centavo). **Status: só conversa; o dono pediu
  para não implementar nada ainda.**
- **26/11 — EXPANSÃO (Centro-Oeste + Norte, em andamento):** decisão do dono de **crescer a cobertura primeiro**
  (largura antes de profundidade). Criados e populados **10 novos repositórios** de municípios pelo SICONFI, no mesmo
  molde dos do Nordeste (só muda o bloco ESTADO do `config.py` e o CFG do `docs/uf.js`; já com a marca "Quanto Custa"):
  **Centro-Oeste** `quanto-custa-municipios-go` (GO, IBGE 52, 246 mun., TCM-GO), `-mt` (MT, 51, 141, TCE-MT),
  `-ms` (MS, 50, 79, TCE-MS); **Norte** `-ac` (AC, 12, 22, TCE-AC), `-am` (AM, 13, 62, TCE-AM), `-ap` (AP, 16, 16,
  TCE-AP), `-pa` (PA, 15, 144, TCM-PA), `-ro` (RO, 11, 52, TCE-RO), `-rr` (RR, 14, 15, TCE-RR), `-to` (TO, 17, 139,
  TCE-TO). Push feito no `main` de cada um; **primeira coleta disparada** (`atualizar.yml` com `semanal=sim`) nos
  servidores do GitHub (testes passaram; coletando). **Pendente do dono:** ligar o **Pages** (main /docs) nos 10.
  **Pendente meu (quando os dados chegarem e o Pages estiver ligado):** registrar os 10 no seletor da página única
  dos municípios (`quanto-custa-municipios/docs/index.html`: `#f-uf` + `ESTADOS`), no hub (`robo/mensageiro.py`
  SICONFI/CHAVES_MUN e `hub.js` UF_NOME/UF_DO/UF_EM) e fazer a auditoria. Depois: Sul; por fim Sudeste (SP/MG grandes).
- **26/11 — cor:** o **vermelho dos indicadores** (números grandes das homes, deltas, etc.) passou do vermelho suave
  **`#C84C4C`** para o vermelho sangue **`#c4161c`** (o mesmo já usado nos cartões compartilháveis — agora unificado),
  a pedido do dono ("vermelho sangue, mais chamativo"). Trocado em 7 repositórios (hub `hub.css`/`hub.js`/`indice`,
  `quanto-custa-nucleo/web/tema.css` e os `tema.css`/CSS de deputados, senadores, municípios e estaduais). Subidas as
  versões de cache (`?v=`) dos CSS/JS alterados em todos os sites, para o navegador pegar o novo visual (era por isso
  que o layout parecia "desatualizado" — cache antigo).
- **26/11 — Centro-Oeste + Norte NO AR:** os 10 estados terminaram a 1ª coleta e foram **registrados e publicados**.
  Feito: `SICONFI` do `robo/mensageiro.py` + mapas `UF_NOME/UF_DO/UF_EM` do `hub.js` (os 10 adicionados); seletor
  `#f-uf` e mapa `ESTADOS` de `quanto-custa-municipios/docs/index.html` (uf.js?v=1 para cada); textos fixos do hub
  index.html atualizados de "9 estados do Nordeste" para **19 estados** (Nordeste+Norte+Centro-Oeste), subtítulo do
  menu "prefeituras e câmaras de 19 estados". Mensageiro rodado localmente (lê raw.githubusercontent): os 10 entraram
  com status "ok" e valores reais; `totais_hub.json`/`estados.json` commitados. hub.js?v=32. Push hub+municipios
  (main+dev). **Auditoria dos 10: limpa** — 0 câmara negativa sem aviso, 0 câmara>gasto_total; R$/vereador altos só
  em cidades ricas reais (Canaã dos Carajás e Parauapebas/PA, Rio Verde e Senador Canedo/GO, Rondonópolis/MT). 
  **Cobertura 2025 varia muito** (adesão ao SICONFI): alta em AC 100%, PA 97%, GO 96%, AP 94%, RR 87%; baixa em
  MT 56%, AM 55%, TO 50%, RO 44%, **MS 14%** — muitas prefeituras ainda não enviaram o RREO de 2025 ao Tesouro (como
  no RN); o robô diário continua preenchendo e o site mostra "sem relatório" para as que faltam. Total agora: 19
  estados nas prefeituras (CE nota-a-nota + 18 SICONFI). Próximo: Sul; por fim Sudeste.
- **26/11 — auditoria + clareza no cartão das prefeituras:** o dono viu "valores que não batem". Auditoria: **não é
  erro nem bug** — o hub mostra o gasto das câmaras em 3 réguas (contador = pago/liquidado + projeção até o fim do ano;
  cartão = empenhado corrigido pelo IPCA; mapa = empenhado por estado), e isso já existia nos estados antigos. Para
  esclarecer, a pedido do dono, o **cartão "Prefeitos e vereadores"** passou a dizer **"empenhado"** no rótulo e ganhou
  uma linha informativa: **"dos quais R$ X já foram pagos (Ceará) ou liquidados (demais estados)"** (`pagoLiq` =
  `hoje(pago_ano CE + Σ liquidado_ano SICONFI)`; `hub.js`/`hub.css`, classe `.valor-sub`). Ex. atual: empenhado
  R$ 11,55 bi, dos quais R$ 9,02 bi pagos/liquidados. hub.js?v=33, hub.css?v=20. Nenhum valor de dado foi alterado.
- **26/11 — linguagem simples (início):** decisão do dono de deixar o site explicativo, que "qualquer pessoa entenda",
  guardando os termos técnicos/jargão para o **modo acadêmico** (futuro). Primeira reescrita, no cartão das prefeituras
  (hub.js, hub.js?v=34): o rótulo do valor virou "o que as câmaras municipais separaram para gastar em {ano}, já
  corrigido pela inflação" (era "empenhado... valores de hoje") e o informativo virou "desse valor, R$ X já saíram de
  fato dos cofres" (era "pagos/liquidados"). **Regra combinada:** frase simples na frente; termo técnico só como apoio
  (ideia: tracinho pontilhado com mini-glossário) ou no modo acadêmico. **Pendente (quando o dono aprovar o tom):**
  estender para o aviso do SICONFI e o quadro "por vereador" do mesmo cartão, depois contadores e demais cartões
  (deputados: cota/subsídio; prefeituras: SICONFI/RREO/função Legislativa; "valores de hoje (IPCA)").
  **Dono aprovou o tom ("ótimo, pode alterar tudo").** **FEITO na home (hub.js?v=35):** reescritos — as duas notas dos
  contadores (estimativa/ritmo; "já saiu dos cofres" × "só reservado no orçamento"), o aviso do SICONFI, os rótulos
  "por vereador" e "gabinetes", o resumo "câmaras inteiras" e o "lado a lado" (saiu "IPCA", "empenhado", "liquidado",
  "pago", "SICONFI", "valores de hoje"). **Pendente (sweep nos outros repositórios, mesma receita):** cartões/páginas de
  **deputados** (cota parlamentar, CEAPS, subsídio) e **senadores**; páginas por estado das **prefeituras** (uf.js:
  empenhado/liquidado/função Legislativa/RREO/SICONFI); **metodologias**; **deputados estaduais**. Regra: frase simples
  na frente, termo técnico só no modo acadêmico.
  **HOME 100% revisada (hub.js?v=36):** além dos contadores/cartão, reescrita a seção "Como calculamos" inteira
  (CEAP/CEAPS→"cota parlamentar"; "empenhado menos anulações"→"o gasto"; "balancete"→"prestação de contas/balanço";
  "função Legislativa (SICONFI)"→"a parte da prefeitura gasta com a câmara"; "IPCA/valores de hoje"→"corrigido pela
  inflação"; pago/liquidado/registrado→"já saiu dos cofres"/"só reservado no orçamento") e os rótulos do painel do
  mapa, das pendências ("Não enviaram as contas") e do aviso de divergência. TCE-CE e CNPJ ficam (definidos/comuns).
- **26/11 — revisão de segurança (a pedido do dono).** Estrutura: site estático (GitHub Pages), sem servidor, sem
  banco, sem login → ninguém altera o site sem acesso de escrita ao GitHub; o risco real de "tomada" é a conta do
  GitHub/DNS (recomendado 2FA), não o código. **Achado e CORRIGIDO: XSS armazenado** — os rótulos de KPI/destaque
  (rot/obs) iam para innerHTML sem `esc()`, e nomes de fornecedor (dado externo) chegavam neles; um nome com HTML
  malicioso rodaria script no navegador do visitante. Escapado no sink `kpis()`/`k()` de deputados (app.js?v=28),
  senadores (v=13), municípios (v=14) e estaduais (v=15); rótulos nunca usam HTML, sem regressão. **Checado e OK:**
  sem segredo hardcoded (token ALRN lido em runtime); busca, tabelas e modal de CNPJ do hub escapam; scripts externos
  só o GoatCounter (resto é local em `vendor/`); nenhum workflow com gatilho `pull_request`; sondagem usa env var
  (padrão seguro, sem injeção de comando). **Hardening opcional (não são falhas):** fixar versões exatas das deps
  (requests/pytest usam `>=`); SRI no GoatCounter; CSP via meta; escapar também os KPIs dos `uf.js` dos 18 estados
  SICONFI (hoje só mostram nome de cidade do IBGE + números, risco ~nulo).
- **26/11 — sondagem deputados estaduais (via sondagem.yml do repo senadores, roda no GitHub porque o container não
  acessa gov).** 1ª varredura: **MG (ALMG) = coletável** (API aberta XML, `dadosabertos.almg.gov.br/ws/...`); PR (ALEP)
  promissor (verba de ressarcimento + dados abertos, mas reCAPTCHA); RS endereços não resolveram. 2ª sondagem dirigida
  (SP/RJ, com User-Agent de navegador): **SP = BLOQUEADO** — `www.al.sp.gov.br/repositorioDados/*.xml` dá 503 para o
  runner do GitHub mesmo com cabeçalho, e `dadosabertos.al.sp.gov.br` tem **certificado HTTPS quebrado**; sem caminho
  limpo agora. **RJ = DIFÍCIL** — os dados existem mas atrás de apps JavaScript: a verba (DOCIGP, `docigp.alerj.rj.gov.br`)
  é um app Laravel com **token embutido** (padrão parecido com o do RN/ALRN) e o `transparencia.alerj.rj.gov.br` é SPA
  (`/section/report/NNN` só devolve a casca; dados vêm por API interna). Coletável só com engenharia reversa da API —
  trabalhoso e frágil. **Recomendação ao dono: começar por MG** (rápido) para já ter um estado novo no ar; SP e RJ ficam
  como "possível, mas difícil" para depois. Aguardando o dono dizer se começo por MG. Deputados estaduais é 1 repo só
  (`quanto-custa-deputados-estaduais`), não precisa criar repo novo; cada assembleia tem coletor próprio (alece/alba/alrn).
- **26/11 — MG (ALMG) em construção.** A verba de MG fica no portal `almg.gov.br` (não na API de dados abertos): lista
  da legislatura em `.../verba-indenizatoria/?leg=20` (link `detalhe.html?id=<cod>` por deputado) e detalhe por
  deputado/ano `detalhe.html?id=<cod>&ano=AAAA` (tabela nota a nota: Emitente, CNPJ/CPF, Data, Número, Valor). O portal
  responde aos robôs do GitHub. **Escrito `coletor/almg.py`** (molde ALBA: verba nota a nota + subsídio fixado em lei =
  R$ 34.774,64, 75% do federal) + bloco ALMG e `CASAS['mg']` (MG, 77 vagas, desde 2023) no config.py + integração no
  atualizar.py (atualizar_cadastro_mg/coletar_mg/meses_mg + despacho `--uf mg`; MG coletado por último junto com BA por
  ser lento). **Parsers validados localmente** contra as páginas reais da sondagem: 77 deputados lidos, notas com
  fornecedor/CNPJ/valor corretos. Testes passam (15/15). Push no main; **coleta disparada** (atualizar.yml uf=mg).
  (Descoberta da API via várias rodadas da sondagem.yml do repo senadores.)
- **27/11 — MG NO AR.** O que travava: as tentativas de coleta de **madrugada** (23h–00h BRT) falhavam porque o portal
  `www.almg.gov.br` **não aceitava conexão** àquela hora (run noturno #20: Errno 101 IPv6; #21, já com IPv4 forçado em
  `coletor/http.py`, ConnectTimeout — "fora do ar nesta execução"). Não era bloqueio de IP (a sondagem já lera os 77
  deputados de dia). **Rodando de dia (run agendado das 08:32 e o manual das 10h BRT) a ALMG respondeu e coletou tudo.**
  Correção mantida: `coletor/http.py` força IPv4 (`allowed_gai_family=AF_INET`). **Auditoria MG 2025:** 75 deputados com
  verba, R$ 27,2 mi no ano (~R$ 30 mil/mês cada), sem negativos, sem nota sem fornecedor, fornecedores com CNPJ, subsídio
  R$ 34.774,64. Anos 2023–2026. **Ligado no site:** o seletor é dinâmico (lê `estados.json`, que o `gravar_estados` já
  preenche), então MG entrou sozinho; só foi preciso o **bloco de metodologia** `data-uf-texto="mg"` no `index.html`
  (espelha a Bahia) + MG nas descrições de SEO. Render local (Playwright): seletor, ranking, ficha e metodologia de MG
  **sem erro de JS**. Push no main (`estaduais`). **Lição:** portais de assembleia/governo podem cair de madrugada —
  coletar em horário comercial BR. Estados estaduais agora: **CE, BA, RN, MG**.
