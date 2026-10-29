"""Monta a base por seção eleitoral: Lula x Flávio, 1º vs 2º turno.

Saída: saida/base_secao.parquet (uma linha por seção, colunas _t1/_t2 e deltas).
Rodar da raiz da pasta de análise: .venv/bin/python -I scripts/01_base_secao.py
"""
import duckdb

LULA, FLAVIO, BRANCO, NULO = "13", "22", "95", "96"

con = duckdb.connect()
con.sql("SET preserve_insertion_order=false")


def csv(path):
    return f"read_csv('{path}', delim=';', quote='\"', header=true, encoding='latin-1', all_varchar=true)"


VOTOS = csv("dados/votacao_secao_2026_BR/votacao_secao_2026_BR.csv")
DETALHE = csv("dados/detalhe_votacao_secao_2026/detalhe_votacao_secao_2026_BR.csv")
LOCAL = csv("dados/eleitorado_local_votacao_2026/eleitorado_local_votacao_2026_BRASIL.csv")

# chave da seção: UF + município (TSE, 5 dígitos) + zona + seção
con.sql(f"""
create table votos as
select
    NR_TURNO::int as turno,
    SG_UF as uf,
    lpad(CD_MUNICIPIO, 5, '0') as cd_mun,
    NR_ZONA::int as zona,
    NR_SECAO::int as secao,
    sum(case when NR_VOTAVEL = '{LULA}' then QT_VOTOS::int else 0 end) as lula,
    sum(case when NR_VOTAVEL = '{FLAVIO}' then QT_VOTOS::int else 0 end) as flavio,
    sum(case when NR_VOTAVEL = '{BRANCO}' then QT_VOTOS::int else 0 end) as branco,
    sum(case when NR_VOTAVEL = '{NULO}' then QT_VOTOS::int else 0 end) as nulo,
    sum(case when NR_VOTAVEL not in ('{LULA}', '{FLAVIO}', '{BRANCO}', '{NULO}')
             then QT_VOTOS::int else 0 end) as outros
from {VOTOS}
where DS_CARGO = 'Presidente'
group by all
""")

con.sql(f"""
create table detalhe as
select
    NR_TURNO::int as turno,
    SG_UF as uf,
    lpad(CD_MUNICIPIO, 5, '0') as cd_mun,
    NR_ZONA::int as zona,
    NR_SECAO::int as secao,
    sum(QT_APTOS::int) as aptos,
    sum(QT_COMPARECIMENTO::int) as comparecimento,
    sum(QT_ABSTENCOES::int) as abstencoes,
    max(ST_SECAO_INSTALADA) as instalada,
    max(ST_SECAO_ANULADA) as anulada,
    count(*) as linhas
from {DETALHE}
where DS_CARGO = 'Presidente'
group by all
""")

print("linhas detalhe por chave (1 = sem duplicata):")
print(con.sql("select linhas, count(*) from detalhe group by 1 order by 1").df().to_string())

con.sql("""
create table por_turno as
select
    d.turno, d.uf, d.cd_mun, d.zona, d.secao,
    d.aptos, d.comparecimento, d.abstencoes, d.instalada, d.anulada,
    coalesce(v.lula, 0) as lula, coalesce(v.flavio, 0) as flavio,
    coalesce(v.outros, 0) as outros, coalesce(v.branco, 0) as branco,
    coalesce(v.nulo, 0) as nulo
from detalhe d
left join votos v using (turno, uf, cd_mun, zona, secao)
""")

print("\nseções do detalhe sem votos (não instaladas/anuladas?):")
print(con.sql("""
select turno, instalada, anulada, count(*) secoes, sum(aptos) aptos,
       sum(lula + flavio + outros + branco + nulo) votos
from por_turno group by all order by all
""").df().to_string())

print("\nvotos que não casam com nenhuma seção do detalhe:")
print(con.sql("""
select v.turno, count(*) secoes, sum(v.lula + v.flavio + v.outros + v.branco + v.nulo) votos
from votos v anti join detalhe d using (turno, uf, cd_mun, zona, secao) group by 1
""").df().to_string())

print("\nconsistência comparecimento x votos (seções instaladas):")
print(con.sql("""
select turno, count(*) secoes,
       sum(comparecimento) comparecimento,
       sum(lula + flavio + outros + branco + nulo) votos,
       sum(case when comparecimento != lula + flavio + outros + branco + nulo then 1 else 0 end) secoes_divergentes
from por_turno where instalada = 'Sim' group by 1 order by 1
""").df().to_string())

# local de votação: snapshot do 2º turno (coordenadas, bairro, endereço)
con.sql(f"""
create table local as
select
    SG_UF as uf, lpad(CD_MUNICIPIO, 5, '0') as cd_mun, NR_ZONA::int as zona, NR_SECAO::int as secao,
    NR_LOCAL_VOTACAO::int as nr_local, NM_LOCAL_VOTACAO as nm_local,
    DS_ENDERECO as endereco, NM_BAIRRO as bairro, NR_CEP as cep, NM_MUNICIPIO as municipio,
    try_cast(replace(NR_LATITUDE, ',', '.') as double) as lat,
    try_cast(replace(NR_LONGITUDE, ',', '.') as double) as lon,
    DS_TIPO_SECAO_AGREGADA as tipo_secao
from {LOCAL}
where NR_TURNO = '2'
""")

print("\nlocal: linhas e chaves únicas (turno 2):")
print(con.sql("select count(*) linhas, count(distinct uf||cd_mun||zona||secao) chaves from local").df().to_string())
print(con.sql("""
select count(*) filter (where lat is null or lon is null or lat = 0 or lon = 0 or lat = -1 or lon = -1) sem_coord,
       count(*) total from local
""").df().to_string())

con.sql("""
create table base as
select
    t2.uf, t2.cd_mun, t2.zona, t2.secao,
    t1.aptos as aptos_t1, t2.aptos as aptos_t2,
    t1.comparecimento as comp_t1, t2.comparecimento as comp_t2,
    t1.abstencoes as abst_t1, t2.abstencoes as abst_t2,
    t1.lula as lula_t1, t2.lula as lula_t2,
    t1.flavio as flavio_t1, t2.flavio as flavio_t2,
    t1.outros as outros_t1, t2.outros as outros_t2,
    t1.branco as branco_t1, t2.branco as branco_t2,
    t1.nulo as nulo_t1, t2.nulo as nulo_t2,
    t2.lula - t1.lula as d_lula,
    t2.flavio - t1.flavio as d_flavio,
    t2.branco - t1.branco as d_branco,
    t2.nulo - t1.nulo as d_nulo,
    t2.abstencoes - t1.abstencoes as d_abst,
    t2.aptos - t1.aptos as d_aptos,
    t1.outros as outros_t1_eliminados,
    t2.instalada as instalada_t2, t1.instalada as instalada_t1
from (select * from por_turno where turno = 2) t2
join (select * from por_turno where turno = 1) t1 using (uf, cd_mun, zona, secao)
""")

print("\nseções em ambos os turnos:", con.sql("select count(*) from base").fetchone()[0])
print("só no T1:", con.sql("select count(*) from por_turno t1 anti join (select * from por_turno where turno=2) t2 using (uf,cd_mun,zona,secao) where t1.turno=1").fetchone()[0])
print("só no T2:", con.sql("select count(*) from por_turno t2 anti join (select * from por_turno where turno=1) t1 using (uf,cd_mun,zona,secao) where t2.turno=2").fetchone()[0])

con.sql("""
create table saida as
select b.*, l.nr_local, l.nm_local, l.endereco, l.bairro, l.cep, l.municipio, l.lat, l.lon, l.tipo_secao
from base b left join (select distinct * from local) l using (uf, cd_mun, zona, secao)
""")
print("\nseções sem local:", con.sql("select count(*) from saida where nr_local is null").fetchone()[0])

con.sql("copy saida to 'saida/base_secao.parquet' (format parquet)")
print("\nTotais nacionais (seções presentes nos dois turnos):")
print(con.sql("""
select sum(lula_t1) lula_t1, sum(lula_t2) lula_t2, sum(d_lula) d_lula,
       sum(flavio_t1) flavio_t1, sum(flavio_t2) flavio_t2, sum(d_flavio) d_flavio,
       sum(d_branco) d_branco, sum(d_nulo) d_nulo, sum(d_abst) d_abst,
       sum(outros_t1) outros_t1, sum(d_aptos) d_aptos
from saida
""").df().T.to_string())
