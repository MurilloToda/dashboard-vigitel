# analysis_engine.py
# ============================================================
# Funções puras de análise/filtragem sobre o CUBO WIDE
# (sem estados globais; resultados pequenos → baixo uso de RAM)
# ============================================================

from __future__ import annotations
import numpy as np
import pandas as pd

DIM_COLS = ["ano", "cidade_nome", "sexo", "faixa_etaria", "faixa_escolaridade"]

def _apply_filters(df: pd.DataFrame,
                   anos: list[int] | None = None,
                   cidades: list[str] | None = None,
                   sexos: list[str] | None = None,
                   fet: list[str] | None = None,
                   fesc: list[str] | None = None) -> pd.DataFrame:
    out = df
    if anos:
        out = out[out["ano"].isin(anos)]
    if cidades and "cidade_nome" in out:
        out = out[out["cidade_nome"].isin(cidades)]
    if sexos and "sexo" in out:
        out = out[out["sexo"].isin(sexos)]
    if fet and "faixa_etaria" in out:
        out = out[out["faixa_etaria"].isin(fet)]
    if fesc and "faixa_escolaridade" in out:
        out = out[out["faixa_escolaridade"].isin(fesc)]
    return out

def series_evolucao(df: pd.DataFrame, indicador: str, cidades: list[str], anos: list[int] | None = None) -> pd.DataFrame:
    # Linha: ano x cidade (prevalência média simples dos filtros remanescentes)
    cols = ["ano", "cidade_nome", indicador]
    subset = _apply_filters(df, anos=anos, cidades=cidades)[cols].dropna(subset=[indicador])
    if subset.empty:
        return subset
    res = (subset
           .groupby(["ano", "cidade_nome"], as_index=False, sort=True)[indicador]
           .mean())  # já está agregado no cubo; média simples sobre estratos filtrados
    return res

def barras_categoria(df: pd.DataFrame, indicador: str, dim: str,
                     ano: int, cidade: str) -> pd.DataFrame:
    # Barras: uma dimensão categórica (sexo/fet/fesc)
    if dim not in DIM_COLS:
        raise ValueError(f"Dimensão inválida: {dim}")
    cols = [dim, indicador]
    sub = _apply_filters(df, anos=[ano], cidades=[cidade])[cols].dropna(subset=[indicador])
    if sub.empty:
        return sub
    res = sub.groupby(dim, as_index=False)[indicador].mean()
    return res

def ranking_capitais(df: pd.DataFrame, indicador: str, ano: int, top_k: int = 10) -> pd.DataFrame:
    # Ranking simples por capital no ano
    cols = ["cidade_nome", indicador]
    sub = _apply_filters(df, anos=[ano])[cols].dropna(subset=[indicador])
    if sub.empty:
        return sub
    res = sub.groupby("cidade_nome", as_index=False)[indicador].mean()
    res = res.sort_values(indicador, ascending=False, kind="mergesort")
    return res.head(top_k)

def ultimo_ano_disponivel(df: pd.DataFrame) -> int:
    return int(df["ano"].max())

def primeiras_cidades(df: pd.DataFrame, n: int = 6) -> list[str]:
    # escolhe as N mais frequentes (estáveis pra vitrine)
    if "cidade_nome" not in df.columns:
        return []
    freq = df["cidade_nome"].value_counts()
    return freq.head(n).index.tolist()
