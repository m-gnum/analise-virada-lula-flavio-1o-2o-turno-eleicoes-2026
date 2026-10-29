"""Gera index.html (dashboard em arquivo único) e, se existir a base por seção, o CSV por seção.

Lê saida/locais_dashboard.parquet, embute os dados compactados
(gzip + base64) no modelo scripts/dashboard_template.html.
Rodar da raiz da pasta de análise: .venv/bin/python -I scripts/05_dashboard.py
"""
import base64
import gzip
import json

import duckdb
import numpy as np
import pandas as pd

loc = pd.read_parquet("saida/locais_dashboard.parquet")
loc = loc.sort_values(["uf", "municipio", "cd_mun", "zona", "nr_local"]).reset_index(drop=True)

ufs = sorted(loc.uf.unique())
mun_chave = loc[["uf", "cd_mun", "municipio"]].drop_duplicates(["uf", "cd_mun"]).reset_index(drop=True)
# segurança pública (script 07): vítimas de CVLI nos últimos 12 meses e população do Censo 2022, por município
seg = pd.read_parquet("saida/seguranca_municipio.parquet")[["uf", "cd_mun", "cvli_12m", "pop_2022"]]
mun_chave = mun_chave.merge(seg, on=["uf", "cd_mun"], how="left")
mun_idx = {(r.uf, r.cd_mun): i for i, r in mun_chave.iterrows()}
bairros = sorted(loc.bairro.fillna("").str.strip().str.upper().unique())
bai_idx = {b: i for i, b in enumerate(bairros)}


def ints(s, nulo=0):
    return s.fillna(nulo).round().astype(int).tolist()


cols = {
    "uf": loc.uf.map({u: i for i, u in enumerate(ufs)}).tolist(),
    "mun": [mun_idx[(u, c)] for u, c in zip(loc.uf, loc.cd_mun)],
    "bai": loc.bairro.fillna("").str.strip().str.upper().map(bai_idx).tolist(),
    "lat": loc.lat.fillna(0).round(5).tolist(),
    "lon": loc.lon.fillna(0).round(5).tolist(),
    "ca": ints(loc.coord_aprox),
    "sec": ints(loc.secoes),
    "ap": ints(loc.aptos),
    "ab1": ints(loc.abst_t1), "ab2": ints(loc.abst_t2),
    "l1": ints(loc.lula_t1), "l2": ints(loc.lula_t2),
    "f1": ints(loc.flavio_t1), "f2": ints(loc.flavio_t2),
    "o1": ints(loc.outros_t1),
    "b1": ints(loc.branco_t1), "b2": ints(loc.branco_t2),
    "n1": ints(loc.nulo_t1), "n2": ints(loc.nulo_t2),
    "pe": ints(loc.perf_eleitores),
    "mu": ints(loc.mulheres),
    "i1": ints(loc.idade_16_24), "i2": ints(loc.idade_25_44), "i3": ints(loc.idade_45_59), "i4": ints(loc.idade_60_mais),
    "e0": ints(loc.esc_sem_instrucao), "e1": ints(loc.esc_fundamental), "e2": ints(loc.esc_medio), "e3": ints(loc.esc_superior),
    "rd": ints(loc.renda_media_1km, nulo=-1),
}
dados = {
    "ufs": ufs,
    "muns": [
        [r.municipio, ufs.index(r.uf), -1 if pd.isna(r.cvli_12m) else int(r.cvli_12m), 0 if pd.isna(r.pop_2022) else int(r.pop_2022)]
        for r in mun_chave.itertuples()
    ],
    "bairros": bairros,
    "nm": loc.nm_local.fillna("").tolist(),
    "c": cols,
}

bruto = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
comp = gzip.compress(bruto, 9)
b64 = base64.b64encode(comp).decode("ascii")
print(f"dados: {len(bruto)/1e6:.1f} MB -> gzip+base64 {len(b64)/1e6:.1f} MB | locais {len(loc)}")

html = open("scripts/dashboard_template.html", encoding="utf-8").read()
assert "__DADOS_B64__" in html
open("index.html", "w", encoding="utf-8").write(html.replace("__DADOS_B64__", b64))
print("index.html gerado")

# CSV por seção (para quem quiser a base completa); só roda se a saída do script 04 estiver na pasta
import os

if not os.path.exists("saida/secao_analise.parquet"):
    print("saida/secao_analise.parquet não encontrado: CSV por seção não gerado")
    raise SystemExit
con = duckdb.connect()
con.sql("""
copy (
  select uf as UF, cd_mun as COD_MUNICIPIO_TSE, municipio as MUNICIPIO, zona as ZONA, secao as SECAO,
         nr_local as LOCAL_VOTACAO, nm_local as NOME_LOCAL, bairro as BAIRRO_TSE, endereco as ENDERECO,
         lat as LATITUDE, lon as LONGITUDE,
         aptos_t2 as APTOS,
         lula_t1 as LULA_1T, lula_t2 as LULA_2T, d_lula as DELTA_LULA,
         flavio_t1 as FLAVIO_1T, flavio_t2 as FLAVIO_2T, d_flavio as DELTA_FLAVIO,
         outros_t1 as ELIMINADOS_1T, branco_t1 as BRANCOS_1T, branco_t2 as BRANCOS_2T, d_branco as DELTA_BRANCOS,
         nulo_t1 as NULOS_1T, nulo_t2 as NULOS_2T, d_nulo as DELTA_NULOS,
         abst_t1 as ABSTENCAO_1T, abst_t2 as ABSTENCAO_2T, d_abst as DELTA_ABSTENCAO,
         renda_media_1km as RENDA_MEDIA_RESP_1KM
  from 'saida/secao_analise.parquet'
  order by uf, municipio, zona, secao
) to 'saida/secoes_variacao_votos.csv' (header, delimiter ';')
""")
print("csv por seção gerado")
