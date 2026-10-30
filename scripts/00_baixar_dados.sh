#!/usr/bin/env bash
# Baixa os dados abertos do TSE e do IBGE usados no painel e descompacta em dados/ (layout esperado pelos scripts 01 a 03).
# Rodar da raiz do projeto: bash scripts/00_baixar_dados.sh
# Atenção: o download total passa de 3 GB compactado (a pasta dados/ chega a ~36 GB descompactada).
set -euo pipefail

TSE="https://cdn.tse.jus.br/estatistica/sead/odsele"
IBGE="https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022"
mkdir -p dados

baixa() { # url pasta_destino
  local url="$1" pasta="dados/$2" zip
  zip="dados/$(basename "$url")"
  if [ -d "$pasta" ] && [ -n "$(ls -A "$pasta" 2>/dev/null)" ]; then echo "já existe: $pasta"; return; fi
  echo "baixando $url"
  curl -fL --retry 3 -o "$zip" "$url"
  mkdir -p "$pasta"
  unzip -q -o "$zip" -d "$pasta"
  rm -f "$zip"
}

# resultados da eleição (por seção) e locais de votação com coordenadas
baixa "$TSE/votacao_secao/votacao_secao_2026_BR.zip" votacao_secao_2026_BR
baixa "$TSE/detalhe_votacao_secao/detalhe_votacao_secao_2026.zip" detalhe_votacao_secao_2026
baixa "$TSE/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip" eleitorado_local_votacao_2026

# conferência dos totais (script 06): resultados por município e zona
baixa "$TSE/votacao_candidato_munzona/votacao_candidato_munzona_2026.zip" votacao_candidato_munzona_2026
baixa "$TSE/detalhe_votacao_munzona/detalhe_votacao_munzona_2026.zip" detalhe_votacao_munzona_2026

# perfil do eleitorado por seção (um zip por UF, mais ZZ = exterior), todos na mesma pasta
if [ ! -d dados/perfil_eleitor_secao_2026 ] || [ -z "$(ls -A dados/perfil_eleitor_secao_2026 2>/dev/null)" ]; then
  mkdir -p dados/perfil_eleitor_secao_2026
  for uf in AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ; do
    echo "baixando perfil_eleitor_secao_2026_$uf"
    curl -fL --retry 3 -o "dados/perfil_$uf.zip" "$TSE/perfil_eleitor_secao/perfil_eleitor_secao_2026_$uf.zip"
    unzip -q -o "dados/perfil_$uf.zip" -d dados/perfil_eleitor_secao_2026
    rm -f "dados/perfil_$uf.zip"
  done
fi

# IBGE: renda do responsável por setor censitário (Censo 2022) e malha de setores
baixa "$IBGE/Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip" Agregados_por_setores_renda_responsavel_BR_20260508_csv
if [ ! -f BR_setores_CD2022.gpkg ]; then
  curl -fL --retry 3 -o BR_setores_CD2022.gpkg "$IBGE/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/gpkg/BR/BR_setores_CD2022.gpkg"
fi
# segurança pública: vítimas de CVLI por município e mês (Sinesp-VDE, gov.br/MJSP), script 07
mkdir -p dados/sinesp_vde
for ano in 2025 2026; do
  [ -s "dados/sinesp_vde/bancovde-$ano.xlsx" ] || curl -fL --retry 3 -A "Mozilla/5.0" -o "dados/sinesp_vde/bancovde-$ano.xlsx" \
    "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-$ano.xlsx/@@download/file"
done
# IBGE: lista oficial de municípios (código IBGE) e população residente do Censo 2022 (SIDRA, tabela 4709), script 07
mkdir -p dados/ibge_municipios
[ -s dados/ibge_municipios/localidades_municipios.json ] || curl -fL --retry 3 -o dados/ibge_municipios/localidades_municipios.json "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
[ -s dados/ibge_municipios/sidra_4709_populacao_2022.json ] || curl -fL --retry 3 -o dados/ibge_municipios/sidra_4709_populacao_2022.json "https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/2022/variaveis/93?localidades=N6%5Ball%5D"
# IBGE: PIB dos Municípios 2010-2023 (PIB e PIB per capita), script 10; o zip tem acento no nome do arquivo, por isso a extração em python
mkdir -p dados/ibge_pib
[ -s dados/ibge_pib/pib_municipios_2010_2023.xlsx ] || {
  curl -fL --retry 3 -o dados/ibge_pib/base.zip "https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_xlsx.zip"
  python3 -c "import zipfile; z = zipfile.ZipFile('dados/ibge_pib/base.zip'); open('dados/ibge_pib/pib_municipios_2010_2023.xlsx', 'wb').write(z.read(z.namelist()[0]))"
  rm dados/ibge_pib/base.zip
}
echo "ok"
