# Lula x Flávio: variação de votos entre o 1º e o 2º turno (Presidente, 2026)

Painel interativo (um único arquivo HTML) que mostra quanto Lula e Flávio ganharam ou perderam de votos entre o 1º turno (04/10/2026) e o 2º turno (25/10/2026), por **região, estado, cidade, bairro e local de votação**, e que cruza essa variação com o **perfil do eleitorado** (TSE) e a **renda** (Censo 2022, IBGE).

**Abrir o painel:** https://m-gnum.github.io/eleicoes-2026-lula-flavio/ (ou baixe `index.html` e abra no navegador; precisa de internet para o mapa e as bibliotecas).

## O que o painel responde

- Quanto cada candidato ganhou ou perdeu de votos entre os turnos, em votos e em pontos percentuais (p.p.) dos eleitores aptos do recorte (Brasil, região, estado, cidade ou bairro).
- De onde vieram esses votos: eleitores dos candidatos eliminados no 1º turno, queda da abstenção, queda de brancos e nulos. Vale a identidade, porque os aptos são os mesmos nos dois turnos: **Δ Lula + Δ Flávio = votos dos eliminados − Δ brancos − Δ nulos − Δ abstenção**.
- Se os dois candidatos ganharam votos nos mesmos lugares ou em lugares diferentes, e como são esses lugares (renda, % de mulheres, faixas de idade e escolaridade).
- Que combinações de características (por exemplo, % de mulheres × % de idosos) estão associadas a maior ou menor crescimento de cada candidato, de brancos + nulos e da abstenção.

Seções do painel: filtros, indicadores, mapa de bolhas (cheia = ganho, vazia = perda; vermelho = Lula, azul = Flávio), ranking, de onde vieram os votos, variação por unidade, perfil das áreas onde cada candidato mais ganhou e menos cresceu (regras de uma árvore de regressão), cruzamento de duas características e **resumo executivo** que se recalcula a cada filtro.

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
| Malha de setores censitários (GeoPackage, 472.780 setores) | https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/gpkg/BR/BR_setores_CD2022.gpkg | polígonos para cruzar os locais de votação com os setores |

## Como o painel foi construído

Cada script lê a saída do anterior. Rodar sempre da raiz do projeto, com as dependências de `requirements.txt` (`pip install -r requirements.txt`):

| Passo | Script | Saída | O que faz |
|---|---|---|---|
| 0 | `scripts/00_baixar_dados.sh` | `dados/`, `BR_setores_CD2022.gpkg` | baixa e descompacta os arquivos acima |
| 1 | `scripts/01_base_secao.py` | `saida/base_secao.parquet` | uma linha por seção (UF + município + zona + seção): aptos, comparecimento e abstenção, Lula, Flávio, eliminados, brancos e nulos nos dois turnos, deltas e dados do local de votação. Valida que não há seção duplicada e que comparecimento = soma dos votos |
| 2 | `scripts/02_locais_renda.py` | `saida/locais_renda.parquet` | para cada local de votação, a renda média do responsável no setor onde ele cai e a média num raio de 1 km, ponderada por responsáveis × fração da área do setor dentro do raio (projeção SIRGAS 2000 / Brazil Polyconic, EPSG:5880) |
| 3 | `scripts/03_perfil_secao.py` | `saida/perfil_secao.parquet` | perfil do eleitorado por seção: mulheres, faixas de idade, escolaridade, cor/raça |
| 4 | `scripts/04_analise.py` | `saida/secao_analise.parquet`, `saida/locais_dashboard.parquet`, `saida/analise_perfil.json` | junta tudo, calcula as variações em p.p. dos aptos, agrega por local de votação (a tabela que alimenta o painel) e roda análises de apoio (quintis, comparação perdeu × ganhou e uma regressão ponderada) |
| 5 | `scripts/05_dashboard.py` | `index.html`, `saida/secoes_variacao_votos.csv` | embute a tabela por local no modelo `scripts/dashboard_template.html` e gera o painel e o CSV por seção |
| 6 | `scripts/06_conferencia_tse.py` | texto no terminal | compara os totais da base com os oficiais do TSE por município e zona |

### Arquivos finais que alimentam o HTML

`saida/locais_dashboard.parquet` (incluído neste repositório) tem **uma linha por local de votação** (94.046 locais, sem o exterior). É a única fonte do HTML; o script 05 só precisa dele e do modelo para regenerar o painel:

| Coluna | Significado |
|---|---|
| `uf`, `cd_mun`, `zona`, `nr_local`, `nm_local`, `municipio`, `bairro`, `regiao` | identificação do local (bairro = o do endereço no TSE) |
| `secoes`, `aptos` | seções do local e eleitores aptos |
| `lula_t1`, `lula_t2`, `flavio_t1`, `flavio_t2` | votos de cada candidato em cada turno |
| `outros_t1`, `branco_t1/_t2`, `nulo_t1/_t2`, `abst_t1/_t2` | votos dos eliminados no 1º turno, brancos, nulos e abstenções |
| `perf_eleitores`, `mulheres`, `idade_16_24`, `idade_25_44`, `idade_45_59`, `idade_60_mais`, `esc_sem_instrucao`, `esc_fundamental`, `esc_medio`, `esc_superior` | perfil do eleitorado do local (contagens, TSE) |
| `renda_media_1km` | renda média do responsável pelo domicílio, ponderada num raio de 1 km (R$, Censo 2022) |
| `lat`, `lon`, `coord_aprox` | coordenada (mediana das seções); `coord_aprox = 1` quando caiu no centro da cidade por falta de coordenada válida |

O CSV `saida/secoes_variacao_votos.csv` (por seção, ~118 MB) passa do limite de arquivo do GitHub e por isso não está aqui; é gerado pelo script 05 quando a saída do script 04 está na pasta.

### O HTML (`index.html`)

- **Um único arquivo**: a tabela por local é gravada dentro do HTML como JSON compactado (gzip + base64, ~7 MB) e lida no navegador com `DecompressionStream`. Colunas embutidas: `uf, mun, bai, lat, lon, ca, sec, ap, ab1, ab2, l1, l2, f1, f2, o1, b1, b2, n1, n2, pe, mu, i1..i4, e0..e3, rd` (versões curtas das colunas acima).
- **Bibliotecas, carregadas por CDN**: [Leaflet 1.9.4](https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js) (mapa), [Plotly 2.35.2](https://cdn.plot.ly/plotly-2.35.2.min.js) (gráficos) e o mapa base cinza da Esri (*World Light Gray*). O OpenStreetMap bloqueia (403) páginas abertas por `file://`, por isso não é usado.
- Todo o cálculo (agregações por região, estado, cidade, bairro e local; quintis; árvore de regressão; resumo executivo) roda **no navegador**, a cada filtro.
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
- **Renda** é a do **responsável pelo domicílio** (Censo 2022), média ponderada num raio de 1 km do local, não a renda familiar. O salário mínimo usado para converter em SM é R$ 1.621.
- **Exterior (ZZ) fora**: os totais cobrem só o Brasil.
- **Coordenadas**: 623 locais sem coordenada válida foram posicionados no centro da própria cidade; 4 ficaram sem posição e só aparecem nos totais.
- As **regras de perfil** (árvore de regressão) e os insights são exploratórios, calculados nos dados do filtro atual; não provam causa.

## Reproduzir

```bash
pip install -r requirements.txt
bash scripts/00_baixar_dados.sh                  # ~3 GB compactados
python -I scripts/01_base_secao.py
python -I scripts/02_locais_renda.py
python -I scripts/03_perfil_secao.py
python -I scripts/04_analise.py
python -I scripts/05_dashboard.py                # gera index.html
python -I scripts/06_conferencia_tse.py          # confere os totais com o TSE
```

Só para regenerar o HTML a partir da tabela já pronta, basta `saida/locais_dashboard.parquet`, o modelo e `python -I scripts/05_dashboard.py`.
