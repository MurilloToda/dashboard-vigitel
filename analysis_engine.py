# analysis_engine.py
import pandas as pd
import numpy as np

def calculate_weighted_proportions(df: pd.DataFrame, indicator: str, group_by: list):
    """
    Prevalência ponderada + erro padrão + IC95%, por grupos.
    Assume indicador binário (0/1) e peso 'pesorake'.
    """
    if indicator not in df.columns or 'pesorake' not in df.columns:
        return pd.DataFrame()

    data = df[group_by + [indicator, 'pesorake']].copy()
    data[indicator] = pd.to_numeric(data[indicator], errors='coerce').fillna(0)
    data['pesorake'] = pd.to_numeric(data['pesorake'], errors='coerce').fillna(0)

    results = []
    for name, g in data.groupby(group_by, dropna=False):
        n = len(g)
        w_sum = g['pesorake'].sum()
        if w_sum <= 0:
            continue

        prev = (g[indicator] * g['pesorake']).sum() / w_sum
        # Var ≈ ( Σ w_i^2 * (y_i - p)^2 ) / (Σ w_i)^2
        variance = np.sum((g['pesorake'] ** 2) * (g[indicator] - prev) ** 2) / (w_sum ** 2)
        se = float(np.sqrt(variance))
        z = 1.96
        lower = max(0.0, prev - z * se)
        upper = min(1.0, prev + z * se)

        if isinstance(name, tuple):
            row = dict(zip(group_by, name))
        else:
            row = {group_by[0]: name}
        row.update({
            'n': n,
            'prevalencia': float(prev),
            'erro_padrao': se,
            'ic_inferior': float(lower),
            'ic_superior': float(upper),
        })
        results.append(row)

    return pd.DataFrame(results)
