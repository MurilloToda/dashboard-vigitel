# data_preparation.py
import pandas as pd
import numpy as np

# Colunas realmente usadas no app (atividade física + demografia + pesos)
COLS = [
    "ano","cidade_nome","pesorake","q6","q8_anos","q7",  # demografia
    "ativo_lazer_unif","atitrans","atiocu","atidom","inativo",
    "af3dominios","af3dominios_insu",
    # Nutrição/IMC/álcool/morbidades (para as outras páginas)
    "q9","q11","q37","q38","q75","q76","excpeso","obesid"
]

def _to_num(s): return pd.to_numeric(s, errors="coerce")

def prepare_data(parquet_path: str) -> pd.DataFrame:
    # Lê só as colunas necessárias
    try:
        df = pd.read_parquet(parquet_path, columns=COLS, engine="pyarrow")
    except Exception as e:
        print(f"Erro ao ler Parquet: {e}")
        return pd.DataFrame()

    # ---------- Downcast forte ----------
    # numéricos pequenos
    for c in ["ano","q6","q7"]:
        if c in df.columns:
            df[c] = _to_num(df[c]).astype("Int16")

    if "q8_anos" in df.columns:
        df["q8_anos"] = _to_num(df["q8_anos"]).astype("Int16")

    if "pesorake" in df.columns:
        df["pesorake"] = _to_num(df["pesorake"]).astype("float32")

    # indicadores binários -> Int8
    for c in ["ativo_lazer_unif","atitrans","atiocu","atidom","inativo",
              "af3dominios","af3dominios_insu","excpeso","obesid"]:
        if c in df.columns:
            df[c] = _to_num(df[c]).astype("Int8")

    # medidas p/ IMC e álcool/morbidades
    for c in ["q9","q11","q37","q38","q75","q76"]:
        if c in df.columns:
            df[c] = _to_num(df[c]).astype("float32")

    # ---------- Derivações leves e categorizações ----------
    # Sexo
    if "q7" in df.columns:
        sexo_map = {1: "Masculino", 2: "Feminino"}
        df["sexo"] = df["q7"].map(sexo_map).astype("category")
    else:
        df["sexo"] = pd.Categorical([])

    # Faixa etária
    if "q6" in df.columns:
        age_bins = [17, 24, 34, 44, 54, 64, np.inf]
        age_labels = ['18-24 anos','25-34 anos','35-44 anos','45-54 anos','55-64 anos','65+ anos']
        df["faixa_etaria"] = pd.cut(df["q6"].astype("float32"), bins=age_bins,
                                    labels=age_labels, right=True).astype("category")
    else:
        df["faixa_etaria"] = pd.Categorical([])

    # Escolaridade
    if "q8_anos" in df.columns:
        edu_bins = [-1, 8, 11, np.inf]
        edu_labels = ['0-8 anos','9-11 anos','12+ anos']
        df["faixa_escolaridade"] = pd.cut(df["q8_anos"].astype("float32"),
                                          bins=edu_bins, labels=edu_labels,
                                          right=True).astype("category")
    else:
        df["faixa_escolaridade"] = pd.Categorical([])

    # Cidades como categoria
    if "cidade_nome" in df.columns:
        df["cidade_nome"] = df["cidade_nome"].astype("string").astype("category")

    # Mantém só o essencial para o app (remove colunas cruas grandes)
    keep = ["ano","cidade_nome","pesorake","sexo","faixa_etaria","faixa_escolaridade",
            "ativo_lazer_unif","atitrans","atiocu","atidom","inativo",
            "af3dominios","af3dominios_insu","excpeso","obesid"]
    exist = [c for c in keep if c in df.columns]
    df = df[exist].copy()

    # Garante ordenação e índices compactos
    df.sort_values(["ano","cidade_nome"], inplace=True, ignore_index=True)

    return df
