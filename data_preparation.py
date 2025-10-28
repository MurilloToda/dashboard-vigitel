# data_preparation.py
import pandas as pd
import numpy as np

def to_numeric_silent(series):
    return pd.to_numeric(series, errors='coerce')

def prepare_data(parquet_path: str) -> pd.DataFrame:
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        print(f"Erro ao ler o arquivo Parquet: {e}")
        return pd.DataFrame()

    # Demografia básica
    df['q6'] = to_numeric_silent(df.get('q6'))           # Idade
    df['q8_anos'] = to_numeric_silent(df.get('q8_anos')) # Escolaridade (anos)
    df['q7'] = to_numeric_silent(df.get('q7'))           # Sexo
    df['ano'] = to_numeric_silent(df.get('ano'))
    if 'cidade_nome' in df.columns:
        df['cidade_nome'] = df['cidade_nome'].astype('string')

    # Faixas
    age_bins = [17, 24, 34, 44, 54, 64, np.inf]
    age_labels = ['18-24 anos','25-34 anos','35-44 anos','45-54 anos','55-64 anos','65+ anos']
    df['faixa_etaria'] = pd.cut(df['q6'], bins=age_bins, labels=age_labels, right=True)

    edu_bins = [-1, 8, 11, np.inf]
    edu_labels = ['0-8 anos','9-11 anos','12+ anos']
    df['faixa_escolaridade'] = pd.cut(df['q8_anos'], bins=edu_bins, labels=edu_labels, right=True)

    # Sexo
    sexo_map = {1: 'Masculino', 2: 'Feminino'}
    df['sexo'] = df['q7'].map(sexo_map)

    # IMC / Excesso de peso / Obesidade (valores extremos tratados)
    peso = to_numeric_silent(df.get('q9'))
    alt_cm = to_numeric_silent(df.get('q11'))
    imc = peso / ((alt_cm / 100) ** 2)
    imc[(alt_cm >= 700) | (peso >= 700)] = np.nan  # sentinelas conforme dicionário
    imc[(imc < 10) | (imc > 100)] = np.nan
    df['imc'] = imc
    df['excpeso'] = np.where(df['imc'] >= 25, 1, 0)
    df['obesid']  = np.where(df['imc'] >= 30, 1, 0)

    # Álcool abusivo (q37 homem; q38 mulher)
    cond_h = (df['sexo'] == 'Masculino') & (to_numeric_silent(df.get('q37')) == 1)
    cond_m = (df['sexo'] == 'Feminino') & (to_numeric_silent(df.get('q38')) == 1)
    df['abuso_alcool'] = np.where(cond_h | cond_m, 1, 0)

    # Morbidades autorreferidas
    df['hipertensao'] = np.where(to_numeric_silent(df.get('q75')) == 1, 1, 0)
    df['diabetes']    = np.where(to_numeric_silent(df.get('q76')) == 1, 1, 0)  # << q76

    # Garante indicadores (se faltarem, cria como NaN)
    indicator_cols = [
        'ativo_lazer_unif','atitrans','atiocu','atidom','inativo',
        'af3dominios','af3dominios_insu','excpeso','obesid',
        'abuso_alcool','hipertensao','diabetes'
    ]
    for col in indicator_cols:
        if col not in df.columns:
            df[col] = np.nan
        else:
            df[col] = to_numeric_silent(df[col])

    # Essenciais para o app
    must = ['ano','cidade_nome','sexo','faixa_etaria','faixa_escolaridade','pesorake']
    for c in must:
        if c not in df.columns:
            df[c] = np.nan
    df.dropna(subset=must, inplace=True)

    return df
