"""Confere os totais da base por seção com os totais oficiais do TSE por município e zona.

Compara (Brasil, sem exterior): votos de Lula e Flávio nos dois turnos, aptos, comparecimento,
abstenção, brancos e nulos. Os arquivos oficiais são independentes da base por seção.
Rodar da raiz do projeto: python -I scripts/06_conferencia_tse.py [pasta_candidato_munzona] [pasta_detalhe_munzona]
"""
import sys

import duckdb

CAND = sys.argv[1] if len(sys.argv) > 1 else "dados/votacao_candidato_munzona_2026"
DET = sys.argv[2] if len(sys.argv) > 2 else "dados/detalhe_votacao_munzona_2026"


def csv(path):
    return f"read_csv('{path}', delim=';', quote='\"', header=true, encoding='latin-1', all_varchar=true)"


con = duckdb.connect()
cand = csv(f"{CAND}/votacao_candidato_munzona_2026_BR.csv")
det = csv(f"{DET}/detalhe_votacao_munzona_2026_BR.csv")

oficial = con.sql(f"""
select 'oficial' as fonte, c.NR_TURNO::int as turno,
       sum(case when NR_CANDIDATO = '13' then QT_VOTOS_NOMINAIS::bigint end) as lula,
       sum(case when NR_CANDIDATO = '22' then QT_VOTOS_NOMINAIS::bigint end) as flavio
from {cand} c
where DS_CARGO = 'Presidente' and SG_UF != 'ZZ' group by 2
""").df()
det_of = con.sql(f"""
select NR_TURNO::int as turno, sum(QT_APTOS::bigint) as aptos, sum(QT_COMPARECIMENTO::bigint) as comparecimento,
       sum(QT_ABSTENCOES::bigint) as abstencao, sum(QT_VOTOS_BRANCOS::bigint) as brancos,
       sum(QT_TOTAL_VOTOS_NULOS::bigint) as nulos, sum(QT_VOTOS_NULOS_TECNICOS::bigint) as nulos_tecnicos
from {det} where DS_CARGO = 'Presidente' and SG_UF != 'ZZ' group by 1
""").df()
base = con.sql("""
select 1 as turno, sum(lula_t1) as lula, sum(flavio_t1) as flavio, sum(aptos_t1) as aptos, sum(aptos_t1 - abst_t1) as comparecimento,
       sum(abst_t1) as abstencao, sum(branco_t1) as brancos, sum(nulo_t1) as nulos
from 'saida/base_secao.parquet' where uf != 'ZZ'
union all
select 2, sum(lula_t2), sum(flavio_t2), sum(aptos_t2), sum(aptos_t2 - abst_t2), sum(abst_t2), sum(branco_t2), sum(nulo_t2)
from 'saida/base_secao.parquet' where uf != 'ZZ'
""").df()

print("== oficial (TSE, município x zona) ==")
print(oficial.merge(det_of, on="turno").sort_values("turno").set_index("turno").T.to_string())
print("\n== base por seção (usada no painel) ==")
print(base.set_index("turno").T.to_string())
print("\nObservação: no 1º turno o TSE separa 'nulos técnicos' dos nulos; na base por seção eles entram em 'eleitores dos"
      " candidatos eliminados' (0,004% dos votos), sem efeito nos totais nem na conta de fluxo dos votos.")
