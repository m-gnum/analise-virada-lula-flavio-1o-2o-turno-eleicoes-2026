"""Casos curiosos da variação de votos (Lula e Flávio, 1º x 2º turno): cidades e estados que fogem do padrão.

Entrada:  saida/locais_dashboard.parquet, saida/seguranca_municipio.parquet, saida/estatistica.json
Saída:    saida/curiosidades.json (aba "Curiosidades" do painel)
Rodar da raiz do projeto: .venv/bin/python -I scripts/09_curiosidades.py

Seis blocos: uniformidade, outliers, correlações fortes, perfil sem efeito, outros cenários e eliminados x abstenção x brancos e nulos.
Cada caso vem de uma regra com corte mínimo de tamanho (cidades de 15 a 20 mil aptos ou mais, bairros de 1.500 aptos ou mais etc.), para não
mostrar ruído de unidades pequenas. Os textos descrevem padrões, não causas.
"""
import json
import re
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.simplefilter("ignore", FutureWarning)

d = pd.read_parquet("saida/locais_dashboard.parquet")
sg = pd.read_parquet("saida/seguranca_municipio.parquet")[["uf", "cd_mun", "taxa_cvli_100k"]]
d = d.merge(sg, on=["uf", "cd_mun"], how="left")
EST = json.load(open("saida/estatistica.json", encoding="utf-8"))

UF_NOME = {"AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"}
PEQ = {"DE", "DA", "DO", "DAS", "DOS", "E"}


ACENTO = {"AMAMBAI": "AMAMBAÍ"}  # a fonte traz alguns nomes sem acento


def bonito(s):
    """MARECHAL CÂNDIDO RONDON -> Marechal Cândido Rondon."""
    s = ACENTO.get(str(s), str(s))
    ps = s.title().split()
    t = " ".join(p.lower() if i and p.upper() in PEQ else p for i, p in enumerate(ps))
    return re.sub(r"(?<=[a-zà-ú])'([A-ZÀ-Ú])", lambda m: "'" + m.group(1).lower(), t)


def local(s):
    """Nome do local de votação sem o sufixo técnico (UE-MUN etc.)."""
    return bonito(re.sub(r"\s+UE[- ]\s*(MUN|EST|FED|PRIV)\w*$", "", str(s), flags=re.I))


def apt(x):
    return f"{fm(x / 1e6, 1)} milhões de aptos" if x >= 1e6 else f"{fm(x / 1e3, 0)} mil aptos"


def fm(x, n=1):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sgn(x, n=1):
    return ("+" if x >= 0 else "−") + fm(abs(x), n)


def pc(x, n=0):
    return fm(x * 100, n) + "%"


# ------------------------------------------------------------------ base
d["cidade"] = d.municipio.map(bonito) + "/" + d.uf
for c, (a, b) in {"lula": ("lula_t1", "lula_t2"), "flavio": ("flavio_t1", "flavio_t2")}.items():
    d["dpp_" + c] = (d[b] - d[a]) / d.aptos * 100
p = d.perf_eleitores
d["renda"] = np.log(d.renda_media_1km)
d["superior"] = d.esc_superior / p * 100
d["sem_instr"] = d.esc_sem_instrucao / p * 100
d["idade60"] = d.idade_60_mais / p * 100
d["idade16"] = d.idade_16_24 / p * 100
d["mulheres_p"] = d.mulheres / p * 100
d["fund"] = d.esc_fundamental / p * 100
d["medio"] = d.esc_medio / p * 100
d["idade2544"] = d.idade_25_44 / p * 100
d["idade4559"] = d.idade_45_59 / p * 100
VARS = ["renda", "superior", "sem_instr", "idade60", "idade16", "mulheres_p"]  # as seis do R²
VX = VARS + ["fund", "medio", "idade2544", "idade4559"]  # todas as características do painel, para as correlações
CAND = {"lula": "Lula", "flavio": "Flávio"}
SOMAR = ["aptos", "lula_t1", "lula_t2", "flavio_t1", "flavio_t2", "outros_t1", "branco_t1", "branco_t2", "nulo_t1", "nulo_t2", "abst_t1", "abst_t2"]


def wmean(x, w):
    return np.average(x, weights=w)


def wsd(x, w):
    m = np.average(x, weights=w)
    return float(np.sqrt(np.average((x - m) ** 2, weights=w)))


def wcorr(x, y, w):
    mx, my = wmean(x, w), wmean(y, w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return float(cov / np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w)))


def somar(df, keys):
    g = df.groupby(keys)
    o = g[SOMAR].sum()
    o["n_loc"] = g.size()
    for c in CAND:
        o["dpp_" + c] = (o[f"{c}_t2"] - o[f"{c}_t1"]) / o.aptos * 100
    return o.reset_index()


# coordenadas: média ponderada dos locais com coordenada própria
ok = d[(d.coord_aprox == 0) & d.lat.notna()]
cc = ok.groupby(["uf", "cd_mun"]).apply(lambda s: pd.Series({"lat": wmean(s.lat, s.aptos), "lon": wmean(s.lon, s.aptos)})).reset_index()
ce = ok.groupby("uf").apply(lambda s: pd.Series({"lat": wmean(s.lat, s.aptos), "lon": wmean(s.lon, s.aptos)})).reset_index()
COORD_C = {(r.uf, r.cd_mun): (r.lat, r.lon) for r in cc.itertuples()}
COORD_E = {r.uf: (r.lat, r.lon) for r in ce.itertuples()}
CID = d.drop_duplicates(["uf", "cd_mun"])[["uf", "cd_mun", "municipio", "cidade"]]
CHAVE = {r.cidade: (r.uf, r.cd_mun, r.municipio) for r in CID.itertuples()}


def ent_c(uf, cd_mun, municipio):
    la, lo = COORD_C[(uf, cd_mun)]
    return {"k": "c", "uf": uf, "mn": municipio, "nome": bonito(municipio) + "/" + uf, "lat": round(float(la), 3), "lon": round(float(lo), 3)}


def ent_nome(nome):
    """'Cruzeiro do Sul/AC' -> entidade."""
    uf, cd, mn = CHAVE[nome]
    return ent_c(uf, cd, mn)


def ent_e(uf):
    la, lo = COORD_E[uf]
    return {"k": "e", "uf": uf, "mn": "", "nome": UF_NOME[uf], "lat": round(float(la), 3), "lon": round(float(lo), 3)}


def B(c):
    return f"<b>{c}</b>"


def linha(txt, *ents):
    return {"txt": txt, "ents": list(ents)}


def item(titulo, linhas, nota=""):
    return {"titulo": titulo, "nota": nota, "linhas": linhas}


SECOES = []

# ------------------------------------------------------------------ 1. uniformidade
bairros = somar(d, ["uf", "cd_mun", "municipio", "bairro"])
bq = bairros[bairros.aptos >= 1500]
rows = []
for (uf, cd, mn), s in bq.groupby(["uf", "cd_mun", "municipio"]):
    if len(s) < 8:
        continue
    rows.append(dict(uf=uf, cd=cd, mn=mn, nb=len(s), aptos=s.aptos.sum(), sdL=wsd(s.dpp_lula, s.aptos), sdF=wsd(s.dpp_flavio, s.aptos), mL=wmean(s.dpp_lula, s.aptos), mF=wmean(s.dpp_flavio, s.aptos)))
U = pd.DataFrame(rows)
U["sd"] = U.sdL + U.sdF
medL, medF = U.sdL.median(), U.sdF.median()
unif = U.sort_values("sd").head(6)
disp = U.sort_values("sd", ascending=False).head(6)
cidades = somar(d, ["uf", "cd_mun", "municipio"])
rows = []
for uf, s in cidades[cidades.aptos >= 3000].groupby("uf"):
    if len(s) >= 8:
        rows.append(dict(uf=uf, n=len(s), sdL=wsd(s.dpp_lula, s.aptos), sdF=wsd(s.dpp_flavio, s.aptos)))
E = pd.DataFrame(rows)
e_unif = E.sort_values("sdL").head(5)
e_disp = E.sort_values("sdL", ascending=False).head(7)
E["razao"] = E.sdL / E.sdF
e_assim = E[E.razao > 2].sort_values("razao", ascending=False)
am = U[U.mn == "AMAMBAI"].iloc[0]
bt = U[U.mn == "BERTIOGA"].iloc[0]
S1 = {
    "id": "uniformidade",
    "titulo": "1. Uniformidade: onde tudo mudou igual, e onde nada mudou igual",
    "intro": (
        "<b>Desvio</b> mede o quanto as áreas de um mesmo lugar diferem entre si. Pense nas variações de cada bairro de uma cidade: se quase todos subiram o mesmo tanto, o desvio é pequeno; se uns subiram muito e outros caíram, é grande. "
        f"Em {B('Bertioga/SP')} o Lula subiu em média {sgn(bt.mL)} p.p. nos bairros, com desvio de {fm(bt.sdL, 2)}: um bairro típico fica entre {sgn(bt.mL - bt.sdL)} e {sgn(bt.mL + bt.sdL)}, praticamente igual aos demais. "
        f"Em {B('Amambaí/MS')}, com desvio de {fm(am.sdL, 1)}, um bairro típico fica entre {sgn(am.mL - am.sdL)} e {sgn(am.mL + am.sdL)}: a cidade é feita de bairros muito diferentes. "
        f"No país, o desvio típico entre bairros de uma cidade é de {fm(medL, 1)} p.p. para o Lula e {fm(medF, 1)} para o Flávio. Contei só cidades com 8 ou mais bairros de 1.500 aptos ou mais (e, nos estados, as cidades de 3 mil aptos ou mais)."
    ),
    "itens": [
        item("Cidades com bairros quase iguais", [linha(f"{B(bonito(r.mn) + '/' + r.uf)}: {r.nb} bairros grandes que variaram quase igual (desvio de {fm(r.sdL, 2)} p.p. para Lula e {fm(r.sdF, 2)} para Flávio).", ent_c(r.uf, r.cd, r.mn)) for r in unif.itertuples()]),
        item("Cidades com bairros muito diferentes", [linha(f"{B(bonito(r.mn) + '/' + r.uf)}: desvio de {fm(r.sdL, 1)} p.p. para Lula e {fm(r.sdF, 1)} para Flávio, entre {r.nb} bairros.", ent_c(r.uf, r.cd, r.mn)) for r in disp.itertuples()]),
        item("Estados com cidades parecidas", [linha(f"{B(UF_NOME[r.uf])}: as {r.n} cidades variaram de forma parecida (desvio de {fm(r.sdL, 1)} p.p. para Lula e {fm(r.sdF, 1)} para Flávio).", ent_e(r.uf)) for r in e_unif.itertuples()]),
        item("Estados com cidades muito diferentes", [linha(f"{B(UF_NOME[r.uf])}: desvio de {fm(r.sdL, 1)} p.p. para Lula e {fm(r.sdF, 1)} para Flávio, entre {r.n} cidades.", ent_e(r.uf)) for r in e_disp.itertuples()]),
        item(
            "Um candidato varia muito, o outro quase não",
            [linha(f"{B(UF_NOME[r.uf])}: as cidades variam muito para o Lula (desvio de {fm(r.sdL, 1)} p.p.) e pouco para o Flávio ({fm(r.sdF, 1)}).", ent_e(r.uf)) for r in e_assim.itertuples()],
            "Nenhum estado mostra o inverso de forma marcante.",
        ),
    ],
}
SECOES.append(S1)

# ------------------------------------------------------------------ 2. outliers
res = []
for (uf, cd, mn), s in bairros.groupby(["uf", "cd_mun", "municipio"]):
    s = s[s.aptos >= 300]
    if len(s) < 7 or s.aptos.sum() < 20000:
        continue
    for c in CAND:
        v = s["dpp_" + c].values
        med = np.median(v)
        mad = max(np.median(np.abs(v - med)) * 1.4826, 0.6)
        z = (v - med) / mad
        for i in np.argsort(-np.abs(z))[:2]:
            res.append(dict(uf=uf, cd=cd, mn=mn, bairro=s.bairro.iloc[i], c=c, aptos=int(s.aptos.iloc[i]), pct=s.aptos.iloc[i] / s.aptos.sum() * 100, val=v[i], med=med, desv=v[i] - med, z=z[i]))
RB = pd.DataFrame(res)
rural = RB.bairro.str.contains("RURAL|RIBEIRINHO", case=False, regex=True)
ob = RB[(RB.aptos >= 1000) & (RB.z.abs() > 5) & ~rural].assign(a=lambda x: x.desv.abs()).sort_values("a", ascending=False).drop_duplicates(["uf", "cd"]).head(9)
# zona rural como bairro
rr = []
for (uf, cd, mn), s in bairros.groupby(["uf", "cd_mun", "municipio"]):
    if s.aptos.sum() < 30000:
        continue
    m = s.bairro.str.contains("RURAL|RIBEIRINHO", case=False, regex=True)
    if not m.any():
        continue
    for i in s[m].index:
        o = s[s.index != i]
        share = s.loc[i, "aptos"] / s.aptos.sum()
        if share < 0.15 or len(o) < 3:
            continue
        mo = wmean(o.dpp_lula, o.aptos)
        rr.append(dict(uf=uf, cd=cd, mn=mn, bairro=s.loc[i, "bairro"], share=share, val=s.loc[i, "dpp_lula"], out=mo, dif=s.loc[i, "dpp_lula"] - mo))
RR = pd.DataFrame(rr)
RR = RR[RR.dif <= -3].sort_values("dif").drop_duplicates(["uf", "cd"]).head(8)
# locais extremos
x = d[d.aptos >= 800]
loc_lin = []
for c, asc, rot in [("lula", False, "maior ganho"), ("lula", True, "maior queda ou menor ganho"), ("flavio", False, "maior ganho"), ("flavio", True, "maior queda ou menor ganho")]:
    r = x.sort_values("dpp_" + c, ascending=asc).iloc[0]
    o = "flavio" if c == "lula" else "lula"
    loc_lin.append(linha(f"{B(r.cidade)}, {local(r.nm_local)} ({fm(r.aptos, 0)} aptos): {CAND[c]} {sgn(r['dpp_' + c])} p.p., {rot} entre os locais do país com 800 aptos ou mais; {CAND[o]} {sgn(r['dpp_' + o])} p.p.", ent_c(r.uf, r.cd_mun, r.municipio)))
# cidades que destoam do estado
cg = cidades[cidades.aptos >= 15000]
res = []
for uf, s in cg.groupby("uf"):
    if len(s) < 8:
        continue
    for c in CAND:
        v = s["dpp_" + c].values
        med = np.median(v)
        mad = max(np.median(np.abs(v - med)) * 1.4826, 0.6)
        for i in np.argsort(-np.abs((v - med) / mad))[:3]:
            res.append(dict(uf=uf, cd=s.cd_mun.iloc[i], mn=s.municipio.iloc[i], c=c, val=v[i], med=med, desv=v[i] - med, z=(v[i] - med) / mad))
RC = pd.DataFrame(res)
RC = RC[RC.z.abs() > 4].assign(a=lambda x: x.desv.abs()).sort_values("a", ascending=False).drop_duplicates(["uf", "cd"]).head(7)
c50 = cidades[cidades.aptos >= 50000]
mariana = c50.sort_values("dpp_lula", ascending=False).iloc[0]
S2 = {
    "id": "outliers",
    "titulo": "2. Outliers: bairros, locais e cidades que destoam",
    "intro": (
        "Aqui o critério é a distância para o que é típico: um bairro (ou cidade) que variou muito acima ou muito abaixo do bairro típico da cidade (ou da cidade típica do estado), em pontos percentuais dos aptos. "
        "Só entram unidades com tamanho suficiente para não serem ruído. Os nomes (\"zona rural\", \"ribeirinhos\", \"indígena\") são rótulos dos locais de votação: a lista descreve o padrão, não explica o motivo."
    ),
    "itens": [
        item("Bairros que destoam da própria cidade", [linha(f"{B(bonito(r.mn) + '/' + r.uf)}, bairro {bonito(r.bairro)}: {CAND[r.c]} {sgn(r.val)} p.p., contra {sgn(r.med)} no bairro típico da cidade ({fm(r.pct, 1)}% dos aptos).", ent_c(r.uf, r.cd, r.mn)) for r in ob.itertuples()]),
        item("Locais de votação extremos", loc_lin),
        item("Zona rural e ribeirinhos como \"bairro\"", [linha(f"{B(bonito(r.mn) + '/' + r.uf)}: o bairro \"{bonito(r.bairro)}\" reúne {fm(r.share * 100, 0)}% dos aptos e o Lula variou {sgn(r.val)} p.p. nele, contra {sgn(r.out)} nos demais bairros.", ent_c(r.uf, r.cd, r.mn)) for r in RR.itertuples()]),
        item(
            "Cidades que destoam do estado",
            [linha(f"{B(bonito(r.mn) + '/' + r.uf)}: {CAND[r.c]} {sgn(r.val)} p.p., contra {sgn(r.med)} na cidade típica do estado.", ent_c(r.uf, r.cd, r.mn)) for r in RC.itertuples()]
            + [linha(f"{B(bonito(mariana.municipio) + '/' + mariana.uf)}: Lula {sgn(mariana.dpp_lula)} p.p., o maior ganho entre as cidades com 50 mil aptos ou mais.", ent_c(mariana.uf, mariana.cd_mun, mariana.municipio))],
        ),
    ],
}
SECOES.append(S2)

# ------------------------------------------------------------------ 3. correlações e 4. sem efeito
base = d[d.aptos >= 100].dropna(subset=VX + ["dpp_lula", "dpp_flavio"])
nac = {c: {v: wcorr(base[v].values, base["dpp_" + c].values, base.aptos.values) for v in VX} for c in CAND}
LAB = {
    "renda": "renda no entorno",
    "superior": "eleitores com ensino superior",
    "sem_instr": "eleitores sem instrução",
    "fund": "eleitores com ensino fundamental",
    "medio": "eleitores com ensino médio",
    "idade16": "eleitores de 16 a 24 anos",
    "idade2544": "eleitores de 25 a 44 anos",
    "idade4559": "eleitores de 45 a 59 anos",
    "idade60": "eleitores de 60 anos ou mais",
    "mulheres_p": "mulheres",
}


def frase_r(var, cand, r):
    return f"quanto mais {LAB[var]}, {'maior' if r > 0 else 'menor'} a variação de {CAND[cand]} (correlação {sgn(r, 2)})"


rows = []
for k, s in base.groupby("cidade"):
    if len(s) < 80:
        continue
    r = {"cidade": k, "n": len(s)}
    for c in CAND:
        for v in VX:
            r[f"{c}|{v}"] = wcorr(s[v].values, s["dpp_" + c].values, s.aptos.values) if s[v].std() > 0 else np.nan
    rows.append(r)
CR = pd.DataFrame(rows)
long = CR.melt(id_vars=["cidade", "n"], var_name="cv", value_name="r")
long[["c", "v"]] = long.cv.str.split("|", expand=True)
forte = long[long.v.isin(["superior", "renda"])].reindex(long[long.v.isin(["superior", "renda"])].r.abs().sort_values(ascending=False).index).drop_duplicates("cidade").head(8)
inv = long[(long.c == "lula") & (long.v == "sem_instr") & (long.r > 0.55)].sort_values("r", ascending=False).head(7)
# R2 por cidade (n >= 40)
rows = []
for k, s in base.groupby("cidade"):
    if len(s) < 40:
        continue
    X = sm.add_constant((s[VARS] - s[VARS].mean()) / s[VARS].std().replace(0, 1))
    r = {"cidade": k, "n": len(s)}
    for c in CAND:
        r[c] = sm.WLS(s["dpp_" + c], X, weights=s.aptos).fit().rsquared_adj
        cs = {v: wcorr(s[v].values, s["dpp_" + c].values, s.aptos.values) for v in VARS if s[v].std() > 0}
        r[c + "_cs"] = cs
    rows.append(r)
R2 = pd.DataFrame(rows)
R2["mn_"] = R2[["lula", "flavio"]].min(axis=1)
R2["mx_"] = R2[["lula", "flavio"]].max(axis=1)
alto = R2.sort_values("mn_", ascending=False).head(8)
nulo = R2[(R2.mx_ <= 0.025) & (R2.n >= 40)].sort_values("mx_").head(10)
so_f = R2[(R2.lula < 0.05) & (R2.flavio > 0.45)].sort_values("flavio", ascending=False).head(4)
so_l = R2[(R2.flavio < 0.05) & (R2.lula > 0.45)].sort_values("lula", ascending=False).head(5)
# estados: correlação por local
est_r = {}
for uf, s in base.groupby("uf"):
    est_r[uf] = {f"{c}|{v}": wcorr(s[v].values, s["dpp_" + c].values, s.aptos.values) for c in CAND for v in VX}
mun = d.groupby(["uf", "cd_mun", "municipio"]).agg(aptos=("aptos", "sum"), l1=("lula_t1", "sum"), l2=("lula_t2", "sum"), f1=("flavio_t1", "sum"), f2=("flavio_t2", "sum"), taxa=("taxa_cvli_100k", "first")).reset_index()
mun["dL"] = (mun.l2 - mun.l1) / mun.aptos * 100
mun["dF"] = (mun.f2 - mun.f1) / mun.aptos * 100
mun["ltx"] = np.log1p(mun.taxa)
cv = {}
for uf, s in mun[mun.aptos >= 3000].dropna(subset=["taxa"]).groupby("uf"):
    if len(s) >= 30:
        cv[uf] = (wcorr(s.ltx.values, s.dL.values, s.aptos.values), wcorr(s.ltx.values, s.dF.values, s.aptos.values), len(s))
sb = mun[mun.aptos >= 3000].dropna(subset=["taxa"])
cv_br = (wcorr(sb.ltx.values, sb.dL.values, sb.aptos.values), wcorr(sb.ltx.values, sb.dF.values, sb.aptos.values))
dois_sobem = [u for u in ["AC", "AP", "AM", "RR", "TO"] if est_r[u]["lula|renda"] > 0.4 and est_r[u]["flavio|renda"] > 0.4]
ambos_cid = CR[(CR["lula|renda"] > 0.4) & (CR["flavio|renda"] > 0.4)].sort_values("n", ascending=False).head(6)


def cid_top(v, c, sinal, k):
    x = long[(long.v == v) & (long.c == c) & (long.r * sinal > 0.4)].copy()
    x["rs"] = x.r * sinal
    return x.sort_values("rs", ascending=False).head(k)


def uf_top(v, c, sinal, k):
    xs = sorted([(u, e[f"{c}|{v}"]) for u, e in est_r.items() if e[f"{c}|{v}"] * sinal > 0.25], key=lambda t: -t[1] * sinal)
    return xs[:k]


def itm_corr(titulo, specs, nota=""):
    """specs: (tipo 'c' cidade | 'u' estado, característica, candidato, sinal, quantidade)."""
    ls = []
    for t, v, c, sinal, k in specs:
        if t == "c":
            ls += [linha(f"{B(r.cidade)}: {frase_r(v, c, r.r)}.", ent_nome(r.cidade)) for r in cid_top(v, c, sinal, k).itertuples()]
        else:
            ls += [linha(f"{B(UF_NOME[u])}: {frase_r(v, c, r)}.", ent_e(u)) for u, r in uf_top(v, c, sinal, k)]
    return item(titulo, ls, nota)


def perfil_de(r, c):
    """Características que mais acompanham a variação do candidato na cidade (as duas mais fortes, se a segunda também for forte)."""
    cs = r[c + "_cs"]
    ordem = sorted(cs, key=lambda v: -abs(cs[v]))
    t = [ordem[0]] + [v for v in ordem[1:2] if abs(cs[v]) >= 0.5 and abs(cs[v]) >= 0.7 * abs(cs[ordem[0]])]
    return " e ".join(f"{LAB[v]} ({sgn(cs[v], 2)})" for v in t)


def linha_r2(r):
    txt = (
        f"{B(r.cidade)} ({fm(r.n, 0)} locais): o perfil explica {pc(r.lula)} da variação de Lula e {pc(r.flavio)} da de Flávio. "
        f"Características mais ligadas à variação: para o Lula, {perfil_de(r._asdict(), 'lula')}; para o Flávio, {perfil_de(r._asdict(), 'flavio')}."
    )
    return linha(txt, ent_nome(r.cidade))


S3 = {
    "id": "correlacoes",
    "titulo": "3. Correlações muito diretas entre o perfil e a variação",
    "intro": (
        "<b>Correlação</b> vai de −1 a +1 e mede se duas coisas andam juntas nos locais de votação de um mesmo lugar. Perto de +1: onde uma é maior, a outra também é. Perto de −1: onde uma é maior, a outra é menor. Perto de 0: uma não ajuda a prever a outra. "
        f"Por exemplo, −0,86 entre ensino superior e a variação de Lula em João Pessoa significa que, bairro a bairro, quanto mais eleitores com ensino superior, menos o Lula cresceu, de forma bem regular. "
        "<b>R²</b> resume o conjunto: é a parte da diferença de variação entre os locais que o perfil (renda, escolaridade, idade e sexo) consegue explicar. 70% quer dizer que, sabendo o perfil, dá para prever quase tudo da variação; perto de 0%, que o perfil não ajuda; o que sobra vem de outros fatores que o painel não mede. "
        "São padrões entre áreas, não o motivo do voto de cada eleitor."
    ),
    "itens": [
        item("Cidades onde o perfil acompanha a variação de forma quase perfeita", [linha(f"{B(r.cidade)}: {frase_r(r.v, r.c, r.r)}.", ent_nome(r.cidade)) for r in forte.itertuples()]),
        item(
            "Cidades onde o perfil explica quase tudo (R² alto)",
            [linha_r2(r) for r in alto.itertuples()],
            "Entre parênteses, a correlação de cada característica com a variação do candidato na cidade (quanto mais perto de ±1, mais ela acompanha). Positiva: onde a característica é maior, o candidato cresceu mais. Negativa: cresceu menos.",
        ),
        item(
            "O contrário do país: bairros com mais eleitores sem instrução, mais ganho do Lula",
            [linha(f"{B(r.cidade)}: nos locais com mais eleitores sem instrução o Lula cresceu mais (correlação {sgn(r.r, 2)}).", ent_nome(r.cidade)) for r in inv.itertuples()],
            f"No país como um todo a correlação entre eleitores sem instrução e a variação de Lula é {sgn(nac['lula']['sem_instr'], 2)}: as cidades com mais eleitores sem instrução (interior da Amazônia e do Maranhão) cresceram menos. Dentro das cidades, o padrão se inverte.",
        ),
        item(
            "Estados: o mais polarizado e onde os dois candidatos sobem com a renda",
            [linha(f"{B('Distrito Federal')}: o Lula cresceu menos onde a renda é maior (correlação {sgn(est_r['DF']['lula|renda'], 2)}) e o Flávio cresceu mais ({sgn(est_r['DF']['flavio|renda'], 2)}): a divisão mais nítida do país.", ent_e("DF"))]
            + [linha(f"{B(UF_NOME[u])}: nos locais de renda maior, os dois candidatos cresceram mais (Lula {sgn(est_r[u]['lula|renda'], 2)}, Flávio {sgn(est_r[u]['flavio|renda'], 2)}).", ent_e(u)) for u in dois_sobem]
            + [linha(f"{B(r.cidade)}: os dois crescem com a renda (Lula {sgn(r['lula|renda'], 2)}, Flávio {sgn(r['flavio|renda'], 2)}).", ent_nome(r.cidade)) for _, r in ambos_cid.iterrows()],
        ),
        item(
            "Presença de mulheres no local",
            [linha(f"{B(UF_NOME[u])}: quanto mais mulheres no local, mais o Lula cresceu (correlação {sgn(est_r[u]['lula|mulheres_p'], 2)}).", ent_e(u)) for u in ["AP", "AM", "AC", "RR", "TO"]]
            + [linha(f"{B(UF_NOME[u])}: não há relação entre a presença de mulheres e a variação de {CAND[c]} (correlação {sgn(est_r[u][c + '|mulheres_p'], 2)}).", ent_e(u)) for u, c in [("DF", "lula"), ("SP", "flavio"), ("SC", "flavio")]],
            f"No país, a correlação entre % de mulheres e a variação de Lula é {sgn(nac['lula']['mulheres_p'], 2)}.",
        ),
        itm_corr(
            "Eleitores de 60 anos ou mais",
            [("c", "idade60", "lula", -1, 6), ("u", "idade60", "lula", -1, 2), ("u", "idade60", "flavio", 1, 2)],
            f"No país, a correlação entre % de eleitores de 60 anos ou mais e a variação de Lula é {sgn(nac['lula']['idade60'], 2)} (e {sgn(nac['flavio']['idade60'], 2)} para Flávio).",
        ),
        itm_corr(
            "Eleitores de 16 a 24 anos",
            [("c", "idade16", "lula", 1, 5), ("c", "idade16", "flavio", -1, 2), ("u", "idade16", "flavio", -1, 2), ("u", "idade16", "lula", 1, 1)],
            f"No país, a correlação entre % de eleitores de 16 a 24 anos e a variação de Flávio é {sgn(nac['flavio']['idade16'], 2)}; para Lula, {sgn(nac['lula']['idade16'], 2)}.",
        ),
        itm_corr(
            "Eleitores de 25 a 44 anos",
            [("c", "idade2544", "lula", 1, 5), ("c", "idade2544", "flavio", -1, 1), ("u", "idade2544", "lula", 1, 3)],
            f"No país, a correlação com a variação de Lula é {sgn(nac['lula']['idade2544'], 2)} e com a de Flávio, {sgn(nac['flavio']['idade2544'], 2)}.",
        ),
        itm_corr(
            "Eleitores de 45 a 59 anos",
            [("c", "idade4559", "lula", -1, 3), ("c", "idade4559", "flavio", 1, 3), ("u", "idade4559", "flavio", 1, 4)],
            f"No país, a correlação com a variação de Flávio é {sgn(nac['flavio']['idade4559'], 2)} e com a de Lula, {sgn(nac['lula']['idade4559'], 2)}.",
        ),
        itm_corr(
            "Eleitores com ensino médio",
            [("c", "medio", "lula", 1, 6), ("c", "medio", "flavio", -1, 2), ("u", "medio", "lula", 1, 4)],
            f"No país, a correlação entre % com ensino médio e a variação de Lula é {sgn(nac['lula']['medio'], 2)}.",
        ),
        itm_corr(
            "Eleitores com ensino fundamental",
            [("c", "fund", "lula", 1, 5), ("c", "fund", "flavio", -1, 3), ("u", "fund", "lula", 1, 1), ("u", "fund", "flavio", -1, 2), ("u", "fund", "lula", -1, 1)],
            f"No país, a correlação entre % com ensino fundamental e a variação de Lula é {sgn(nac['lula']['fund'], 2)} (e {sgn(nac['flavio']['fund'], 2)} para Flávio). Dentro de cada cidade, porém, o padrão costuma ser forte, e o sinal muda de um lugar para outro.",
        ),
        itm_corr(
            "Eleitores sem instrução e o Flávio",
            [("c", "sem_instr", "flavio", -1, 5), ("u", "sem_instr", "flavio", -1, 3)],
            f"No país, a correlação entre % sem instrução e a variação de Flávio é {sgn(nac['flavio']['sem_instr'], 2)}: onde há mais eleitores sem instrução, ele cresceu menos.",
        ),
        item(
            "Taxa de CVLI e variação, entre as cidades de cada estado",
            [linha(f"Brasil: entre as {fm(len(sb), 0)} cidades com 3 mil aptos ou mais, a taxa de CVLI não tem relação com a variação de Lula (correlação {sgn(cv_br[0], 2)}) e tem relação negativa com a de Flávio ({sgn(cv_br[1], 2)}): nas cidades mais violentas ele cresceu menos.")]
            + [linha(f"{B(UF_NOME['PI'])}: nas cidades mais violentas o Lula cresceu mais (correlação {sgn(cv['PI'][0], 2)}).", ent_e("PI"))]
            + [linha(f"{B(UF_NOME[u])}: Lula {sgn(cv[u][0], 2)} e Flávio {sgn(cv[u][1], 2)}: nas cidades mais violentas o Lula cresceu mais e o Flávio menos.", ent_e(u)) for u in ["RS", "SC"]]
            + [linha(f"{B(UF_NOME['PE'])}: o único estado em que o Flávio cresce claramente mais nas cidades mais violentas (correlação {sgn(cv['PE'][1], 2)}).", ent_e("PE"))],
            "Correlação entre a taxa de CVLI (em escala logarítmica) e a variação, com as cidades de 3 mil aptos ou mais; só em estados com 30 ou mais cidades.",
        ),
    ],
}
SECOES.append(S3)
st = lambda u, c, k: EST["reg"][u][c][k]  # noqa: E731
low = sorted([u for u in UF_NOME if u in EST["reg"]], key=lambda u: st(u, "lula", "r2"))
S4 = {
    "id": "sem_efeito",
    "titulo": "4. Perfil sem efeito: onde as características quase não explicam a variação",
    "intro": (
        "Aqui o <b>R²</b> é baixo: renda, escolaridade, idade e sexo dos locais quase não ajudam a prever quanto cada candidato variou. "
        "R² de 70% quer dizer que o perfil explica quase tudo; perto de 0%, que ele não explica nada (valores ligeiramente negativos indicam o mesmo). O que sobra vem de outros fatores que o painel não mede: história local, campanha, abstenção e outros."
    ),
    "itens": [
        item(
            "Estados",
            [linha(f"{B(UF_NOME['SE'])}: o perfil explica só {pc(st('SE', 'lula', 'r2'))} da variação de Lula, o menor valor entre os estados (e {pc(st('SE', 'flavio', 'r2'))} da de Flávio).", ent_e("SE")),
             linha(f"{B(UF_NOME['SC'])}: o perfil explica {pc(st('SC', 'lula', 'r2'))} da variação de Lula e {pc(st('SC', 'flavio', 'r2'))} da de Flávio, entre os menores do país.", ent_e("SC")),
             linha(f"{B(UF_NOME['AL'])}: o Lula não tem relação com a renda (correlação {sgn(est_r['AL']['lula|renda'], 2)}) nem com eleitores sem instrução ({sgn(est_r['AL']['lula|sem_instr'], 2)}), enquanto o Flávio responde claramente à renda ({sgn(est_r['AL']['flavio|renda'], 2)}).", ent_e("AL"))],
        ),
        item("Cidades em que o perfil não explica nada, para os dois", [linha(f"{B(r.cidade)}: o perfil explica {pc(max(r.lula, 0))} da variação de Lula e {pc(max(r.flavio, 0))} da de Flávio ({r.n} locais).", ent_nome(r.cidade)) for r in nulo.itertuples()]),
        item(
            "O perfil explica um candidato, e o outro não",
            [linha(f"{B(r.cidade)}: o perfil explica {pc(r.flavio)} da variação de Flávio e nada da de Lula.", ent_nome(r.cidade)) for r in so_f.itertuples()]
            + [linha(f"{B(r.cidade)}: o perfil explica {pc(r.lula)} da variação de Lula e {pc(max(r.flavio, 0))} da de Flávio.", ent_nome(r.cidade)) for r in so_l.itertuples()],
        ),
    ],
}
SECOES.append(S4)

# ------------------------------------------------------------------ 5. outros cenários
M = cidades.copy()
M["m1"] = (M.lula_t1 - M.flavio_t1) / M.aptos * 100
M["m2"] = (M.lula_t2 - M.flavio_t2) / M.aptos * 100
v_l = M[(M.m1 < 0) & (M.m2 > 0)]
v_f = M[(M.m1 > 0) & (M.m2 < 0)]
grandes = v_l.sort_values("aptos", ascending=False).head(5)
UFt = d.groupby("uf")[["lula_t1", "lula_t2", "flavio_t1", "flavio_t2", "aptos"]].sum()
UFt["m1"] = (UFt.lula_t1 - UFt.flavio_t1) / UFt.aptos * 100
UFt["m2"] = (UFt.lula_t2 - UFt.flavio_t2) / UFt.aptos * 100
uf_vira = UFt[np.sign(UFt.m1) != np.sign(UFt.m2)]
perd = cidades[(cidades.aptos >= 15000) & (cidades.dpp_lula < 0)].sort_values("dpp_lula")
n_f_perd = int(((cidades.aptos >= 15000) & (cidades.dpp_flavio < 0)).sum())
go = c50[c50.uf == "GO"].sort_values("dpp_flavio", ascending=False).head(5)
top_f = c50.sort_values("dpp_flavio", ascending=False).head(5)
ext_lo = c50.sort_values("dpp_lula").head(5)
ext_hi = c50.sort_values("dpp_lula", ascending=False).head(5)
S5 = {
    "id": "outros",
    "titulo": "5. Outros cenários curiosos",
    "intro": "Fatos que não cabem nas categorias acima, mas que chamam a atenção: viradas de liderança, cidades em que um candidato perdeu votos e extremos de variação. Cidades com 15 mil aptos ou mais (50 mil nos extremos).",
    "itens": [
        item(
            "Cidades em que a liderança virou",
            [linha(f"Em {B(str(len(v_l)) + ' cidades')} o Flávio liderava no 1º turno e o Lula passou à frente no 2º. Só {len(v_f)} cidade virou no sentido contrário: {B(bonito(v_f.iloc[0].municipio) + '/' + v_f.iloc[0].uf)}, com {fm(v_f.iloc[0].aptos, 0)} aptos.", *[ent_c(r.uf, r.cd_mun, r.municipio) for r in v_f.itertuples()])]
            + [linha(f"{B(bonito(r.municipio) + '/' + r.uf)}: a margem do Lula passou de {sgn(r.m1)} p.p. dos aptos para {sgn(r.m2)} ({apt(r.aptos)}).", ent_c(r.uf, r.cd_mun, r.municipio)) for r in grandes.itertuples()]
            + [linha(f"{B(UF_NOME[u])}: o único estado em que a liderança mudou: a margem do Lula passou de {sgn(r.m1)} para {sgn(r.m2)} p.p. dos aptos.", ent_e(u)) for u, r in uf_vira.iterrows()],
        ),
        item(
            "Cidades em que o Lula perdeu votos",
            [linha(f"Em {B(str(len(perd)) + ' cidades')} com 15 mil aptos ou mais o Lula perdeu votos em termos absolutos; o Flávio perdeu em {B(str(n_f_perd))}.")]
            + [linha(f"{B(bonito(r.municipio) + '/' + r.uf)}: Lula {sgn(r.dpp_lula)} p.p. e Flávio {sgn(r.dpp_flavio)}.", ent_c(r.uf, r.cd_mun, r.municipio)) for r in perd.head(8).itertuples()],
        ),
        item(
            "Os maiores ganhos do Flávio ficaram no mesmo estado",
            [linha(f"{B(bonito(r.municipio) + '/' + r.uf)}: Flávio {sgn(r.dpp_flavio)} p.p. (Lula também {sgn(r.dpp_lula)}).", ent_c(r.uf, r.cd_mun, r.municipio)) for r in top_f.itertuples()],
            "As cinco maiores variações do Flávio entre as cidades de 50 mil aptos ou mais são goianas." if (top_f.uf == "GO").all() else "",
        ),
        item(
            "Extremos de variação",
            [linha(f"{B(bonito(r.municipio) + '/' + r.uf)}: Lula {sgn(r.dpp_lula)} p.p., um dos maiores ganhos.", ent_c(r.uf, r.cd_mun, r.municipio)) for r in ext_hi.head(2).itertuples()]
            + [linha(f"{B(bonito(r.municipio) + '/' + r.uf)}: Lula {sgn(r.dpp_lula)} p.p., um dos menores ganhos.", ent_c(r.uf, r.cd_mun, r.municipio)) for r in ext_lo.itertuples()],
        ),
    ],
}
SECOES.append(S5)

# ------------------------------------------------------------------ 6. eliminados x abstenção x brancos e nulos
def comp(g):
    g = g.copy()
    g["G"] = (g.lula_t2 - g.lula_t1) + (g.flavio_t2 - g.flavio_t1)
    g["Ep"] = g.outros_t1 / g.aptos * 100
    g["Ap"] = -(g.abst_t2 - g.abst_t1) / g.aptos * 100
    g["BNp"] = -((g.branco_t2 + g.nulo_t2) - (g.branco_t1 + g.nulo_t1)) / g.aptos * 100
    g["Gp"] = g.G / g.aptos * 100
    g["ret"] = g.G / g.outros_t1 * 100
    return g


T = comp(d[SOMAR].sum().to_frame().T).iloc[0]
UFc = comp(d.groupby("uf")[SOMAR].sum())
Cc = comp(cidades)
Cc = Cc[Cc.aptos >= 20000]


def lc(r, nome, ent):
    ret = fm(r.ret, 0) + "%" if r.ret >= 0 else f"negativa, {sgn(r.ret, 0)}%"
    return linha(
        f"{B(nome)}: eliminados {fm(r.Ep, 1)}% dos aptos; abstenção {'caiu' if r.Ap > 0 else 'subiu'} {fm(abs(r.Ap), 1)} p.p.; "
        f"brancos e nulos {'caíram' if r.BNp > 0 else 'subiram'} {fm(abs(r.BNp), 1)} p.p.; ganho dos dois {sgn(r.Gp, 1)} p.p. (retenção {ret}).",
        ent,
    )


def lcid(r):
    return lc(r, bonito(r.municipio) + "/" + r.uf, ent_c(r.uf, r.cd_mun, r.municipio))


def lest(u):
    return lc(UFc.loc[u], UF_NOME[u], ent_e(u))


gelim = Cc.sort_values("Ep", ascending=False).head(4)
gabst = Cc[Cc.Ap > Cc.Ep].sort_values("ret", ascending=False).head(5)
gengole = Cc.sort_values("Ap").head(6)
lula_ganha = Cc[(Cc.dpp_lula > 1) & (Cc.dpp_flavio < -1) & (Cc.Gp.abs() < 1)].sort_values("aptos", ascending=False).head(5)
bn_cai = Cc.sort_values("BNp", ascending=False).head(4)
bn_sobe = Cc.sort_values("BNp").head(5)
S6 = {
    "id": "eliminados",
    "titulo": "6. Eliminados × abstenção × brancos e nulos",
    "intro": (
        f"O ganho líquido de Lula e Flávio (Δ Lula + Δ Flávio) tem três fontes contábeis: os <b>votos dos eliminados</b> do 1º turno, a <b>queda da abstenção</b> e a <b>queda de brancos e nulos</b>. "
        f"No Brasil, o ganho dos dois foi de {fm(T.G / 1e6, 1)} milhões de votos ({fm(T.Gp, 1)} p.p. dos aptos): {fm(T.outros_t1 / 1e6, 1)} milhões vieram do volume dos eliminados ({pc(T.outros_t1 / T.G)} do ganho), "
        f"{fm(-(T.abst_t2 - T.abst_t1) / 1e6, 1)} milhões da queda da abstenção ({pc(-(T.abst_t2 - T.abst_t1) / T.G)}) e {fm(-((T.branco_t2 + T.nulo_t2) - (T.branco_t1 + T.nulo_t1)) / 1e6, 1)} milhão da queda de brancos e nulos ({pc(-((T.branco_t2 + T.nulo_t2) - (T.branco_t1 + T.nulo_t1)) / T.G)}). "
        "A <b>retenção</b> é o ganho dos dois dividido pelo volume dos eliminados: acima de 100%, entraram votos novos (menos abstenção ou menos brancos e nulos); abaixo de 100% ou negativa, parte desse volume se perdeu em abstenção ou brancos e nulos. "
        "É uma conta de totais: não mostra para onde foi cada eleitor."
    ),
    "itens": [
        item(
            "Onde os eliminados pesaram mais",
            [lest("GO"), lest("DF")] + [lcid(r) for r in gelim.itertuples()],
            "Em Goiás os eliminados somam o maior volume do país (cerca de 12% dos aptos) e a abstenção pesou pouco.",
        ),
        item(
            "Onde a abstenção pesou mais",
            [lest(u) for u in ["BA", "PE", "PB"]] + [lcid(r) for r in gabst.itertuples()],
            "Nessas cidades a queda da abstenção foi maior que o volume dos eliminados, e o ganho dos dois passa de 2 a 5 vezes esse volume.",
        ),
        item(
            "Onde a abstenção engoliu os eliminados",
            [lest(u) for u in ["AP", "AC", "RR", "AM", "TO"]] + [lcid(r) for r in gengole.itertuples()],
            f"No país a abstenção caiu {fm(-(T.abst_t2 - T.abst_t1) / T.aptos * 100, 2)} p.p.; nessas unidades ela subiu e o ganho líquido dos dois ficou menor que o volume dos eliminados (negativo em AP, AC e RR).",
        ),
        item(
            "Lula ganha, Flávio perde e o total fica perto de zero",
            [lcid(r) for r in lula_ganha.itertuples()],
            "Os eliminados foram quase todos compensados pela alta da abstenção; o saldo ficou concentrado no Lula.",
        ),
        item("Queda forte de brancos e nulos", [lest(u) for u in ["AL", "PB"]] + [lcid(r) for r in bn_cai.itertuples()], "Parte do ganho dos dois vem de eleitores que deixaram de votar em branco ou nulo."),
        item("Alta de brancos e nulos", [lcid(r) for r in bn_sobe.itertuples()], "Nessas cidades brancos e nulos subiram e seguraram o ganho dos dois."),
    ],
}
SECOES.append(S6)

GLOSSARIO = [
    {"t": "Variação (p.p.)", "x": "É a diferença entre o 2º e o 1º turno, em pontos percentuais dos eleitores aptos do recorte. +8 p.p. quer dizer que o candidato ganhou, no 2º turno, votos equivalentes a 8% dos aptos."},
    {"t": "Desvio", "x": "Mostra o quanto as áreas de um lugar diferem umas das outras. Desvio pequeno (0,3 p.p.): bairros que variaram quase igual. Desvio grande (5 p.p.): bairros muito diferentes, uns subindo muito e outros pouco ou caindo."},
    {"t": "Correlação", "x": "Vai de −1 a +1 e diz se duas coisas andam juntas. +0,8: onde uma é maior, a outra costuma ser maior. −0,8: onde uma é maior, a outra costuma ser menor. 0: uma não ajuda a prever a outra. Não indica causa."},
    {"t": "R²", "x": "É a parte da diferença de variação entre os locais que o perfil (renda, escolaridade, idade e sexo) consegue explicar. 70%: sabendo o perfil, quase se prevê a variação. 0% ou menos: o perfil não ajuda. O resto vem de fatores que o painel não mede."},
    {"t": "Eliminados, abstenção, brancos e nulos", "x": "O ganho líquido dos dois candidatos = votos dos eliminados do 1º turno + queda da abstenção + queda de brancos e nulos. A retenção compara o ganho com o volume dos eliminados: acima de 100%, entraram votos novos; abaixo, parte se perdeu."},
]
out = {
    "glossario": GLOSSARIO,
    "secoes": SECOES,
    "aviso": "Os casos vêm de regras com corte de tamanho; entre 5.571 cidades e várias métricas, alguns extremos podem aparecer por acaso. Os textos descrevem padrões entre áreas, não causas nem o voto de cada eleitor.",
}
with open("saida/curiosidades.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
n_l = sum(len(i["linhas"]) for s in SECOES for i in s["itens"])
print("saida/curiosidades.json:", n_l, "linhas em", sum(len(s["itens"]) for s in SECOES), "itens")
for s in SECOES:
    print("\n##", s["titulo"])
    for i in s["itens"]:
        print(" -", i["titulo"])
        for l in i["linhas"]:
            print("    ", re.sub("<[^>]+>", "", l["txt"]))
