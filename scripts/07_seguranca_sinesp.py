"""Taxa de CVLI por 100 mil habitantes por município (Sinesp-VDE, últimos 12 meses fechados).

Entrada:  dados/sinesp_vde/bancovde-2025.xlsx e bancovde-2026.xlsx (gov.br/MJSP), saida/locais_renda.parquet (municípios do TSE),
          dados/ibge_municipios/localidades_municipios.json (código IBGE) e sidra_4709_populacao_2022.json (população do Censo 2022)
Saída:    saida/seguranca_municipio.parquet (uma linha por município do TSE)
Rodar da raiz do projeto: .venv/bin/python -I scripts/07_seguranca_sinesp.py
"""
import json
import re
import unicodedata

import pandas as pd

# CVLI = homicídio doloso + feminicídio + latrocínio + lesão corporal seguida de morte (medido em vítimas)
EVENTOS_CVLI = [
    "Homicídio doloso",
    "Feminicídio",
    "Roubo seguido de morte (latrocínio)",
    "Lesão corporal seguida de morte",
]
JANELA = (pd.Timestamp("2025-10-01"), pd.Timestamp("2026-09-01"))  # 12 meses fechados (arquivo atualizado em 26/10/2026)

# grafias diferentes entre TSE e Sinesp (chave normalizada TSE -> chave normalizada Sinesp)
ALIASES = {
    "GO|BOM JESUS": "GO|BOM JESUS DE GOIAS",
    "MG|DONA EUSEBIA": "MG|DONA EUZEBIA",
    "MG|SAO THOME DAS LETRAS": "MG|SAO TOME DAS LETRAS",
    "PA|ELDORADO DOS CARAJAS": "PA|ELDORADO DO CARAJAS",
    "PR|MUNHOZ DE MELLO": "PR|MUNHOZ DE MELO",
    "RN|ASSU": "RN|ACU",
    "RN|AREZ": "RN|ARES",
    "RN|BOA SAUDE": "RN|JANUARIO CICCO",
    "RO|ESPIGAO DO OESTE": "RO|ESPIGAO D OESTE",
    "RO|ALVORADA DO OESTE": "RO|ALVORADA D OESTE",
    "SE|AMPARO DE SAO FRANCISCO": "SE|AMPARO DO SAO FRANCISCO",
    "SE|GRACCHO CARDOSO": "SE|GRACHO CARDOSO",
    "SP|SAO LUIS DO PARAITINGA": "SP|SAO LUIZ DO PARAITINGA",
}


# grafias do TSE diferentes das do IBGE (chave normalizada TSE -> chave normalizada IBGE)
ALIASES_IBGE = {
    "GO|BOM JESUS": "GO|BOM JESUS DE GOIAS",
    "MG|BARAO DE MONTE ALTO": "MG|BARAO DO MONTE ALTO",
    "MG|DONA EUSEBIA": "MG|DONA EUZEBIA",
    "MG|SAO THOME DAS LETRAS": "MG|SAO TOME DAS LETRAS",
    "MT|SANTO ANTONIO DO LEVERGER": "MT|SANTO ANTONIO DE LEVERGER",
    "PA|ELDORADO DOS CARAJAS": "PA|ELDORADO DO CARAJAS",
    "PR|MUNHOZ DE MELLO": "PR|MUNHOZ DE MELO",
    "RN|BOA SAUDE": "RN|JANUARIO CICCO",
    "RO|ESPIGAO DO OESTE": "RO|ESPIGAO D OESTE",
    "RO|ALVORADA DO OESTE": "RO|ALVORADA D OESTE",
    "RR|SAO LUIZ": "RR|SAO LUIZ DO ANAUA",
    "SE|AMPARO DE SAO FRANCISCO": "SE|AMPARO DO SAO FRANCISCO",
    "SP|SAO LUIS DO PARAITINGA": "SP|SAO LUIZ DO PARAITINGA",
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


vde = pd.concat(
    [
        pd.read_excel(f"dados/sinesp_vde/bancovde-{a}.xlsx", usecols=["uf", "municipio", "evento", "data_referencia", "total_vitima", "abrangencia"])
        for a in (2025, 2026)
    ]
)
vde = vde[vde.evento.isin(EVENTOS_CVLI) & (vde.abrangencia == "Estadual") & vde.data_referencia.between(*JANELA)]
meses = vde.data_referencia.nunique()
assert meses == 12, meses
vde["k"] = vde.uf + "|" + vde.municipio.map(norm)
# o Distrito Federal vem uma linha por região administrativa: a soma por chave resolve
cvli = vde.groupby("k", as_index=False).total_vitima.sum().rename(columns={"total_vitima": "cvli_12m"})

loc = pd.read_parquet("saida/locais_renda.parquet", columns=["uf", "cd_mun", "municipio"])
mun = loc.drop_duplicates(["uf", "cd_mun"]).reset_index(drop=True)
mun["k_ibge"] = (mun.uf + "|" + mun.municipio.map(norm)).replace(ALIASES_IBGE)
mun["k"] = (mun.uf + "|" + mun.municipio.map(norm)).replace(ALIASES)

# código IBGE pelo nome (lista oficial de municípios do IBGE) e população residente do Censo 2022 (SIDRA, tabela 4709)
ibge = pd.DataFrame(
    [(str(m["id"]), m["microrregiao"]["mesorregiao"]["UF"]["sigla"] if m.get("microrregiao") else m["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"], m["nome"]) for m in json.load(open("dados/ibge_municipios/localidades_municipios.json"))],
    columns=["cd_mun_ibge", "uf", "nome"],
)
ibge["k_ibge"] = ibge.uf + "|" + ibge.nome.map(norm)
assert not ibge.k_ibge.duplicated().any()
pop = pd.DataFrame(
    [(x["localidade"]["id"], float(x["serie"]["2022"])) for x in json.load(open("dados/ibge_municipios/sidra_4709_populacao_2022.json"))[0]["resultados"][0]["series"] if x["serie"]["2022"].replace(".", "").isdigit()],
    columns=["cd_mun_ibge", "pop_2022"],
)
mun = mun.merge(ibge[["k_ibge", "cd_mun_ibge"]], on="k_ibge", how="left")
assert not mun.cd_mun_ibge.dropna().duplicated().any(), "dois municípios do TSE com o mesmo código IBGE"
faltam = mun[mun.cd_mun_ibge.isna()]
assert faltam.empty, f"municípios do TSE sem código IBGE: {faltam[['uf', 'municipio']].values.tolist()}"
mun = mun.drop(columns="k_ibge")

out = mun.merge(cvli, on="k", how="left").merge(pop, on="cd_mun_ibge", how="left")
out["taxa_cvli_100k"] = out.cvli_12m / out.pop_2022 * 1e5
out = out.drop(columns="k")
out.to_parquet("saida/seguranca_municipio.parquet", index=False)

print("municípios:", len(out), "| sem CVLI (sem par no Sinesp):", out.cvli_12m.isna().sum(), "| sem população:", out.pop_2022.isna().sum())
print("vítimas na janela:", int(vde.total_vitima.sum()), "| atribuídas a municípios do painel:", int(out.cvli_12m.sum()))
print("taxa Brasil (100 mil):", round(out.cvli_12m.sum() / out.pop_2022[out.cvli_12m.notna()].sum() * 1e5, 2))
print(out.sort_values("taxa_cvli_100k").tail(5).to_string())
