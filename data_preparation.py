# data_preparation.py
# ============================================================
# Carrega o CUBO AGREGADO do Vigitel (preferir WIDE .parquet)
# e aplica redução agressiva de memória (downcast + category).
# ------------------------------------------------------------
# Saídas exportadas para o app:
#   - df_cubo: DataFrame leve (parquet/csv wide ou derivado do long)
#   - META: metadados (listas de dimensões e indicadores)
# ============================================================

from __future__ import annotations
from pathlib import Path
import unicodedata
import numpy as np
import pandas as pd

# Onde ficam os arquivos do cubo
CUBO_DIR = Path("outputs")

# Ordem preferida de leitura (mais leve -> mais pesado)
WIDE_FIRST = [
    CUBO_DIR / "cubo_vigitel_wide.parquet",
    CUBO_DIR / "cubo_vigitel_wide.csv",
]
LONG_FALLBACK = [
    CUBO_DIR / "cubo_vigitel_long.parquet",
    CUBO_DIR / "cubo_vigitel_long.csv",
]

# Dimensões padrão
DIM_COLS = ["ano", "cidade_nome", "sexo", "faixa_etaria", "faixa_escolaridade"]

# Normalização leve para nomes de cidades
def _norm_str(s: pd.Series) -> pd.Series:
    s = s.astype("string")
    s = s.str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("utf-8")
    return s.str.strip().str.lower()

def _to_int16(x: pd.Series) -> pd.Series:
    return pd.to_numeric(x, errors="coerce").astype("Int16")

def _downcast_dims(df: pd.DataFrame) -> pd.DataFrame:
    if "ano" in df.columns:
        df["ano"] = _to_int16(df["ano"])
    for c in ("cidade_nome", "sexo", "faixa_etaria", "faixa_escolaridade"):
        if c in df.columns:
            df[c] = _norm_str(df[c]).astype("category")
    return df

def _find_file(paths) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None

def _wide_from_long(df_long: pd.DataFrame) -> pd.DataFrame:
    # Espera colunas: DIM_COLS + ["indicador", "prevalencia"]
    base_cols = [c for c in DIM_COLS if c in df_long.columns]
    long_min = df_long[base_cols + ["indicador", "prevalencia"]].copy()
    wide = (
        long_min
        .pivot_table(index=base_cols, columns="indicador", values="prevalencia")
        .reset_index()
    )
    wide.columns = [f"prev_{c}" if c not in base_cols else c for c in wide.columns]
    return wide

def _downcast_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # Tudo que começa com "prev_" vira float32
    for c in df.columns:
        if c.startswith("prev_"):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
    return df

def load_cubo() -> tuple[pd.DataFrame, dict]:
    # 1) tenta WIDE
    f_wide = _find_file(WIDE_FIRST)
    if f_wide is not None:
        if f_wide.suffix == ".parquet":
            df = pd.read_parquet(f_wide)
        else:
            df = pd.read_csv(f_wide)
        df = _downcast_dims(df)
        df = _downcast_indicators(df)

    else:
        # 2) fallback para LONG e deriver WIDE in-memory (ainda barato)
        f_long = _find_file(LONG_FALLBACK)
        if f_long is None:
            raise FileNotFoundError(
                "Cubo não encontrado. Gere com gerar_cubo_vigitel.py "
                f"({WIDE_FIRST[0].as_posix()} ou {LONG_FALLBACK[0].as_posix()})"
            )
        if f_long.suffix == ".parquet":
            df_long = pd.read_parquet(f_long, columns=[*DIM_COLS, "indicador", "prevalencia"])
        else:
            usecols = [*DIM_COLS, "indicador", "prevalencia"]
            df_long = pd.read_csv(f_long, usecols=[c for c in usecols if c in pd.read_csv(f_long, nrows=0).columns])

        df_long = _downcast_dims(df_long)
        df = _wide_from_long(df_long)
        df = _downcast_dims(df)
        df = _downcast_indicators(df)

    # Filtra linhas inválidas (ano/cidade vazios)
    df = df.dropna(subset=[c for c in ("ano", "cidade_nome") if c in df.columns]).reset_index(drop=True)

    # Metadados mínimos
    indicators = [c for c in df.columns if c.startswith("prev_")]
    indicators.sort()
    anos = sorted([int(a) for a in df["ano"].dropna().unique()])
    cidades = df["cidade_nome"].cat.categories.tolist() if hasattr(df["cidade_nome"], "cat") else sorted(df["cidade_nome"].dropna().unique().tolist())
    sexos = df["sexo"].cat.categories.tolist() if ("sexo" in df and hasattr(df["sexo"], "cat")) else sorted(df.get("sexo", pd.Series(dtype="string")).dropna().unique().tolist())
    fet = df["faixa_etaria"].cat.categories.tolist() if ("faixa_etaria" in df and hasattr(df["faixa_etaria"], "cat")) else sorted(df.get("faixa_etaria", pd.Series(dtype="string")).dropna().unique().tolist())
    fesc = df["faixa_escolaridade"].cat.categories.tolist() if ("faixa_escolaridade" in df and hasattr(df["faixa_escolaridade"], "cat")) else sorted(df.get("faixa_escolaridade", pd.Series(dtype="string")).dropna().unique().tolist())

    META = {
        "indicators": indicators,
        "anos": anos,
        "cidades": cidades,
        "sexos": sexos,
        "faixa_etaria": fet,
        "faixa_escolaridade": fesc,
    }
    return df, META

