# data_preparation.py
# Este script carrega os dados e cria as variáveis demográficas necessárias para o dashboard.

import pandas as pd
import numpy as np

def to_numeric_silent(series):
    """Converte uma série para tipo numérico, tratando erros silenciosamente."""
    return pd.to_numeric(series, errors='coerce')

def prepare_data(parquet_path: str) -> pd.DataFrame:
    """
    Carrega e prepara os dados do VIGITEL para uso no dashboard.
    Enriquece o DataFrame com colunas categóricas para idade e escolaridade.
    """
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        print(f"Erro ao ler o arquivo Parquet: {e}")
        # Retorna um DataFrame vazio em caso de erro para não quebrar a aplicação
        return pd.DataFrame()

    # --- Limpeza e Conversão de Tipos ---
    # Garante que as colunas demográficas chave sejam numéricas
    df['q6'] = to_numeric_silent(df['q6'])       # Idade
    df['q8_anos'] = to_numeric_silent(df['q8_anos']) # Anos de estudo
    df['q7'] = to_numeric_silent(df['q7'])       # Sexo

    # --- Criação de Faixa Etária ---
    # As faixas são baseadas nas tabelas sociodemográficas do relatório VIGITEL 2023 
    age_bins = [17, 24, 34, 44, 54, 64, np.inf]
    age_labels = ['18-24 anos', '25-34 anos', '35-44 anos', '45-54 anos', '55-64 anos', '65+ anos']
    df['faixa_etaria'] = pd.cut(df['q6'], bins=age_bins, labels=age_labels, right=True)

    # --- Criação de Faixa de Escolaridade ---
    # As faixas são baseadas nas tabelas sociodemográficas do relatório VIGITEL 2023 
    edu_bins = [-1, 8, 11, np.inf]
    edu_labels = ['0-8 anos', '9-11 anos', '12+ anos']
    df['faixa_escolaridade'] = pd.cut(df['q8_anos'], bins=edu_bins, labels=edu_labels, right=True)
    
    # --- Mapeamento de Sexo ---
    # Cria uma coluna mais descritiva para o sexo
    sexo_map = {1: 'Masculino', 2: 'Feminino'}
    df['sexo'] = df['q7'].map(sexo_map)

    # --- Criação de Indicadores Adicionais (Exemplos) ---
    # Obesidade e Excesso de Peso (conforme dicionário) 
    df['imc'] = to_numeric_silent(df['q9']) / ((to_numeric_silent(df['q11']) / 100) ** 2)
    df.loc[(df['imc'] < 10) | (df['imc'] > 100), 'imc'] = np.nan # Limpeza de outliers
    df['excpeso'] = np.where(df['imc'] >= 25, 1, 0)
    df['obesid'] = np.where(df['imc'] >= 30, 1, 0)
    
    # Consumo Abusivo de Álcool (conforme dicionário) 
    # q37 para homens (>=5 doses), q38 para mulheres (>=4 doses)
    cond_homem = (df['sexo'] == 'Masculino') & (df['q37'] == 1)
    cond_mulher = (df['sexo'] == 'Feminino') & (df['q38'] == 1)
    df['abuso_alcool'] = np.where(cond_homem | cond_mulher, 1, 0)

    # Morbidades Autorreferidas (conforme dicionário) 
    df['hipertensao'] = np.where(df['q75'] == 1, 1, 0)
    df['diabetes'] = np.where(df['q77'] == 1, 1, 0)

    # Garante que as colunas de indicadores sejam numéricas para agregação
    indicator_cols = [
        'ativo_lazer_unif', 'atitrans', 'atiocu', 'atidom', 'inativo', 
        'af3dominios', 'af3dominios_insu', 'excpeso', 'obesid', 
        'abuso_alcool', 'hipertensao', 'diabetes'
    ]
    for col in indicator_cols:
        if col in df.columns:
            df[col] = to_numeric_silent(df[col])
        else:
            # Adiciona a coluna com NaNs se não existir para evitar erros posteriores
            df[col] = np.nan

    # Remove linhas onde as variáveis demográficas essenciais são nulas
    df.dropna(subset=['ano', 'cidade_nome', 'sexo', 'faixa_etaria', 'faixa_escolaridade', 'pesorake'], inplace=True)

    return df