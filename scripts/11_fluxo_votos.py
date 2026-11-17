"""Fluxo estimado de votos do 1º para o 2º turno (matriz de transição por inferência ecológica).

Entrada:  saida/base_secao.parquet (script 01), dados/votacao_secao_2026_BR/votacao_secao_2026_BR.csv (votos por candidato no 1º turno),
          saida/locais_dashboard.parquet (região de cada UF)
Saída:    saida/fluxo_votos.json (bloco "Para onde foram os votos" do painel)
Rodar da raiz do projeto: .venv/bin/python -I scripts/11_fluxo_votos.py   (com "teste" no fim, só o Brasil)

Método: em cada seção, a parcela de eleitores aptos que vai para cada destino no 2º turno é a mistura das parcelas de origem do 1º turno:
    y_ij = soma_k T_kj * x_ik + erro        (regressão de Goodman com restrições)
x_ik = parcela dos aptos da seção i na origem k (Lula, Flávio, Cury, Renan, Caiado, Zema e outros, brancos e nulos, abstenção),
y_ij = parcela no destino j (Lula, Flávio, brancos e nulos, abstenção) e T_kj = fração da origem k que foi para o destino j, igual para todas as
seções do recorte. Restrições: cada linha de T soma 1 e T >= 0. Mínimos quadrados ponderados pelos aptos. Depois os fluxos (T x votos da origem)
são ajustados (IPF) para somar exatamente os totais observados de cada origem e de cada destino.
Margem de erro: bootstrap por conglomerados (municípios; locais de votação quando o recorte tem menos de 30 municípios), 95% por percentis.
É uma estimativa: supõe que a taxa de transição é a mesma em todas as seções do recorte (falácia ecológica).
"""
import json
import sys
import time

import duckdb
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import minimize

B = 300  # réplicas do bootstrap
MIN_SECOES = 300  # cidades com menos seções não têm estimativa
MIN_MUN = 30  # abaixo disso o conglomerado é o local de votação, não o município
ORIG = ["Lula", "Flávio", "Cury", "Renan Santos", "Caiado", "Zema e outros", "Brancos e nulos", "Abstenção"]
DEST = ["Lula", "Flávio", "Brancos e nulos", "Abstenção"]
K, J = len(ORIG), len(DEST)
CAND = {"cury": "AUGUSTO JORGE CURY", "renan": "RENAN ANTONIO FERREIRA DOS SANTOS", "caiado": "RONALDO RAMOS CAIADO"}
TESTE = len(sys.argv) > 1 and sys.argv[1] == "teste"

# ------------------------------------------------------------------ base por seção
b = pd.read_parquet("saida/base_secao.parquet")
reg = pd.read_parquet("saida/locais_dashboard.parquet", columns=["uf", "regiao"]).drop_duplicates("uf").set_index("uf").regiao
b = b[b.uf.isin(reg.index)]  # sem o exterior (ZZ), como no resto do painel
b = b[(b.instalada_t1 == "Sim") & (b.instalada_t2 == "Sim") & (b.aptos_t1 > 0)].copy()
con = duckdb.connect()
csv = "read_csv('dados/votacao_secao_2026_BR/votacao_secao_2026_BR.csv', delim=';', quote='\"', header=true, encoding='latin-1', all_varchar=true)"
casos = ",\n".join(f"sum(case when NM_VOTAVEL = '{n}' then QT_VOTOS::int else 0 end) as {k}" for k, n in CAND.items())
cand = con.sql(f"""
select SG_UF as uf, lpad(CD_MUNICIPIO, 5, '0') as cd_mun, NR_ZONA::int as zona, NR_SECAO::int as secao, {casos}
from {csv} where DS_CARGO = 'Presidente' and NR_TURNO = '1' group by all
""").df()
b = b.merge(cand, on=["uf", "cd_mun", "zona", "secao"], how="left").fillna({k: 0 for k in CAND})
b["zema_outros"] = b.outros_t1 - b.cury - b.renan - b.caiado
assert (b.zema_outros >= 0).all(), "candidatos nomeados somam mais que 'outros'"

X = np.column_stack([b.lula_t1, b.flavio_t1, b.cury, b.renan, b.caiado, b.zema_outros, b.branco_t1 + b.nulo_t1, b.abst_t1]).astype(float)
Y = np.column_stack([b.lula_t2, b.flavio_t2, b.branco_t2 + b.nulo_t2, b.abst_t2]).astype(float)
ok = (X.sum(1) > 0) & (Y.sum(1) > 0) & (np.abs(X.sum(1) - Y.sum(1)) <= 0.01 * X.sum(1))  # seções cujas parcelas somam os mesmos aptos nos dois turnos
print(f"seções: {len(b)} | usadas: {ok.sum()} | fora (aptos diferentes entre turnos ou sem votos): {(~ok).sum()}")
b, X, Y = b[ok].reset_index(drop=True), X[ok], Y[ok]
w = X.sum(1)  # aptos da seção
Xs, Ys = X / w[:, None], Y / Y.sum(1)[:, None]
AO = (w[:, None, None] * Xs[:, :, None] * Xs[:, None, :]).reshape(len(b), K * K)  # estatísticas suficientes por seção
BO = (w[:, None, None] * Xs[:, :, None] * Ys[:, None, :]).reshape(len(b), K * J)

b["regiao"] = b.uf.map(reg)
b["mun_cod"] = b.uf + b.cd_mun
b["loc_cod"] = b.mun_cod + "|" + b.zona.astype(str) + "|" + b.nr_local.astype(str)
assert b.groupby(["uf", "municipio"]).cd_mun.nunique().max() == 1, "nome de município repetido na UF"


# ------------------------------------------------------------------ estimador
def solve(A, Bm, T0):
    """Mínimos quadrados com T >= 0 e linhas somando 1 (problema quadrático pequeno, K x J variáveis)."""
    esc = np.trace(A) / K
    A, Bm = A / esc, Bm / esc

    def f(v):
        T = v.reshape(K, J)
        g = 2 * (A @ T - Bm)
        return float((T * (A @ T - 2 * Bm)).sum()), g.ravel()

    soma = np.zeros((K, K * J))
    for k in range(K):
        soma[k, k * J:(k + 1) * J] = 1
    r = minimize(f, T0.ravel(), jac=True, method="SLSQP", bounds=[(0, 1)] * (K * J), constraints=[{"type": "eq", "fun": lambda v: soma @ v - 1, "jac": lambda v: soma}], options={"maxiter": 300, "ftol": 1e-12})
    return np.clip(r.x.reshape(K, J), 0, None)


def rake(F, lin, col, it=200):
    """IPF: ajusta os fluxos aos totais de origem (linhas) e de destino (colunas)."""
    F = np.maximum(F, 1e-9)
    col = col * lin.sum() / col.sum()
    for _ in range(it):
        F *= (lin / F.sum(1))[:, None]
        F *= (col / F.sum(0))[None, :]
        if np.abs(F.sum(1) - lin).max() < 1e-6 * lin.sum():
            break
    return F


def estimar(idx, cluster):
    """Fluxos (votos) estimados e intervalo de 95% para as seções idx; cluster = rótulos dos conglomerados."""
    cod, uniq = pd.factorize(cluster[idx])
    S = sparse.csr_matrix((np.ones(len(idx)), (cod, np.arange(len(idx)))), shape=(len(uniq), len(idx)))
    Ac, Bc = S @ AO[idx], S @ BO[idx]
    lin, col = (w[idx, None] * Xs[idx]).sum(0), (w[idx, None] * Ys[idx]).sum(0)
    T0 = np.tile(Y[idx].sum(0) / Y[idx].sum(), (K, 1))
    A, Bm = Ac.sum(0).reshape(K, K), Bc.sum(0).reshape(K, J)
    T = solve(A, Bm, T0)
    F = rake(T * lin[:, None], lin, col)
    n = len(uniq)
    boot = np.empty((B, K, J))
    for i in range(B):
        c = np.bincount(RNG.integers(0, n, n), minlength=n)
        boot[i] = rake(solve((c @ Ac).reshape(K, K), (c @ Bc).reshape(K, J), T) * lin[:, None], lin, col)
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    return {"secoes": int(len(idx)), "conglomerados": int(n), "orig": np.round(lin).astype(int).tolist(), "dest": np.round(col).astype(int).tolist(),
            "f": np.round(F).astype(int).tolist(), "lo": np.round(lo).astype(int).tolist(), "hi": np.round(hi).astype(int).tolist()}


RNG = np.random.default_rng(2026)
saida = {"meta": {"orig": ORIG, "dest": DEST, "reps": B, "min_secoes": MIN_SECOES, "min_mun": MIN_MUN}, "rec": {}}
tarefas = [("Brasil", np.arange(len(b)))]
if not TESTE:
    tarefas += [(r, np.flatnonzero((b.regiao == r).values)) for r in sorted(b.regiao.unique())]
    tarefas += [(u, np.flatnonzero((b.uf == u).values)) for u in sorted(b.uf.unique())]
    cs = b.groupby(["uf", "municipio"]).size()
    cs = cs[cs >= MIN_SECOES]
    tarefas += [(f"{u}|{m}", np.flatnonzero(((b.uf == u) & (b.municipio == m)).values)) for (u, m) in cs.index]
print(f"recortes: {len(tarefas)} (cidades com {MIN_SECOES}+ seções: {len(tarefas) - 1 - 5 - 27 if not TESTE else '-'})")

t0 = time.time()
for i, (chave, idx) in enumerate(tarefas):
    nmun = b.mun_cod.values[idx]
    cluster = b.mun_cod.values if len(set(nmun)) >= MIN_MUN else b.loc_cod.values
    r = estimar(idx, cluster)
    r["cluster"] = "município" if len(set(nmun)) >= MIN_MUN else "local de votação"
    saida["rec"][chave] = r
    if i < 3 or i % 25 == 0:
        print(f"[{i + 1}/{len(tarefas)}] {chave}: {len(idx)} seções, {r['conglomerados']} conglomerados ({r['cluster']}) | {time.time() - t0:.0f}s")

json.dump(saida, open("saida/fluxo_votos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"saida/fluxo_votos.json: {len(json.dumps(saida)) / 1e3:.0f} KB | {time.time() - t0:.0f}s")

# conferência no Brasil: matriz em % das origens, com o intervalo
r = saida["rec"]["Brasil"]
F, lo, hi, lin = (np.array(r[k], float) for k in ("f", "lo", "hi", "orig"))
print("\nBrasil: % de cada origem que foi para cada destino (intervalo 95%)")
print(pd.DataFrame([[f"{F[k, j] / lin[k] * 100:4.1f} [{lo[k, j] / lin[k] * 100:4.1f}-{hi[k, j] / lin[k] * 100:4.1f}]" for j in range(J)] for k in range(K)], index=[f"{o} ({lin[k] / 1e6:.2f} mi)" for k, o in enumerate(ORIG)], columns=DEST).to_string())
print("destinos estimados x observados:", np.round(F.sum(0)).astype(int).tolist(), r["dest"])
