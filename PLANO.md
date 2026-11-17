# Regras do projeto (valem para todos os sites e robôs)

1. **Toda e qualquer limitação dos dados é explicada no próprio site, com o motivo.** Ano que falta, órgão que não
   publica, valor que não dá para conferir, fonte diferente de outro estado, dado que ainda está sendo coletado:
   o aviso aparece na página onde o número é mostrado (e na Metodologia), dizendo o que falta e por quê.
2. **Divergência nos dados oficiais é sempre informada**, dizendo de quem é a responsabilidade (ex.: câmara que não
   mandou o balancete ao TCE). Se o dado está errado na fonte e não avisamos, a culpa passa a ser nossa.
3. **Não publicar número que não conseguimos conferir.** Na dúvida, fica de fora, com o aviso do item 1.
4. **CPF nunca inteiro**: sempre mascarado (***.456.789-**), em dados, páginas e arquivos brutos.
5. **Anonimato**: nenhum nome de autor nem link pessoal no site ("Sociedade do Progresso" pode).
6. **robots.txt de cada fonte é respeitado**, e os robôs consultam devagar (pausa entre consultas).
7. Robôs gravam como `robo-quanto-custa`; não enviar mudanças enquanto o robô do mesmo repositório estiver salvando.
8. Não mudar as cores do mapa.

# Plano: um repositório por estado (decidido em 13/11/2026)

## Decisão
- **Um repositório por estado** para os municípios (e, no futuro, deputados estaduais e governador do mesmo estado),
  em vez de juntar estados em 2 ou 3 repositórios grandes.
- **O hub** (`projetoquantocusta1-alt.github.io`) continua sendo a porta de entrada e liga tudo.
- Começa pelo **Ceará** (já existe: `quanto-custa-municipios`); os outros estados entram um a um.

## Por quê
1. Cada estado tem um tribunal de contas diferente (o TCE-CE tem API; outros publicam de outro jeito) → o robô de coleta é diferente por estado.
2. Tamanho: o GitHub recomenda repositório < 1 GB e o site do GitHub Pages tem limite de 1 GB. CE = 184 municípios; Brasil = 5.570 (MG 853, SP 645).
3. Cada repositório tem as próprias 6 h por execução de robô: os estados rodam em paralelo.
4. Abrir um estado novo = criar o repositório e ligar no hub, sem mexer no que funciona.

## Como fica
- `quanto-custa-nucleo`: código comum a todos os estados (privacidade de CPF, correção pelo IPCA, http, visual, montagem das páginas).
  Cada estado instala o núcleo no robô; corrige-se uma vez, vale para todos.
- `quanto-custa-municipios-XX` (XX = sigla do estado): só o robô de coleta daquele estado + os dados do site.
  Endereço: `https://quantocustaum.com/quanto-custa-municipios-xx/`.
- Hub: o Mensageiro lê uma lista de estados ativos e soma os totais; no mapa, clicar num estado leva ao site dele
  (estados sem dados aparecem como "em breve").
- Futuro: deputados estaduais e governador podem morar no repositório do próprio estado ("tudo sobre o estado").

## Cuidados
- Dados brutos (`dados_brutos`) fora do histórico do git (armazenamento à parte do GitHub), para o repositório não inchar;
  no repositório fica só o que o site mostra.
- Estados grandes (SP, MG) podem precisar de mais de um repositório (por período). Decidir com o tamanho real do CE medido.
- Antes de decidir tamanhos, medir o Ceará completo (2017–2026) quando a coleta terminar.
- Não renomear nem mexer no repositório do CE enquanto o robô do TCE estiver rodando.

## Passos (a fazer juntos)
1. Criar `quanto-custa-nucleo` (público, vazio) e dar acesso ao app do Claude.
2. Extrair o código comum do CE para o núcleo; o robô do CE passa a usar o núcleo.
3. Lista de estados no hub (`robo/estados.json`) e mapa do hub levando aos sites estaduais.
4. Decidir o nome do repositório do CE (`quanto-custa-municipios` → `quanto-custa-municipios-ce`?) — renomear muda o endereço
   do site (o GitHub Pages não redireciona), então fazer só com o hub já apontando para o novo endereço.
5. Próximo estado: escolher qual e estudar a fonte de dados do tribunal de contas dele.

# Ideia anotada (17/11/2026): Índice de Transparência e Governança Pública

Uma nota (por exemplo de 0 a 100) para cada órgão — Assembleia Legislativa, prefeitura, câmara municipal, tribunal de
contas como fonte — medindo **o quanto ele facilita ou dificulta que o cidadão veja como o dinheiro é gasto**.
Base: as dificuldades que os robôs do projeto encontram na prática (os robôs podem guardar essas evidências
automaticamente: cada tentativa, falha, atraso e divergência, com data).

Critérios (a partir do que já aconteceu):
1. **Acesso**: o site responde a robôs e a pessoas de fora? (bloqueados aos computadores do GitHub: TCM-BA, ALMG,
   CLDF, ALEPE, ALRS, ALMA; ALESP com erro 503; ALRN com erro interno; ALEPI com certificado de segurança inválido.)
2. **Formato aberto**: CSV, JSON ou API (bom) x HTML página a página, PDF ou planilha avulsa (ruim). Ex.: Alece com CSV
   mensal; ALBA com 20 notas por página e uma página por nota; ALPB com listas carregadas depois de abrir.
3. **Detalhe**: nota a nota, com CNPJ/CPF do fornecedor? Folha de pagamento com o nome de cada pessoa? (ALBA não
   publica a folha nominal, só o subsídio fixado em lei.)
4. **Pontualidade**: entrega no prazo do balancete (TCE) e do RREO (Tesouro)? (Glória-BA: 10 anos sem entregar o
   RREO; Anagé e Caetité sem 2026; prefeituras do CE sem o balancete do Executivo; câmaras de Moraújo, Tianguá e
   Caucaia sem balancete.)
5. **Consistência**: os números fecham? (notas x balancete: Acaraú, Ipu, Itarema; câmara zerada ou fora do padrão no
   RREO: Itabuna, Érico Cardoso e cerca de 20 câmaras por ano de 2019 a 2022.)
6. **Qualidade do cadastro**: nomes que batem entre folha e verba, sem linhas estranhas misturadas (arquivo antigo da
   Alece misturava aposentadorias e empenhos globais; nomes digitados com erro; "nome não identificado").
7. **Histórico**: anos anteriores disponíveis e no mesmo formato (Alece só confiável desde 2023).
8. **Estabilidade e documentação**: o endereço muda? há explicação dos campos? robots.txt claro? detalhes como "o mês
   precisa ter dois dígitos, senão o arquivo vem vazio".

Como mostrar: ranking por esfera e por estado, ficha de cada órgão com as evidências (o que faltou, quando, desde
quando), metodologia pública com os pesos, e atualização automática pelos robôs. Ligar à lista "Quem não prestou
contas" do site principal, que já é um primeiro passo.
