# analysis_engine.py
# Contém a função principal para cálculos estatísticos ponderados.

import pandas as pd
import numpy as np

def calculate_weighted_proportions(df: pd.DataFrame, indicator: str, group_by: list):
    """
    Calcula a prevalência ponderada, o erro padrão e o intervalo de confiança de 95%
    para um dado indicador, agrupado pelas colunas especificadas.

    Args:
        df (pd.DataFrame): O DataFrame contendo os microdados.
        indicator (str): O nome da coluna do indicador (binário 0/1).
        group_by (list): Uma lista de colunas para agrupar os resultados.

    Returns:
        pd.DataFrame: Um DataFrame com as prevalências e intervalos de confiança por grupo.
    """
    if indicator not in df.columns or 'pesorake' not in df.columns:
        return pd.DataFrame()

    # Garante que o indicador e o peso sejam numéricos e lida com NaNs
    data = df[group_by + [indicator, 'pesorake']].copy()
    data[indicator] = pd.to_numeric(data[indicator], errors='coerce').fillna(0)
    data['pesorake'] = pd.to_numeric(data['pesorake'], errors='coerce').fillna(0)

    # Agrupamento e cálculo
    grouped = data.groupby(group_by)
    
    results =
    for name, group in grouped:
        n = len(group)
        w_sum = group['pesorake'].sum()

        if w_sum > 0:
            # Prevalência ponderada (p_hat)
            prev = (group[indicator] * group['pesorake']).sum() / w_sum
            
            # Cálculo do Erro Padrão para proporção ponderada em amostragem complexa
            # Var(p_hat) ≈ (1/w_sum^2) * Σ [w_i^2 * (y_i - p_hat)^2]
            # Simplificação comum assume um fator de correção de desenho (DEFF), mas para
            # visualização, uma aproximação robusta é suficiente.
            # Erro padrão (SE) = sqrt(Var(p_hat))
            variance = np.sum(group['pesorake']**2 * (group[indicator] - prev)**2) / (w_sum**2)
            se = np.sqrt(variance)
            
            # Intervalo de Confiança de 95% (z-score ≈ 1.96)
            z_score = 1.96
            lower_ci = prev - z_score * se
            upper_ci = prev + z_score * se
            
            # Junta os resultados
            res = dict(zip(group_by, name)) if isinstance(name, tuple) else {group_by: name}
            res.update({
                'n': n,
                'prevalencia': prev,
                'erro_padrao': se,
                'ic_inferior': lower_ci,
                'ic_superior': upper_ci
            })
            results.append(res)

    if not results:
        return pd.DataFrame()
        
    return pd.DataFrame(results)