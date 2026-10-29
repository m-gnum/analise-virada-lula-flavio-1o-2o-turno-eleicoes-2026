"""Análise estatística da variação de votos (Lula e Flávio) entre o 1º e o 2º turno.

Entrada:  saida/locais_dashboard.parquet, saida/seguranca_municipio.parquet
Saída:    saida/estatistica.json (resultados embutidos no bloco "Análise Estatística" do painel)
Rodar da raiz do projeto: .venv/bin/python -I scripts/08_analise_estatistica.py

Desenho (definido antes de rodar, para não "pescar" resultados):
  resposta   variação em p.p. dos aptos, por candidato (Lula, Flávio)
  explicativas  log da renda, % ensino superior, % sem instrução, % 60+, % 16-24, % mulheres (+ CVLI no modelo entre cidades)
  A) simples    uma variável por vez, ponderado por aptos, erro-padrão agrupado por município
  B) ajustado   todas juntas, mesma ponderação
  C) dentro da cidade  efeito fixo de município (compara locais da mesma cidade)
  D) entre cidades     município como unidade (aptos como peso), com CVLI, erro-padrão agrupado por UF
  Efeito = variação em p.p. para +1 desvio-padrão da variável (desvio ponderado por aptos).
  Holm dentro de cada modelo/recorte. Interação renda x região (teste conjunto). Moran I global (kNN=8, permutação) e LISA por município.
"""
import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import sparse
from scipy.spatial import cKDTree
from scipy.stats import f as f_dist

warnings.simplefilter("ignore", FutureWarning)
rng = np.random.default_rng(2026)
MIN_APTOS = 100
REGIOES = ["Brasil", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
CAND = {"lula": ("lula_t1", "lula_t2"), "flavio": ("flavio_t1", "flavio_t2")}
VARS = {  # chave: (rótulo, função sobre o dataframe)
    "renda": "Renda média do responsável (log)",
    "superior": "% com ensino superior",
    "sem_instr": "% sem instrução",
    "idade60": "% com 60 anos ou mais",
    "idade16": "% de 16 a 24 anos",
    "mulheres": "% de mulheres",
}
VARS_MUN = {**VARS, "cvli": "Taxa de CVLI (log)"}

d = pd.read_parquet("saida/locais_dashboard.parquet")
sg = pd.read_parquet("saida/seguranca_municipio.parquet")[["uf", "cd_mun", "taxa_cvli_100k"]]
d = d.merge(sg, on=["uf", "cd_mun"], how="left")
d["mun"] = d.uf + "|" + d.cd_mun.astype(str)
for c, (a, b) in CAND.items():
    d[f"dpp_{c}"] = (d[b] - d[a]) / d.aptos * 100
p = d.perf_eleitores
d["renda"] = np.log(d.renda_media_1km)
d["superior"] = d.esc_superior / p * 100
d["sem_instr"] = d.esc_sem_instrucao / p * 100
d["idade60"] = d.idade_60_mais / p * 100
d["idade16"] = d.idade_16_24 / p * 100
d["mulheres"] = d.mulheres / p * 100
d["cvli"] = np.log1p(d.taxa_cvli_100k)

N_TOTAL = len(d)
base = d[(d.aptos >= MIN_APTOS)].dropna(subset=list(VARS) + ["dpp_lula", "dpp_flavio"]).copy()
print(f"locais: {N_TOTAL} | na análise (aptos>={MIN_APTOS}, com perfil e renda): {len(base)}")


def wz(df, cols, w):
    """Padroniza (média e desvio ponderados por w)."""
    out = {}
    for c in cols:
        m = np.average(df[c], weights=w)
        s = np.sqrt(np.average((df[c] - m) ** 2, weights=w))
        out[c] = (df[c] - m) / s
    return pd.DataFrame(out, index=df.index)


def holm(ps):
    ps = np.asarray(ps)
    o = np.argsort(ps)
    adj = np.empty(len(ps))
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (len(ps) - r) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def ajustar(y, X, w, grupos, nomes):
    X = sm.add_constant(X)
    res = sm.WLS(y, X, weights=w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(grupos)[0]})
    ci = res.conf_int()
    out = {}
    for n in nomes:
        out[n] = {"b": float(res.params[n]), "lo": float(ci.loc[n, 0]), "hi": float(ci.loc[n, 1]), "p": float(res.pvalues[n])}
    return out, res


def com_holm(coefs):
    ks = list(coefs)
    adj = holm([coefs[k]["p"] for k in ks])
    for k, a in zip(ks, adj):
        coefs[k]["p_holm"] = float(a)
    return coefs


def modelos(sub, cands_y, vars_, tem_cvli=False):
    """Simples, ajustado e efeito fixo para um recorte."""
    w = sub.aptos
    Z = wz(sub, list(vars_), w)
    res = {}
    for c in cands_y:
        y = sub[f"dpp_{c}"]
        simples = {}
        for v in vars_:
            simples[v] = ajustar(y, Z[[v]], w, sub.mun, [v])[0][v]
        aj, rf = ajustar(y, Z, w, sub.mun, list(vars_))
        # efeito fixo de município: demeaning ponderado dentro do município
        g = sub.mun
        cnt = g.map(g.value_counts())
        s2 = sub[cnt > 1]
        w2 = s2.aptos
        Z2 = Z.loc[s2.index]
        y2 = y.loc[s2.index]
        wm = w2.groupby(s2.mun).transform("sum")
        dm = lambda s: s - (s * w2).groupby(s2.mun).transform("sum") / wm
        Zd = pd.DataFrame({v: dm(Z2[v]) for v in vars_})
        yd = dm(y2)
        fe, rfe = ajustar(yd, Zd, w2, s2.mun, list(vars_))
        res[c] = {
            "simples": com_holm(simples),
            "ajustado": com_holm(aj),
            "dentro": com_holm(fe),
            "n": int(len(sub)),
            "n_mun": int(sub.mun.nunique()),
            "n_fe": int(len(s2)),
            "r2": float(rf.rsquared),
            "r2_dentro": float(rfe.rsquared),
        }
    return res, Z


def teste_interacao(sub, c):
    """Teste conjunto: o efeito da renda (ajustado) muda por região? (Wald agrupado por município)"""
    w = sub.aptos
    Z = wz(sub, list(VARS), w)
    R = pd.get_dummies(sub.regiao, drop_first=True).astype(float)
    X = Z.copy()
    inter = []
    for r in R.columns:
        X[f"renda_x_{r}"] = Z["renda"] * R[r]
        inter.append(f"renda_x_{r}")
    X = pd.concat([X, R], axis=1)
    X = sm.add_constant(X)
    res = sm.WLS(sub[f"dpp_{c}"], X, weights=w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.mun)[0]})
    A = np.zeros((len(inter), len(res.params)))
    for i, n in enumerate(inter):
        A[i, list(res.params.index).index(n)] = 1
    t = res.wald_test(A, scalar=True)
    return {"F": float(t.statistic), "p": float(t.pvalue), "gl": len(inter)}


# ------------------------- modelos A, B e C por recorte -------------------------
out = {
    "meta": {
        "n_locais": int(N_TOTAL),
        "n_analise": int(len(base)),
        "min_aptos": MIN_APTOS,
        "variaveis": VARS,
        "variaveis_mun": VARS_MUN,
    },
    "reg": {},
    "mun": {},
    "corr": {},
    "interacao": {},
    "moran": {},
}
cands = ["lula", "flavio"]
# escala da resposta: média e desvio-padrão (ponderados por aptos) da variação em p.p., para dar noção de tamanho aos efeitos
out["meta"]["escala"] = {}
for reg in REGIOES:
    sub = base if reg == "Brasil" else base[base.regiao == reg]
    out["meta"]["escala"][reg] = {
        c: {"media": float(np.average(sub[f"dpp_{c}"], weights=sub.aptos)), "dp": float(np.sqrt(np.average((sub[f"dpp_{c}"] - np.average(sub[f"dpp_{c}"], weights=sub.aptos)) ** 2, weights=sub.aptos)))}
        for c in ["lula", "flavio"]
    }
for reg in REGIOES:
    sub = base if reg == "Brasil" else base[base.regiao == reg]
    out["reg"][reg], Z = modelos(sub, cands, VARS)
    print(reg, {c: round(out["reg"][reg][c]["ajustado"]["renda"]["b"], 3) for c in cands}, "n=", len(sub))

# correlação entre explicativas e VIF (Brasil, só os dados da análise)
Zb = wz(base, list(VARS), base.aptos)
cm = Zb.corr()
out["corr"]["matriz"] = {a: {b: float(cm.loc[a, b]) for b in VARS} for a in VARS}
Xv = sm.add_constant(Zb)
out["corr"]["vif"] = {v: float(1 / (1 - sm.OLS(Zb[v], sm.add_constant(Zb.drop(columns=v))).fit().rsquared)) for v in VARS}
print("VIF:", {k: round(v, 2) for k, v in out["corr"]["vif"].items()})

for c in cands:
    out["interacao"][c] = teste_interacao(base, c)
print("interação renda x região:", out["interacao"])

# ------------------------- modelo D: entre cidades (com CVLI) -------------------------
g = base.groupby(["uf", "cd_mun"])
mun = pd.DataFrame({"aptos": g.aptos.sum(), "taxa": g.taxa_cvli_100k.first(), "lat": g.apply(lambda x: np.average(x.lat.fillna(x.lat.mean()), weights=x.aptos)), "lon": g.apply(lambda x: np.average(x.lon.fillna(x.lon.mean()), weights=x.aptos)), "regiao": g.regiao.first(), "nome": g.municipio.first(), "n_locais": g.size()})
for c in cands:
    mun[f"dpp_{c}"] = g.apply(lambda x: (x[CAND[c][1]].sum() - x[CAND[c][0]].sum()) / x.aptos.sum() * 100)
for v in VARS:
    mun[v] = g.apply(lambda x: np.average(x[v], weights=x.aptos))
mun["cvli"] = np.log1p(mun.taxa)
mun = mun.reset_index()
mun["uf_"] = mun.uf
md = mun.dropna(subset=list(VARS_MUN) + ["dpp_lula"]).copy()
print(f"municípios no modelo entre cidades: {len(md)} de {len(mun)}")
for reg in REGIOES:
    sub = md if reg == "Brasil" else md[md.regiao == reg]
    if len(sub) < 30:
        continue
    Zm = wz(sub, list(VARS_MUN), sub.aptos)
    o = {"n": int(len(sub))}
    for c in cands:
        y = sub[f"dpp_{c}"]
        simples = {v: ajustar(y, Zm[[v]], sub.aptos, sub.uf, [v])[0][v] for v in VARS_MUN}
        aj, r = ajustar(y, Zm, sub.aptos, sub.uf, list(VARS_MUN))
        o[c] = {"simples": com_holm(simples), "ajustado": com_holm(aj), "r2": float(r.rsquared)}
    out["mun"][reg] = o
    print("entre cidades", reg, {c: round(o[c]["ajustado"]["cvli"]["b"], 3) for c in cands}, "n=", len(sub))


# ------------------------- Moran I e LISA -------------------------
def vizinhos(lat, lon, k=8):
    xy = np.c_[lat, lon * np.cos(np.radians(lat))]
    tree = cKDTree(xy)
    dist, idx = tree.query(xy, k=k + 1)
    n = len(xy)
    rows = np.repeat(np.arange(n), k)
    W = sparse.csr_matrix((np.ones(n * k) / k, (rows, idx[:, 1:].ravel())), shape=(n, n))
    return W


def moran(z, W, perms=499):
    z = np.asarray(z, float)
    z = z - z.mean()
    n = len(z)
    S0 = W.sum()
    I = n / S0 * (z @ (W @ z)) / (z @ z)
    sims = np.empty(perms)
    for i in range(perms):
        zp = rng.permutation(z)
        sims[i] = n / S0 * (zp @ (W @ zp)) / (zp @ zp)
    p = (1 + (sims >= I).sum()) / (perms + 1)
    return float(I), float(p), float(sims.mean()), float(sims.std())


def lisa(z, W, perms=499):
    z = np.asarray(z, float)
    z = (z - z.mean()) / z.std()
    lag = W @ z
    I = z * lag
    n = len(z)
    k = int(W.getnnz(axis=1).max())
    pv = np.empty(n)
    for i in range(n):
        others = np.delete(z, i)
        samp = rng.choice(others, size=(perms, k))
        sim = z[i] * samp.mean(axis=1)
        # cauda superior para associação positiva (alto-alto, baixo-baixo), inferior para negativa (alto-baixo, baixo-alto)
        pv[i] = (1 + ((sim >= I[i]) if I[i] >= 0 else (sim <= I[i])).sum()) / (perms + 1)
    return z, lag, I, pv


loc_ok = base[(base.coord_aprox == 0) & base.lat.notna() & base.lon.notna()]
for reg in REGIOES:
    sub = loc_ok if reg == "Brasil" else loc_ok[loc_ok.regiao == reg]
    W = vizinhos(sub.lat.values, sub.lon.values)
    o = {"n": int(len(sub))}
    for c in cands:
        z = sub[f"dpp_{c}"].values
        I, p, mu, sd = moran(z, W)
        o[c] = {"I": I, "p": p, "esperado": mu}
    # resíduos do modelo ajustado (sem efeito fixo): a variação real menos a prevista só pelo perfil, ou seja, o que sobra depois do perfil
    Zs = wz(sub, list(VARS), sub.aptos)
    for c in cands:
        y = sub[f"dpp_{c}"]
        X = sm.add_constant(Zs)
        r = sm.WLS(y, X, weights=sub.aptos).fit()
        I, p, mu, sd = moran(r.resid.values, W)
        o[c]["I_resid"] = I
        o[c]["p_resid"] = p
    out["moran"][reg] = o
    print("Moran", reg, {c: (round(o[c]["I"], 3), round(o[c]["I_resid"], 3)) for c in cands}, "n=", len(sub))

# LISA por município (todos os municípios com coordenada)
mm = mun.dropna(subset=["lat", "lon"]).reset_index(drop=True)
Wm = vizinhos(mm.lat.values, mm.lon.values)
lisa_out = {"lat": [round(float(x), 3) for x in mm.lat], "lon": [round(float(x), 3) for x in mm.lon], "nome": [f"{n}/{u}" for n, u in zip(mm.nome, mm.uf)], "aptos": [int(x) for x in mm.aptos]}
for c in cands:
    z, lag, I, pv = lisa(mm[f"dpp_{c}"].values, Wm)
    # 1=alto-alto 2=baixo-baixo 3=alto-baixo 4=baixo-alto 0=não significativo (p<0,01)
    cl = np.zeros(len(z), int)
    sig = pv < 0.01
    cl[sig & (z > 0) & (lag > 0)] = 1
    cl[sig & (z < 0) & (lag < 0)] = 2
    cl[sig & (z > 0) & (lag < 0)] = 3
    cl[sig & (z < 0) & (lag > 0)] = 4
    lisa_out[c] = {"cl": cl.tolist(), "v": [round(float(x), 2) for x in mm[f"dpp_{c}"]]}
    print("LISA", c, {k: int((cl == k).sum()) for k in range(5)})
I_m = {c: moran(mm[f"dpp_{c}"].values, Wm) for c in cands}
out["moran_mun"] = {c: {"I": v[0], "p": v[1]} for c, v in I_m.items()}
out["lisa"] = lisa_out

with open("saida/estatistica.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
print("saida/estatistica.json:", round(len(json.dumps(out)) / 1024), "KB")
