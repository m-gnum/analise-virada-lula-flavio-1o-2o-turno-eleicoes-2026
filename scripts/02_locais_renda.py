"""Cruza cada local de votação com os setores censitários do IBGE (renda do responsável).

Para cada local:
  - setor onde o ponto cai (renda do próprio setor);
  - média num raio de 1 km, ponderada por (responsáveis do setor x fração da área do setor dentro do raio).

Saída: saida/locais_renda.parquet
Rodar da raiz da pasta de análise: .venv/bin/python -I scripts/02_locais_renda.py
"""
import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely

RAIO_M = 1000
CRS_METROS = 5880  # SIRGAS 2000 / Brazil Polyconic

con = duckdb.connect()

# um registro por local de votação; coordenada = mediana das seções (descarta 0, -1 e fora do Brasil)
locais = con.sql("""
select
    uf, cd_mun, zona, nr_local,
    any_value(nm_local) as nm_local, any_value(municipio) as municipio,
    any_value(bairro) as bairro, any_value(cep) as cep, any_value(endereco) as endereco,
    median(lat) filter (where lat between -34 and 6 and lon between -74 and -34) as lat,
    median(lon) filter (where lat between -34 and 6 and lon between -74 and -34) as lon,
    count(*) as secoes
from 'saida/base_secao.parquet'
where uf != 'ZZ'
group by uf, cd_mun, zona, nr_local
""").df()
print("locais:", len(locais), "| sem coordenada válida:", int(locais.lat.isna().sum()))

renda = pd.read_csv(
    "dados/Agregados_por_setores_renda_responsavel_BR_20260508_csv/Agregados_por_setores_renda_responsavel_BR.csv",
    sep=";", encoding="latin-1", dtype=str,
)
for c in ["V06001", "V06002", "V06004", "V06006"]:
    renda[c] = pd.to_numeric(renda[c], errors="coerce")
renda = renda.rename(columns={"V06001": "resp", "V06002": "moradores", "V06004": "renda_media", "V06006": "renda_mediana"})
renda = renda[["CD_SETOR", "resp", "moradores", "renda_media", "renda_mediana"]]
print("setores com renda média:", int(renda.renda_media.notna().sum()), "de", len(renda))

pts_ok = locais.dropna(subset=["lat", "lon"]).copy()
resultados = []

for uf, g in pts_ok.groupby("uf"):
    pts = gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g.lon, g.lat), crs=4674)
    minx, miny, maxx, maxy = pts.total_bounds
    pad = 0.02  # ~2 km
    secs = pyogrio.read_dataframe(
        "BR_setores_CD2022.gpkg",
        columns=["CD_SETOR", "SITUACAO", "NM_BAIRRO", "AREA_KM2"],
        bbox=(minx - pad, miny - pad, maxx + pad, maxy + pad),
    )
    secs = secs.merge(renda, on="CD_SETOR", how="left").to_crs(CRS_METROS).reset_index(drop=True)
    secs["area_m2"] = secs.geometry.area
    pts = pts.to_crs(CRS_METROS).reset_index(drop=True)

    # setor onde o ponto cai
    casa = gpd.sjoin(pts[["geometry"]], secs[["geometry", "CD_SETOR", "SITUACAO", "NM_BAIRRO", "renda_media", "renda_mediana", "resp"]],
                     predicate="within", how="left")
    casa = casa[~casa.index.duplicated(keep="first")]

    # média ponderada no raio de 1 km
    buf = pts[["geometry"]].copy()
    buf["geometry"] = buf.buffer(RAIO_M)
    par = gpd.sjoin(buf, secs[["geometry"]], predicate="intersects", how="inner")
    esq = par.index.to_numpy()
    dir_ = par["index_right"].to_numpy()
    inter = shapely.area(shapely.intersection(buf.geometry.values[esq], secs.geometry.values[dir_]))
    frac = inter / secs.area_m2.values[dir_]
    p = pd.DataFrame({
        "i": esq,
        "peso": secs.resp.values[dir_] * frac,
        "renda": secs.renda_media.values[dir_],
        "mediana": secs.renda_mediana.values[dir_],
    })
    p = p[p.peso.notna() & (p.peso > 0) & p.renda.notna()]
    agg = p.groupby("i").apply(
        lambda d: pd.Series({
            "renda_media_1km": np.average(d.renda, weights=d.peso),
            "renda_mediana_1km": np.average(d["mediana"].fillna(d.renda), weights=d.peso),
            "resp_1km": d.peso.sum(),
        })
    )

    out = g.reset_index(drop=True).copy()
    out["cd_setor"] = casa["CD_SETOR"].values
    out["situacao_setor"] = casa["SITUACAO"].values
    out["bairro_ibge"] = casa["NM_BAIRRO"].values
    out["renda_media_setor"] = casa["renda_media"].values
    out["renda_mediana_setor"] = casa["renda_mediana"].values
    out = out.join(agg)
    resultados.append(out)
    print(f"{uf}: {len(out)} locais | no setor: {out.cd_setor.notna().mean():.1%} | com renda 1km: {out.renda_media_1km.notna().mean():.1%}", flush=True)

res = pd.concat(resultados, ignore_index=True)
sem = locais[locais.lat.isna()].copy()
res = pd.concat([res, sem], ignore_index=True)
res.to_parquet("saida/locais_renda.parquet", index=False)
print("\ntotal locais:", len(res), "| com renda 1km:", int(res.renda_media_1km.notna().sum()))
