# Lula x Flávio: variação de votos entre o 1º e o 2º turno (Presidente, 2026)

Painel interativo (um único arquivo HTML) que mostra quanto Lula e Flávio ganharam ou perderam de votos entre o 1º turno (04/10/2026) e o 2º turno (25/10/2026), por **região, estado, cidade, bairro e local de votação**, e que cruza essa variação com o **perfil do eleitorado** (TSE), a **renda** (Censo 2022, IBGE) e a **segurança pública** (taxa de mortes violentas, Sinesp-VDE do Ministério da Justiça).

**Abrir o painel:** https://m-gnum.github.io/analise-virada-lula-flavio-1o-2o-turno-eleicoes-2026/ (ou baixe `index.html` e abra no navegador; precisa de internet para o mapa e as bibliotecas).

## O que o painel responde

- Quanto cada candidato ganhou ou perdeu de votos entre os turnos, em votos e em pontos percentuais (p.p.) dos eleitores aptos do recorte (Brasil, região, estado, cidade ou bairro).
- De onde vieram esses votos: eleitores dos candidatos eliminados no 1º turno, queda da abstenção, queda de brancos e nulos. Vale a identidade, porque os aptos são os mesmos nos dois turnos: **Δ Lula + Δ Flávio = votos dos eliminados − Δ brancos − Δ nulos − Δ abstenção**.
- Se os dois candidatos ganharam votos nos mesmos lugares ou em lugares diferentes, e como são esses lugares (renda, mortes violentas, % de mulheres, faixas de idade e escolaridade).
- Que combinações de características (por exemplo, % de mulheres × % de idosos) estão associadas a maior ou menor crescimento de cada candidato, de brancos + nulos e da abstenção.

Seções do painel (todas se recalculam a cada filtro):

0. **Como ler este painel**: três linhas no topo (o que é variação e p.p., o que o painel mostra e não mostra) e os avisos ao final.
1. **Filtros** (região, estado, cidade, bairro, nível do mapa) e o botão **Copiar link desta visão**: os filtros e as escolhas do painel ficam no endereço (`#uf=SP&mun=CAMPINAS&ord=ppl...`), então quem abre o link vê o mesmo recorte.
2. **Indicadores** de variação (cartões em duas linhas) ao lado do gráfico **"De onde vieram os votos"**, com insights.
3. **Mapa de bolhas** (cheia = ganho, vazia = perda; vermelho = Lula, azul = Flávio) e ranking das maiores variações (top 5 ganhos e perdas de cada candidato), que traz em cada linha o tamanho da unidade (eleitores aptos e % do recorte) e, nos ganhos, a parcela do ganho total do recorte.
4. **Tabela de variação por unidade** (estados, ou cidades, bairros ou locais, conforme o filtro; por padrão as 20 com maior movimento, e dá para ordenar por votos, p.p., número de aptos, cada faixa de renda, taxa de CVLI ou PIB per capita, e mostrar 20, 50, 100 ou todas). Colunas: unidade; **tamanho** (eleitores aptos, % do recorte e % do ganho de cada candidato); **resultado nos dois turnos** (% dos votos válidos de Lula e Flávio no 1º e no 2º turno, com a indicação de quem liderou e se a liderança **virou**); % do eleitorado em áreas com renda média **menos que 1 SM**, **entre 1 SM e 3 SM**, **entre 3 SM e 5 SM** e **acima de 5 SM** (as quatro faixas somam 100%); **taxa de CVLI por 100 mil habitantes**; **PIB per capita 2023** (IBGE, PIB dos Municípios; para estados e regiões, PIB somado / população somada); barras com a variação de Lula e Flávio (votos e p.p. dos aptos); e uma segunda coluna de barras com **de onde vieram os votos** (os mesmos dados do gráfico do topo: eleitores dos candidatos eliminados no 1º turno e queda de brancos, nulos e abstenção; valor negativo = a categoria cresceu). Cada indicador mostra quanto está acima ou abaixo da média do recorte. Os insights citam esses indicadores, as viradas de liderança e a concentração do ganho ("Lula ganhou mais nas cidades A, B e C, que têm % de renda entre 3 SM e 5 SM acima da média"). A taxa de CVLI e o PIB per capita só existem até o nível de cidade: em bairros e locais o valor da cidade se repete. PIB per capita alto costuma refletir atividade econômica concentrada (indústria, petróleo, porto), não a renda dos moradores.
5. **Perfil das áreas** onde cada candidato mais ganhou e menos cresceu: frases em linguagem simples, com as características em negrito ("a combinação de **mais mulheres**, **menos eleitores com 60 anos ou mais** e **renda mais baixa** parece ter tido mais impacto positivo para Lula"), junto das regras numéricas (árvore de regressão), a tabela de perfil médio e os quintis (aberta por padrão). Com uma única cidade (ou bairro ou local) a taxa de CVLI não varia entre os locais: a coluna continua na tabela de perfil, com a taxa da cidade e o aviso "métrica única para a cidade inteira" (ela não entra nas regras nem nos quintis).
6. **Resumo executivo** do recorte, com as mesmas frases em linguagem simples e um bloco de **Segurança pública (CVLI)**: taxa do recorte contra a média do estado e do Brasil, taxa nos lugares onde cada candidato mais e menos cresceu, e correlação com o crescimento quando é relevante (|r| ≥ 0,3). Os trechos que citam unidades (maiores ganhos, perdas, rankings proporcionais) informam também **quanto cada unidade pesa no recorte** (% dos aptos).
7. **Análise estatística** (bloco final, com seletores próprios; não muda com os filtros do topo): regressões ponderadas por aptos que medem o efeito de cada característica da área (renda, escolaridade, idade, sexo e, entre cidades, CVLI) na variação de Lula e de Flávio, com intervalo de confiança; recortes de Brasil, 5 regiões e 27 estados; comparação do efeito entre regiões (e entre estados de uma região); legenda do filtro "Modelo" (replicado no 2º gráfico) e legenda de ponto cheio/vazio; índice de Moran (os locais vizinhos variaram de forma parecida?) e mapa de manchas por cidade (LISA).

**Abas:** o painel tem duas abas. **Painel** (seções 0 a 7) e **Curiosidades**: 6 blocos de casos incomuns de cidades e estados (bairros ou cidades muito uniformes ou muito diferentes, outliers, correlações muito diretas entre perfil e variação (renda, escolaridade, faixas de idade, mulheres e CVLI; nas cidades de R² alto, o texto mostra quais características mais acompanham a variação de cada candidato), perfil sem efeito, viradas de liderança e o peso dos eliminados, da abstenção e de brancos e nulos no ganho de Lula e Flávio). Cada bloco tem um mapa ao lado, com as cidades (círculos) e os estados (quadrados) citados; o botão "ver no painel" abre a cidade ou o estado na aba Painel. A aba explica, em linguagem simples, desvio, correlação e R². Os casos vêm de regras com corte de tamanho (`scripts/09_curiosidades.py`) e descrevem padrões, não causas.

**Celular:** o painel usa o layout de desktop em qualquer tela (`<meta name="viewport" content="width=1280">`); em dispositivos móveis a página aparece reduzida e dá para ampliar com o gesto de pinça.

## Fontes de dados

Todos os dados são abertos. Os scripts esperam os arquivos na pasta `dados/` com esta estrutura (o script `scripts/00_baixar_dados.sh` baixa e organiza tudo; o download passa de 3 GB compactado e a pasta chega a ~36 GB descompactada).

### TSE (Dados Abertos)

Portal: https://dadosabertos.tse.jus.br/dataset/resultados-2026 e https://dadosabertos.tse.jus.br/dataset/eleitorado-2026

| Arquivo | URL | Uso |
|---|---|---|
| Votação por seção (Brasil) | https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_BR.zip | votos de cada candidato, brancos e nulos por seção, nos dois turnos |
| Detalhe da votação por seção | https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2026.zip | aptos, comparecimento e abstenção por seção |
| Locais de votação | https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip | endereço, bairro, latitude e longitude de cada local |
| Perfil do eleitorado por seção (um zip por UF e `ZZ` = exterior) | `https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitor_secao/perfil_eleitor_secao_2026_<UF>.zip` | sexo, faixa etária, escolaridade e cor/raça por seção |
| Votação por candidato, município e zona | https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2026.zip | só para conferir os totais (script 06) |
| Detalhe da votação por município e zona | https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_2026.zip | só para conferir os totais (script 06) |

Atenção: os arquivos de resultado precisam ter sido gerados **depois** do 2º turno. Os de `munzona` baixados antes da apuração só têm o 1º turno (verifique `NR_TURNO` e `DT_GERACAO`).

### IBGE (Censo 2022)

Portal: https://censo2022.ibge.gov.br/panorama/downloads.html

| Arquivo | URL | Uso |
|---|---|---|
| Renda do responsável por setor censitário (CSV) | https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip | `V06001` (responsáveis), `V06004` (renda média) e `V06006` (mediana) por setor |
| Lista oficial de municípios (código IBGE e nome) | https://servicodados.ibge.gov.br/api/v1/localidades/municipios | casar os municípios do TSE e do Sinesp com o código IBGE |
| População residente por município, Censo 2022 (SIDRA, tabela 4709, soma 203.080.756) | https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/2022/variaveis/93?localidades=N6[all] | denominador da taxa de CVLI |
| Malha de setores censitários (GeoPackage, 472.780 setores) | https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/gpkg/BR/BR_setores_CD2022.gpkg | polígonos para cruzar os locais de votação com os setores |

### Ministério da Justiça (Sinesp-VDE)

Página oficial: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023

| Arquivo | URL | Uso |
|---|---|---|
| Base de dados 2025 (um registro por município, evento e mês) | https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-2025.xlsx/@@download/file | vítimas de CVLI de out/2025 a dez/2025 |
| Base de dados 2026 | https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-2026.xlsx/@@download/file | vítimas de CVLI de jan/2026 a set/2026 (último mês fechado; página atualizada em 26/10/2026) |

A taxa usa a janela dos **12 últimos meses fechados (out/2025 a set/2026)**. **CVLI** (crimes violentos letais intencionais) = homicídio doloso + feminicídio + roubo seguido de morte (latrocínio) + lesão corporal seguida de morte, em número de **vítimas**, só da abrangência estadual. O pacote R `BrazilCrime` (função `get_sinesp_vde_data`) não foi usado: ele traz uma cópia embutida dos dados que vai só até 2024. A base não tem código IBGE, só nome do município; o casamento com os municípios do TSE é por UF + nome normalizado (sem acento nem pontuação), e o código IBGE vem da lista oficial do IBGE pelo mesmo critério. Grafias que divergem (por exemplo Assú/Açu e Boa Saúde/Januário Cicco) estão listadas à mão nos dicionários `ALIASES` (Sinesp) e `ALIASES_IBGE` (IBGE) do script 07, que para com erro se algum município do TSE ficar sem código IBGE ou se dois compartilharem o mesmo. Boa Esperança do Norte (MT) não existe no Sinesp nem na tabela de população e fica sem taxa. O Distrito Federal vem com uma linha por região administrativa e é somado em Brasília. O Sinesp informa só o município: **não existe taxa por bairro**.

## Como o painel foi construído

Cada script lê a saída do anterior. Rodar sempre da raiz do projeto, com as dependências de `requirements.txt` (`pip install -r requirements.txt`):

| Passo | Script | Saída | O que faz |
|---|---|---|---|
| 0 | `scripts/00_baixar_dados.sh` | `dados/` (inclui `dados/sinesp_vde/` e `dados/ibge_municipios/`), `BR_setores_CD2022.gpkg` | baixa e descompacta os arquivos acima, inclusive o Sinesp-VDE e as duas consultas à API do IBGE |
| 1 | `scripts/01_base_secao.py` | `saida/base_secao.parquet` | uma linha por seção (UF + município + zona + seção): aptos, comparecimento e abstenção, Lula, Flávio, eliminados, brancos e nulos nos dois turnos, deltas e dados do local de votação. Valida que não há seção duplicada e que comparecimento = soma dos votos |
| 2 | `scripts/02_locais_renda.py` | `saida/locais_renda.parquet` | para cada local de votação, a renda média do responsável no setor onde ele cai e a média num raio de 1 km, ponderada por responsáveis × fração da área do setor dentro do raio (projeção SIRGAS 2000 / Brazil Polyconic, EPSG:5880) |
| 3 | `scripts/03_perfil_secao.py` | `saida/perfil_secao.parquet` | perfil do eleitorado por seção: mulheres, faixas de idade, escolaridade, cor/raça |
| 4 | `scripts/04_analise.py` | `saida/secao_analise.parquet`, `saida/locais_dashboard.parquet`, `saida/analise_perfil.json` | junta tudo, calcula as variações em p.p. dos aptos, agrega por local de votação (a tabela que alimenta o painel) e roda análises de apoio (quintis, comparação perdeu × ganhou e uma regressão ponderada) |
| 7 | `scripts/07_seguranca_sinesp.py` | `saida/seguranca_municipio.parquet` | taxa de CVLI por município: soma as vítimas dos 12 últimos meses fechados, casa os municípios do TSE com o Sinesp (UF + nome) e com o código IBGE, e divide pela população do Censo 2022. **Roda antes do 05** |
| 8 | `scripts/08_analise_estatistica.py` | `saida/estatistica.json` | regressões (cada característica sozinha, todas juntas, dentro da cidade e entre cidades), teste de interação renda × região (e renda × estado dentro de cada região), índice de Moran e LISA (detalhes em "Análise estatística", abaixo); roda antes do 05 |
| 9 | `scripts/09_curiosidades.py` | `saida/curiosidades.json` | casos curiosos (uniformidade, outliers, correlações fortes, perfil sem efeito, outros cenários e eliminados × abstenção × brancos e nulos) para a aba "Curiosidades"; roda antes do 05 |
| 10 | `scripts/10_pib_municipio.py` | `saida/pib_municipio.parquet` | PIB e PIB per capita 2023 por município (IBGE, PIB dos Municípios, baixado por `00_baixar_dados.sh`), casados pelo código IBGE; guarda também a população implícita (PIB / per capita) para somar estados e regiões. **Roda antes do 05** |
| 5 | `scripts/05_dashboard.py` | `index.html`, `saida/secoes_variacao_votos.csv` | embute a tabela por local, a segurança por município e os resultados estatísticos no modelo `scripts/dashboard_template.html` e gera o painel e o CSV por seção |
| 6 | `scripts/06_conferencia_tse.py` | texto no terminal | compara os totais da base com os oficiais do TSE por município e zona |

### Arquivos finais que alimentam o HTML

`saida/locais_dashboard.parquet` (incluído neste repositório) tem **uma linha por local de votação** (94.046 locais, sem o exterior). É a fonte do HTML junto com `saida/seguranca_municipio.parquet` (abaixo); o script 05 só precisa dos dois e do modelo para regenerar o painel:

| Coluna | Significado |
|---|---|
| `uf`, `cd_mun`, `zona`, `nr_local`, `nm_local`, `municipio`, `bairro`, `regiao` | identificação do local (bairro = o do endereço no TSE) |
| `secoes`, `aptos` | seções do local e eleitores aptos |
| `lula_t1`, `lula_t2`, `flavio_t1`, `flavio_t2` | votos de cada candidato em cada turno |
| `outros_t1`, `branco_t1/_t2`, `nulo_t1/_t2`, `abst_t1/_t2` | votos dos eliminados no 1º turno, brancos, nulos e abstenções |
| `perf_eleitores`, `mulheres`, `idade_16_24`, `idade_25_44`, `idade_45_59`, `idade_60_mais`, `esc_sem_instrucao`, `esc_fundamental`, `esc_medio`, `esc_superior` | perfil do eleitorado do local (contagens, TSE) |
| `renda_media_1km` | renda média do responsável pelo domicílio, ponderada num raio de 1 km (R$, Censo 2022) |
| `lat`, `lon`, `coord_aprox` | coordenada (mediana das seções); `coord_aprox = 1` quando caiu no centro da cidade por falta de coordenada válida |

`saida/seguranca_municipio.parquet` (também incluído) tem **uma linha por município** (5.571):

| Coluna | Significado |
|---|---|
| `uf`, `cd_mun`, `municipio` | município, com o código do TSE |
| `cd_mun_ibge` | código IBGE de 7 dígitos |
| `cvli_12m` | vítimas de CVLI de out/2025 a set/2026 (Sinesp-VDE); vazio se o Sinesp não tem o município (Boa Esperança do Norte/MT) |
| `pop_2022` | população residente do Censo 2022 |
| `taxa_cvli_100k` | `cvli_12m / pop_2022 × 100.000`. Brasil: 15,3 por 100 mil |

O CSV `saida/secoes_variacao_votos.csv` (por seção, ~118 MB) passa do limite de arquivo do GitHub e por isso não está aqui; é gerado pelo script 05 quando a saída do script 04 está na pasta.

### Análise estatística (`scripts/08_analise_estatistica.py`)

O desenho foi fixado antes de rodar, para não "pescar" resultados. Resposta: variação de cada candidato em p.p. dos aptos. Explicativas: log da renda do responsável, % ensino superior, % sem instrução, % 60+, % 16 a 24 anos, % mulheres (e log da taxa de CVLI no modelo entre cidades). Amostra: 91.507 locais com 100 ou mais aptos e perfil e renda conhecidos.

| Modelo | O que compara | Erro-padrão |
|---|---|---|
| Cada característica sozinha | locais, uma variável por vez | agrupado por município |
| Ajustado | locais, todas as características juntas | agrupado por município |
| Dentro da cidade | locais da mesma cidade (efeito fixo de município) | agrupado por município |
| Entre cidades | 5.568 cidades, com CVLI (só em recortes com 30 ou mais municípios; fora AC, AP, RR e DF) | agrupado por UF (robusto HC1 dentro de um estado) |

- Os efeitos são **por +1 desvio-padrão** (ponderado por aptos), em p.p. dos aptos, com IC de 95%. "Efeito relevante" = IC longe de zero **e** efeito de pelo menos 0,5 p.p., porque com 94 mil locais quase tudo é significativo. Correção de Holm nos p-valores, dentro de cada modelo e recorte.
- Rodado para o Brasil, as 5 regiões e os 27 estados. O erro-padrão agrupado usa t de Student com menos de 50 grupos e HC1 (robusto) quando há um grupo só (DF; modelos entre cidades de um estado). Teste conjunto de interação da renda entre regiões e, dentro de cada região, entre estados. No painel: o 1º gráfico tem todos os recortes; o 2º e o 3º (Moran) mostram o Brasil + 5 regiões ou uma região + seus estados. Todos os estados têm 310 ou mais locais; o LISA continua nacional, por cidade.
- **Qual modelo ler:** o "ajustado: todas juntas" é a leitura principal; "dentro da cidade" serve de checagem (se o efeito some, vinha de diferenças entre cidades); "entre cidades" é o único com CVLI; os "sozinha" só para comparar.
- **Índice de Moran** (8 vizinhos mais próximos, teste por permutação) para a variação e para a **parte que o perfil não explica** (o resíduo do modelo ajustado: a variação real menos a prevista só por renda, escolaridade, idade e sexo; se ainda é parecida entre vizinhos, há estrutura geográfica que o perfil não captura); **LISA** por cidade (p < 0,01, sem correção para comparações múltiplas).
- Resultados em `saida/estatistica.json`, embutido no HTML. Para refazer: `python -I scripts/08_analise_estatistica.py` e depois o 05.
- Leitura: são **associações entre áreas** (falácia ecológica), não causas; os dados são todos os locais, não uma amostra, então o intervalo mede a dependência de quais cidades entram; características correlacionadas (VIF até 4,1) pedem comparar "sozinha" com "ajustada"; o CVLI só existe por cidade.

### O HTML (`index.html`)

- **Um único arquivo**: a tabela por local é gravada dentro do HTML como JSON compactado (gzip + base64, ~7 MB) e lida no navegador com `DecompressionStream`. Colunas embutidas: `uf, mun, bai, lat, lon, ca, sec, ap, ab1, ab2, l1, l2, f1, f2, o1, b1, b2, n1, n2, pe, mu, i1..i4, e0..e3, rd` (versões curtas das colunas acima) e, para cada município, `[nome, uf, vítimas de CVLI, população]`.
- **Bibliotecas, carregadas por CDN**: [Leaflet 1.9.4](https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js) (mapa), [Plotly 2.35.2](https://cdn.plot.ly/plotly-2.35.2.min.js) (gráficos) e o mapa base cinza da Esri (*World Light Gray*). O OpenStreetMap bloqueia (403) páginas abertas por `file://`, por isso não é usado.
- Todo o cálculo (agregações por região, estado, cidade, bairro e local; quintis; árvore de regressão; resumo executivo) roda **no navegador**, a cada filtro. A taxa de CVLI de um grupo de municípios é a soma das vítimas dividida pela soma da população (não a média das taxas). Ela entra como mais uma **característica** no perfil das áreas e no cruzamento; ao filtrar uma cidade, o valor é o mesmo em todos os locais e a característica sai dessas análises.
- O modelo editável é `scripts/dashboard_template.html`; o script 05 só troca o marcador `__DADOS_B64__` pelos dados.

## Conferência com os totais oficiais

O script 06 compara a base por seção com os arquivos oficiais por município e zona (Brasil, sem exterior). Os totais **batem exatamente** nos dois turnos:

| | 1º turno | 2º turno |
|---|---|---|
| Lula | 53.722.151 | 64.056.078 |
| Flávio | 55.960.603 | 59.654.544 |
| Aptos | 157.828.968 | 157.828.819 |
| Comparecimento | 124.934.069 | 127.854.631 |
| Abstenção | 32.894.899 | 29.974.188 |
| Brancos | 2.294.982 | 1.425.821 |

Variação nacional (sem exterior): Lula **+10,33 mi** de votos e Flávio **+3,69 mi**; a abstenção caiu de 20,8% para 19,0% dos aptos.

Única diferença: no 1º turno o TSE informa 5.123 "nulos técnicos" separados dos nulos (nulos: 3.669.181 contra 3.664.058 na base). Na base por seção eles ficam em "votos dos eliminados" (0,004% dos votos), o que não altera os totais nem a identidade de fluxo dos votos.

## Limitações e cuidados

- **Falácia ecológica**: as relações são entre áreas (locais de votação), não entre pessoas. Um local com mais jovens que ganhou votos não prova como os jovens votaram.
- **Local de votação, não seção**: o mapa e os gráficos agrupam as seções do mesmo local (499 mil seções em 94 mil locais).
- **Perfil do eleitorado** (sexo, idade, escolaridade) vem do perfil por seção do TSE, gerado em julho de 2026, e descreve quem vota no local (diferença de ~1,5% para os aptos do 2º turno). **Cor/raça** está informada para só ~21% dos eleitores e não foi usada.
- **Renda** é a do **responsável pelo domicílio** (Censo 2022), média ponderada num raio de 1 km do local, não a renda familiar. O salário mínimo usado para converter em SM é R$ 1.621 (a renda do Censo é de 2022, quando o SM era R$ 1.212).
- **Faixas de renda da tabela** (menos que 1 SM, entre 1 SM e 3 SM, entre 3 SM e 5 SM e acima de 5 SM): o IBGE não publica a distribuição de renda por setor, só média e mediana. Por isso a coluna mostra a **% do eleitorado que vota em locais cuja renda média** fica em cada faixa. Não é a % de domicílios nem de pessoas, e em bairros ou locais pequenos o valor tende a 0% ou 100%.
- **CVLI** é um dado do **município inteiro** (o Sinesp não publica por bairro): em bairros e locais, o valor se repete e a comparação é da cidade com a média do estado. Em cidades pequenas a taxa oscila muito com poucos casos (o painel mostra o número de vítimas). Estados podem classificar os casos de forma diferente no Sinesp.
- **Frases em linguagem simples** ("mais mulheres", "renda mais baixa") comparam um grupo de áreas com a média do filtro e descrevem **tipos de área**, não pessoas; não indicam causa.
- **Exterior (ZZ) fora**: os totais cobrem só o Brasil.
- **Coordenadas**: 623 locais sem coordenada válida foram posicionados no centro da própria cidade; 4 ficaram sem posição e só aparecem nos totais.
- **Tamanho das unidades**: rankings proporcionais (p.p. dos aptos) podem ser dominados por unidades pequenas. Por isso as frases mostram o peso de cada unidade citada, os rankings e perfis ignoram unidades com menos de 0,5% dos aptos do recorte (quando há unidades suficientes) e as correlações são ponderadas pelo número de aptos.
- **Análise estatística:** o perfil explica só parte da variação (R² de 22% e 36% no modelo ajustado para o Brasil, para Lula e Flávio), o sinal de algumas características inverte quando as outras entram no modelo e o efeito da renda difere entre regiões. O Moran continua alto depois de descontar o perfil: há estrutura geográfica que o perfil não captura.
- As **regras de perfil** (árvore de regressão) e os insights são exploratórios, calculados nos dados do filtro atual; não provam causa.

## Reproduzir

```bash
pip install -r requirements.txt
bash scripts/00_baixar_dados.sh                  # ~3 GB compactados
python -I scripts/01_base_secao.py
python -I scripts/02_locais_renda.py
python -I scripts/03_perfil_secao.py
python -I scripts/04_analise.py
python -I scripts/07_seguranca_sinesp.py         # taxa de CVLI por município (roda antes do 05)
python -I scripts/08_analise_estatistica.py       # regressões, Moran e LISA (roda antes do 05)
python -I scripts/09_curiosidades.py              # casos da aba Curiosidades (roda antes do 05)
python -I scripts/10_pib_municipio.py             # PIB per capita por município (roda antes do 05)
python -I scripts/05_dashboard.py                # gera index.html
python -I scripts/06_conferencia_tse.py          # confere os totais com o TSE
```

Só para regenerar o HTML a partir das tabelas prontas, basta `saida/locais_dashboard.parquet`, `saida/seguranca_municipio.parquet`, `saida/pib_municipio.parquet`, `saida/estatistica.json`, `saida/curiosidades.json`, o modelo e `python -I scripts/05_dashboard.py`.
