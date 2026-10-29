"""Perfil do eleitorado (TSE) agregado por seção: sexo, faixa etária, escolaridade, cor/raça.

Saída: saida/perfil_secao.parquet (uma linha por UF + município + zona + seção, em contagens).
Rodar da raiz da pasta de análise: .venv/bin/python -I scripts/03_perfil_secao.py
"""
import duckdb

con = duckdb.connect()
ARQ = "dados/perfil_eleitor_secao_2026/perfil_eleitor_secao_2026_*.csv"

con.sql(f"""
create table perfil as
select
    SG_UF as uf,
    lpad(CD_MUNICIPIO, 5, '0') as cd_mun,
    NR_ZONA::int as zona,
    NR_SECAO::int as secao,
    sum(QT_ELEITORES::int) as eleitores,
    sum(case when DS_GENERO = 'FEMININO' then QT_ELEITORES::int else 0 end) as mulheres,
    sum(case when DS_GENERO = 'MASCULINO' then QT_ELEITORES::int else 0 end) as homens,
    -- faixas etárias (a faixa 'Inválida' fica fora de todas)
    sum(case when DS_FAIXA_ETARIA in ('16 anos', '17 anos') then QT_ELEITORES::int else 0 end) as idade_16_17,
    sum(case when DS_FAIXA_ETARIA in ('18 anos', '19 anos', '20 anos', '21 a 24 anos') then QT_ELEITORES::int else 0 end) as idade_18_24,
    sum(case when DS_FAIXA_ETARIA in ('25 a 29 anos', '30 a 34 anos') then QT_ELEITORES::int else 0 end) as idade_25_34,
    sum(case when DS_FAIXA_ETARIA in ('35 a 39 anos', '40 a 44 anos') then QT_ELEITORES::int else 0 end) as idade_35_44,
    sum(case when DS_FAIXA_ETARIA in ('45 a 49 anos', '50 a 54 anos', '55 a 59 anos') then QT_ELEITORES::int else 0 end) as idade_45_59,
    sum(case when DS_FAIXA_ETARIA in ('60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '80 a 84 anos',
                                      '85 a 89 anos', '90 a 94 anos', '95 a 99 anos', '100 anos ou mais') then QT_ELEITORES::int else 0 end) as idade_60_mais,
    -- escolaridade
    sum(case when DS_GRAU_ESCOLARIDADE in ('ANALFABETO', 'LÊ E ESCREVE') then QT_ELEITORES::int else 0 end) as esc_sem_instrucao,
    sum(case when DS_GRAU_ESCOLARIDADE in ('ENSINO FUNDAMENTAL INCOMPLETO', 'ENSINO FUNDAMENTAL COMPLETO') then QT_ELEITORES::int else 0 end) as esc_fundamental,
    sum(case when DS_GRAU_ESCOLARIDADE in ('ENSINO MÉDIO INCOMPLETO', 'ENSINO MÉDIO COMPLETO') then QT_ELEITORES::int else 0 end) as esc_medio,
    sum(case when DS_GRAU_ESCOLARIDADE in ('SUPERIOR INCOMPLETO', 'SUPERIOR COMPLETO') then QT_ELEITORES::int else 0 end) as esc_superior,
    -- cor/raça (muitos 'NÃO INFORMADO': usar só entre os informados)
    sum(case when DS_RACA_COR = 'Branca' then QT_ELEITORES::int else 0 end) as cor_branca,
    sum(case when DS_RACA_COR = 'Preta' then QT_ELEITORES::int else 0 end) as cor_preta,
    sum(case when DS_RACA_COR = 'Parda' then QT_ELEITORES::int else 0 end) as cor_parda,
    sum(case when DS_RACA_COR in ('Amarela', 'Indígena') then QT_ELEITORES::int else 0 end) as cor_amarela_indigena,
    sum(case when DS_RACA_COR = 'NÃO INFORMADO' then QT_ELEITORES::int else 0 end) as cor_nao_informada,
    sum(QT_ELEITORES_DEFICIENCIA::int) as deficiencia
from read_csv('{ARQ}', delim=';', quote='"', header=true, encoding='latin-1', all_varchar=true, union_by_name=true)
group by all
""")

print("valores de cor/raça:", con.sql(f"""
select distinct DS_RACA_COR from read_csv('{ARQ}', delim=';', quote='"', header=true, encoding='latin-1', all_varchar=true, union_by_name=true)
""").df().DS_RACA_COR.tolist())

print("\nseções no perfil:", con.sql("select count(*) from perfil").fetchone()[0])
print("\nconferência com a base de votos (eleitores do perfil x aptos do 2º turno):")
print(con.sql("""
select count(*) secoes_base,
       count(p.uf) secoes_com_perfil,
       sum(b.aptos_t2) aptos_t2,
       sum(p.eleitores) eleitores_perfil,
       sum(case when p.uf is null then b.aptos_t2 else 0 end) aptos_sem_perfil,
       round(avg(abs(p.eleitores - b.aptos_t2)), 2) dif_media_abs
from 'saida/base_secao.parquet' b
left join perfil p using (uf, cd_mun, zona, secao)
""").df().T.to_string())

print("\ncobertura de cor/raça informada:", con.sql("""
select round(100.0 * (1 - sum(cor_nao_informada) / sum(eleitores)), 1) from perfil
""").fetchone()[0], "%")

con.sql("copy perfil to 'saida/perfil_secao.parquet' (format parquet)")
