# app.py
# Script principal para a aplicação Dash do Dashboard VIGITEL.

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np

# Importações de módulos locais
from data_preparation import prepare_data
from analysis_engine import calculate_weighted_proportions
from theme import FGV_COLORS, UI_COLORS, fgv_template

# --- 1. INICIALIZAÇÃO E CARREGAMENTO DE DADOS ---
# Carrega e prepara os dados uma vez na inicialização do aplicativo
DATA_PATH = 'outputs/vigitel_todos_anos.parquet'
df = prepare_data(DATA_PATH)

# Inicializa a aplicação Dash com tema Bootstrap
app = dash.Dash(__name__, external_stylesheets=, suppress_callback_exceptions=True)

# Adicione esta linha para o deploy
server = app.server

# --- 2. DEFINIÇÃO DO LAYOUT DA APLICAÇÃO ---

# -- Componente: Barra Lateral (Sidebar) --
sidebar = html.Div(
   }),
        html.Hr(),
        html.P("Navegação Temática", className="lead"),
        dbc.Nav(
           ,
            vertical=True,
            pills=True,
        ),
        html.Hr(),
        html.Label("Capital(is):", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='capital-filter',
            options=[{'label': i, 'value': i} for i in sorted(df['cidade_nome'].unique())],
            value=['sao paulo'], # Valor padrão
            multi=True
        ),
        html.Label("Ano:", className="mt-3 fw-bold"),
        dcc.RangeSlider(
            id='ano-slider',
            min=df['ano'].min(),
            max=df['ano'].max(),
            step=1,
            value=[df['ano'].max() - 5, df['ano'].max()], # Padrão: últimos 5 anos
            marks={str(ano): str(ano) for ano in range(df['ano'].min(), df['ano'].max() + 1, 3)}
        ),
        html.Label("Sexo:", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='sexo-filter',
            options= + [{'label': s, 'value': s} for s in sorted(df['sexo'].unique())],
            value='Todos'
        ),
        html.Label("Faixa Etária:", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='idade-filter',
            options= + [{'label': i, 'value': i} for i in df['faixa_etaria'].cat.categories],
            value='Todas'
        ),
        html.Label("Escolaridade:", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='escolaridade-filter',
            options= + [{'label': i, 'value': i} for i in df['faixa_escolaridade'].cat.categories],
            value='Todas'
        ),
    ],
    style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", "padding": "2rem 1rem",
        "backgroundColor": UI_COLORS['background'], "borderRight": f"1px solid {UI_COLORS['light_grey']}", "overflowY": "auto"
    }
)

# -- Componente: Conteúdo Principal --
content = html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem 1rem"})

# -- Layout Geral da Aplicação --
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content
])

# --- 3. DEFINIÇÃO DOS LAYOUTS DAS PÁGINAS ---

# Layout da página de Atividade Física
layout_atividade_fisica = html.Div(), className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='line-chart-ativo-lazer'), width=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-chart-inativo-demografico'), width=12),
    ]),
])

# Layout da página de Nutrição
layout_nutricao = html.Div(), className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='line-chart-obesidade'), width=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-chart-excpeso-demografico'), width=12),
    ]),
])

# Adicione aqui os layouts para "Fatores de Risco" e "Morbidades" se desejar expandir

# --- 4. DEFINIÇÃO DOS CALLBACKS ---

# -- Callback para Navegação de Página --
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/atividade-fisica":
        return layout_atividade_fisica
    if pathname == "/nutricao":
        return layout_nutricao
    # Adicionar outras páginas aqui
    # Página padrão
    return layout_atividade_fisica

# -- Função de filtro reutilizável --
def filter_dataframe(df, capitais, anos, sexo, idade, escolaridade):
    if not capitais or not anos:
        return pd.DataFrame() # Retorna DF vazio se filtros essenciais estiverem vazios

    filtered_df = df[
        (df['cidade_nome'].isin(capitais)) &
        (df['ano'] >= anos) &
        (df['ano'] <= anos[1])
    ].copy()

    if sexo!= 'Todos':
        filtered_df = filtered_df[filtered_df['sexo'] == sexo]
    if idade!= 'Todas':
        filtered_df = filtered_df[filtered_df['faixa_etaria'] == idade]
    if escolaridade!= 'Todas':
        filtered_df = filtered_df[filtered_df['faixa_escolaridade'] == escolaridade]
    
    return filtered_df

# -- Callback para a página de Atividade Física --
@app.callback(
    [Output('line-chart-ativo-lazer', 'figure'),
     Output('bar-chart-inativo-demografico', 'figure')],
    [Input('capital-filter', 'value'),
     Input('ano-slider', 'value'),
     Input('sexo-filter', 'value'),
     Input('idade-filter', 'value'),
     Input('escolaridade-filter', 'value')]
)
def update_physical_activity_graphs(capitais, anos, sexo, idade, escolaridade):
    filtered_df = filter_dataframe(df, capitais, anos, sexo, idade, escolaridade)

    if filtered_df.empty:
        return {}, {}

    # Gráfico 1: Linha do Tempo (Atividade Física no Lazer)
    group_by_line = ['ano'] if len(capitais) == 1 else ['ano', 'cidade_nome']
    line_data = calculate_weighted_proportions(filtered_df, 'ativo_lazer_unif', group_by_line)
    fig_line = px.line(
        line_data, x='ano', y='prevalencia', color='cidade_nome' if 'cidade_nome' in line_data else None,
        title='Evolução da Prevalência de Atividade Física no Lazer',
        labels={'ano': 'Ano', 'prevalencia': 'Prevalência (%)'}, markers=True
    )
    fig_line.update_traces(hovertemplate='Ano: %{x}<br>Prevalência: %{y:.2%}')
    fig_line.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)

    # Gráfico 2: Barras Demográficas (Inatividade)
    last_year_df = filtered_df[filtered_df['ano'] == anos[1]]
    bar_data = calculate_weighted_proportions(last_year_df, 'inativo', ['faixa_etaria', 'sexo'])
    fig_bar = px.bar(
        bar_data, x='faixa_etaria', y='prevalencia', color='sexo', barmode='group',
        title=f'Prevalência de Inatividade Física por Faixa Etária e Sexo ({anos[1]})',
        labels={'faixa_etaria': 'Faixa Etária', 'prevalencia': 'Prevalência (%)', 'sexo': 'Sexo'}
    )
    fig_bar.update_traces(hovertemplate='Faixa Etária: %{x}<br>Prevalência: %{y:.2%}')
    fig_bar.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)
    
    return fig_line, fig_bar

# -- Callback para a página de Nutrição --
@app.callback(
    [Output('line-chart-obesidade', 'figure'),
     Output('bar-chart-excpeso-demografico', 'figure')],
    [Input('capital-filter', 'value'),
     Input('ano-slider', 'value'),
     Input('sexo-filter', 'value'),
     Input('idade-filter', 'value'),
     Input('escolaridade-filter', 'value')]
)
def update_nutrition_graphs(capitais, anos, sexo, idade, escolaridade):
    filtered_df = filter_dataframe(df, capitais, anos, sexo, idade, escolaridade)

    if filtered_df.empty:
        return {}, {}

    # Gráfico 1: Linha do Tempo (Obesidade)
    group_by_line = ['ano'] if len(capitais) == 1 else ['ano', 'cidade_nome']
    line_data = calculate_weighted_proportions(filtered_df, 'obesid', group_by_line)
    fig_line = px.line(
        line_data, x='ano', y='prevalencia', color='cidade_nome' if 'cidade_nome' in line_data else None,
        title='Evolução da Prevalência de Obesidade (IMC ≥ 30 kg/m²)',
        labels={'ano': 'Ano', 'prevalencia': 'Prevalência (%)'}, markers=True
    )
    fig_line.update_traces(hovertemplate='Ano: %{x}<br>Prevalência: %{y:.2%}')
    fig_line.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)

    # Gráfico 2: Barras Demográficas (Excesso de Peso por Escolaridade)
    last_year_df = filtered_df[filtered_df['ano'] == anos[1]]
    bar_data = calculate_weighted_proportions(last_year_df, 'excpeso', ['faixa_escolaridade', 'sexo'])
    fig_bar = px.bar(
        bar_data, x='faixa_escolaridade', y='prevalencia', color='sexo', barmode='group',
        title=f'Prevalência de Excesso de Peso por Escolaridade e Sexo ({anos[1]})',
        labels={'faixa_escolaridade': 'Escolaridade', 'prevalencia': 'Prevalência (%)', 'sexo': 'Sexo'}
    )
    fig_bar.update_traces(hovertemplate='Escolaridade: %{x}<br>Prevalência: %{y:.2%}')
    fig_bar.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)
    
    return fig_line, fig_bar

# --- 5. EXECUÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':
    app.run_server(debug=True)