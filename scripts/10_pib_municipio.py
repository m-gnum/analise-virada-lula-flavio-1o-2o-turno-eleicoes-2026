"""PIB per capita municipal (IBGE, PIB dos Municípios 2023) para a coluna de PIB per capita da tabela "Variação por unidade".

Entrada:  dados/ibge_pib/pib_municipios_2010_2023.xlsx (IBGE, base de dados do PIB dos Municípios 2010-2023; ver 00_baixar_dados.sh),
          saida/seguranca_municipio.parquet (código IBGE de cada município do TSE; script 07)
Saída:    saida/pib_municipio.parquet (uma linha por município do TSE: pib_2023_mil, pib_per_capita e pop_pib, a população implícita do IBGE)
O per capita é o publicado pelo IBGE. A população implícita (PIB / per capita) serve para agregar: no painel, o PIB de um conjunto de
municípios é somado e dividido pela soma dessa população (não é a média dos per capita).
Rodar da raiz do projeto: .venv/bin/python -I scripts/10_pib_municipio.py
"""
import pandas as pd

seg = pd.read_parquet("saida/seguranca_municipio.parquet")[["uf", "cd_mun", "municipio", "cd_mun_ibge"]]
x = pd.read_excel("dados/ibge_pib/pib_municipios_2010_2023.xlsx")
x = x[x["Ano"] == 2023]


def col(ini):
    return next(c for c in x.columns if c.startswith(ini))


pib = pd.DataFrame({"cd_mun_ibge": x["Código do Município"].astype(str), "pib_2023_mil": x[col("Produto Interno Bruto, ")].values, "pib_per_capita": x[col("Produto Interno Bruto per capita")].values})
assert len(pib) == 5570 and not pib.cd_mun_ibge.duplicated().any()

out = seg.merge(pib, on="cd_mun_ibge", how="left")
out["pop_pib"] = out.pib_2023_mil * 1000 / out.pib_per_capita
print("municípios:", len(out), "| sem PIB:", out.pib_2023_mil.isna().sum(), "| PIB Brasil (R$ tri):", round(out.pib_2023_mil.sum() / 1e9, 2))
print("PIB per capita Brasil (R$):", round(out.pib_2023_mil.sum() * 1000 / out.pop_pib.sum()))
print(out.sort_values("pib_per_capita").dropna(subset=["pib_per_capita"]).iloc[[0, -1]][["municipio", "uf", "pib_per_capita"]].to_string(index=False))
out[["uf", "cd_mun", "pib_2023_mil", "pib_per_capita", "pop_pib"]].to_parquet("saida/pib_municipio.parquet", index=False)
