"""Junta votos + perfil do eleitorado + renda e roda a análise de perfil.

Saídas (em saida/):
  secao_analise.parquet     uma linha por seção, com percentuais e deltas em p.p. dos aptos
  locais_dashboard.parquet  uma linha por local de votação (contagens), usada pelo dashboard
  analise_perfil.json       quintis, comparação perdeu x ganhou e regressão (Brasil)
Rodar da raiz da pasta de análise: .venv/bin/python -I scripts/04_analise.py
"""
import json

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

REGIAO = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
    "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul", "ZZ": "Exterior",
}

con = duckdb.connect()

# ------------------------------------------------------------------ seção
con.sql("""
create table secao as
select
    b.*,
    p.eleitores as perf_eleitores, p.mulheres,
    p.idade_16_17 + p.idade_18_24 as idade_16_24,
    p.idade_25_34 + p.idade_35_44 as idade_25_44,
    p.idade_45_59, p.idade_60_mais,
    p.esc_sem_instrucao, p.esc_fundamental, p.esc_medio, p.esc_superior,
    r.renda_media_1km, r.renda_mediana_1km, r.renda_media_setor, r.situacao_setor
from 'saida/base_secao.parquet' b
left join 'saida/perfil_secao.parquet' p using (uf, cd_mun, zona, secao)
left join 'saida/locais_renda.parquet' r using (uf, cd_mun, zona, nr_local)
""")
df = con.sql("select * from secao").df()
df["regiao"] = df.uf.map(REGIAO)
print("seções:", len(df), "| com perfil:", int(df.perf_eleitores.notna().sum()),
      "| com renda:", int(df.renda_media_1km.notna().sum()))

# variações em pontos percentuais dos aptos (o denominador é o mesmo nos dois turnos)
ap = df.aptos_t2.replace(0, np.nan)
for c in ["lula", "flavio", "branco", "nulo", "abst"]:
    df[f"pp_{c}"] = df[f"d_{c}"] / ap * 100
df["pp_branco_nulo"] = df.pp_branco + df.pp_nulo
df["pp_eliminados"] = -df.outros_t1 / ap * 100  # saída dos votos dos candidatos eliminados
# participação entre os que compareceram
df["pct_lula_t1"] = df.lula_t1 / (df.lula_t1 + df.flavio_t1 + df.outros_t1) * 100
df["pct_lula_t2"] = df.lula_t2 / (df.lula_t2 + df.flavio_t2) * 100

pe = df.perf_eleitores.replace(0, np.nan)
for c in ["mulheres", "idade_16_24", "idade_25_44", "idade_45_59", "idade_60_mais",
          "esc_sem_instrucao", "esc_fundamental", "esc_medio", "esc_superior"]:
    df[f"sh_{c}"] = df[c] / pe * 100
df["ln_renda"] = np.log(df.renda_media_1km)

df.to_parquet("saida/secao_analise.parquet", index=False)

# ------------------------------------------------------------------ locais (dashboard)
loc = con.sql("""
select
    s.uf, s.cd_mun, s.zona, s.nr_local,
    any_value(s.nm_local) as nm_local, any_value(s.municipio) as municipio,
    any_value(s.bairro) as bairro,
    count(*) as secoes,
    sum(aptos_t1) as aptos, sum(abst_t1) as abst_t1, sum(abst_t2) as abst_t2,
    sum(lula_t1) as lula_t1, sum(lula_t2) as lula_t2,
    sum(flavio_t1) as flavio_t1, sum(flavio_t2) as flavio_t2,
    sum(outros_t1) as outros_t1,
    sum(branco_t1) as branco_t1, sum(branco_t2) as branco_t2,
    sum(nulo_t1) as nulo_t1, sum(nulo_t2) as nulo_t2,
    sum(perf_eleitores) as perf_eleitores, sum(mulheres) as mulheres,
    sum(idade_16_24) as idade_16_24, sum(idade_25_44) as idade_25_44,
    sum(idade_45_59) as idade_45_59, sum(idade_60_mais) as idade_60_mais,
    sum(esc_sem_instrucao) as esc_sem_instrucao, sum(esc_fundamental) as esc_fundamental,
    sum(esc_medio) as esc_medio, sum(esc_superior) as esc_superior,
    any_value(renda_media_1km) as renda_media_1km,
    median(case when s.lat between -34 and 6 and s.lon between -74 and -34 then s.lat end) as lat,
    median(case when s.lat between -34 and 6 and s.lon between -74 and -34 then s.lon end) as lon
from secao s
where s.uf != 'ZZ'
group by s.uf, s.cd_mun, s.zona, s.nr_local
""").df()
loc["regiao"] = loc.uf.map(REGIAO)

# local sem coordenada: usa o centro (ponderado por aptos) do próprio município, marcado como aproximado
ok = loc.dropna(subset=["lat", "lon"])
cen = ok.groupby(["uf", "cd_mun"]).apply(
    lambda d: pd.Series({"clat": np.average(d.lat, weights=d.aptos.clip(lower=1)),
                         "clon": np.average(d.lon, weights=d.aptos.clip(lower=1))}),
    include_groups=False,
).reset_index()
loc = loc.merge(cen, on=["uf", "cd_mun"], how="left")
loc["coord_aprox"] = (loc.lat.isna() & loc.clat.notna()).astype(int)
loc["lat"] = loc.lat.fillna(loc.clat)
loc["lon"] = loc.lon.fillna(loc.clon)
loc = loc.drop(columns=["clat", "clon"])
print("locais:", len(loc), "| sem coordenada nem no município:", int(loc.lat.isna().sum()),
      "| coordenada aproximada:", int(loc.coord_aprox.sum()))
loc.to_parquet("saida/locais_dashboard.parquet", index=False)

# ------------------------------------------------------------------ análise de perfil (Brasil)
a = df[(df.instalada_t2 == "Sim") & (df.instalada_t1 == "Sim") & df.aptos_t2.gt(0)
       & df.perf_eleitores.gt(0) & df.renda_media_1km.notna() & df.uf.ne("ZZ")].copy()
print("seções na análise de perfil:", len(a), "de", len(df))

VARS = {
    "sh_mulheres": "% mulheres",
    "sh_idade_16_24": "% 16 a 24 anos",
    "sh_idade_25_44": "% 25 a 44 anos",
    "sh_idade_45_59": "% 45 a 59 anos",
    "sh_idade_60_mais": "% 60 anos ou mais",
    "sh_esc_sem_instrucao": "% sem instrução (analfabeto / lê e escreve)",
    "sh_esc_fundamental": "% ensino fundamental",
    "sh_esc_medio": "% ensino médio",
    "sh_esc_superior": "% ensino superior",
    "renda_media_1km": "Renda média do responsável (raio 1 km)",
}
RESP = ["pp_lula", "pp_flavio", "pp_eliminados", "pp_branco_nulo", "pp_abst"]


def quintis(d, var, k=5):
    """Quintis de seções ponderados pelos aptos; média ponderada de cada resposta em cada quintil."""
    d = d.sort_values(var)
    cw = d.aptos_t2.cumsum() / d.aptos_t2.sum()
    d["q"] = np.minimum((cw * k).astype(int), k - 1) + 1
    out = []
    for q, g in d.groupby("q"):
        w = g.aptos_t2
        linha = {"q": int(q), "secoes": int(len(g)), "aptos": int(w.sum()),
                 "valor": float(np.average(g[var], weights=w))}
        for r in RESP:
            linha[r] = float(np.average(g[r], weights=w))
        out.append(linha)
    return out


res = {"n_secoes": int(len(a)), "quintis": {}, "perdeu_ganhou": {}, "regressao": {}}
for v, rot in VARS.items():
    res["quintis"][v] = {"rotulo": rot, "linhas": quintis(a, v)}

# perfil das seções onde cada candidato mais perdeu e mais ganhou (decis extremos de pp)
for cand in ["lula", "flavio"]:
    y = f"pp_{cand}"
    d = a.sort_values(y)
    cw = d.aptos_t2.cumsum() / d.aptos_t2.sum()
    grupos = {"perdeu_mais (10% piores)": d[cw <= 0.1], "ganhou_mais (10% melhores)": d[cw > 0.9],
              "todas": d}
    # seções em que o candidato perdeu votos em termos absolutos
    perd = a[a[f"d_{cand}"] < 0]
    res["perdeu_ganhou"][cand] = {
        "secoes_com_perda": int(len(perd)),
        "pct_secoes_com_perda": float(len(perd) / len(a) * 100),
        "votos_perdidos": int(-perd[f"d_{cand}"].sum()),
        "grupos": {},
    }
    for nome, g in grupos.items():
        w = g.aptos_t2
        res["perdeu_ganhou"][cand]["grupos"][nome] = {
            "secoes": int(len(g)),
            "media_pp": float(np.average(g[y], weights=w)),
            **{v: float(np.average(g[v], weights=w)) for v in VARS},
        }

# regressão: Δ em p.p. dos aptos ~ perfil + log(renda) + efeitos fixos de UF, WLS por aptos, erro por município
X_VARS = ["sh_mulheres", "sh_idade_16_24", "sh_idade_25_44", "sh_idade_60_mais",
          "sh_esc_sem_instrucao", "sh_esc_superior", "ln_renda"]
Z = a[X_VARS].copy()
Z = (Z - Z.mean()) / Z.std()
uf_d = pd.get_dummies(a.uf, prefix="uf", drop_first=True, dtype=float)
XM = sm.add_constant(pd.concat([Z, uf_d], axis=1))
grp = (a.uf + a.cd_mun).astype("category").cat.codes
for y in RESP:
    m = sm.WLS(a[y], XM, weights=a.aptos_t2).fit(cov_type="cluster", cov_kwds={"groups": grp})
    res["regressao"][y] = {
        "r2": float(m.rsquared),
        "coef": {v: {"beta": float(m.params[v]), "ep": float(m.bse[v]), "p": float(m.pvalues[v])} for v in X_VARS},
    }
    print(y, "R2=%.3f" % m.rsquared, {v: round(float(m.params[v]), 3) for v in X_VARS})

res["rotulos_x"] = {
    "sh_mulheres": "% mulheres", "sh_idade_16_24": "% 16 a 24 anos", "sh_idade_25_44": "% 25 a 44 anos",
    "sh_idade_60_mais": "% 60 anos ou mais", "sh_esc_sem_instrucao": "% sem instrução",
    "sh_esc_superior": "% ensino superior", "ln_renda": "Renda do responsável (log)",
}
with open("saida/analise_perfil.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("ok")
