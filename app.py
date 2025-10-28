# app.py
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np

from data_preparation import prepare_data
from analysis_engine import calculate_weighted_proportions
from theme import FGV_COLORS, UI_COLORS, fgv_template

# Caminho do Parquet unificado
DATA_PATH = 'outputs/vigitel_todos_anos.parquet'
df = prepare_data(DATA_PATH)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server  # para o Render

# ---------------- Sidebar ----------------
nav = dbc.Nav(
    [
        dbc.NavLink("Atividade Física", href="/atividade-fisica", active="exact"),
        dbc.NavLink("Nutrição", href="/nutricao", active="exact"),
    ],
    vertical=True, pills=True,
)

sidebar = html.Div(
    [
        html.H4("VIGITEL Dashboard", className="fw-bold"),
        html.Hr(),
        html.P("Navegação", className="lead"),
        nav,
        html.Hr(),
        html.Label("Capital(is):", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='capital-filter',
            options=[{'label': i.title(), 'value': i} for i in sorted(df['cidade_nome'].unique())],
            value=['sao paulo'],
            multi=True
        ),
        html.Label("Ano:", className="mt-3 fw-bold"),
        dcc.RangeSlider(
            id='ano-slider',
            min=int(df['ano'].min()),
            max=int(df['ano'].max()),
            step=1,
            value=[int(df['ano'].max()) - 5, int(df['ano'].max())],
            marks={int(a): str(int(a)) for a in range(int(df['ano'].min()), int(df['ano'].max()) + 1, 3)}
        ),
        html.Label("Sexo:", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='sexo-filter',
            options=[{'label': 'Todos', 'value': 'Todos'}] + [{'label': s, 'value': s} for s in sorted(df['sexo'].dropna().unique())],
            value='Todos'
        ),
        html.Label("Faixa Etária:", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='idade-filter',
            options=[{'label': 'Todas', 'value': 'Todas'}] + [{'label': str(i), 'value': i} for i in df['faixa_etaria'].cat.categories],
            value='Todas'
        ),
        html.Label("Escolaridade:", className="mt-3 fw-bold"),
        dcc.Dropdown(
            id='escolaridade-filter',
            options=[{'label': 'Todas', 'value': 'Todas'}] + [{'label': str(i), 'value': i} for i in df['faixa_escolaridade'].cat.categories],
            value='Todas'
        ),
    ],
    style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", "padding": "2rem 1rem",
        "backgroundColor": UI_COLORS['background'], "borderRight": f"1px solid {UI_COLORS['light_grey']}",
        "overflowY": "auto"
    }
)

content = html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem 1rem"})

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

# ---------------- Layouts ----------------
layout_atividade_fisica = html.Div([
    html.H3("Atividade Física", className="mb-4"),
    dbc.Row([dbc.Col(dcc.Graph(id='line-chart-ativo-lazer'), width=12)]),
    dbc.Row([dbc.Col(dcc.Graph(id='bar-chart-inativo-demografico'), width=12)]),
])

layout_nutricao = html.Div([
    html.H3("Nutrição", className="mb-4"),
    dbc.Row([dbc.Col(dcc.Graph(id='line-chart-obesidade'), width=12)]),
    dbc.Row([dbc.Col(dcc.Graph(id='bar-chart-excpeso-demografico'), width=12)]),
])

# ---------------- Navegação ----------------
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/nutricao":
        return layout_nutricao
    # default
    return layout_atividade_fisica

# ---------------- Util ----------------
def filter_dataframe(df, capitais, anos, sexo, idade, escolaridade):
    if not capitais or not anos:
        return pd.DataFrame()
    a0, a1 = int(anos[0]), int(anos[1])

    mask = (df['cidade_nome'].isin(capitais)) & (df['ano'] >= a0) & (df['ano'] <= a1)
    if sexo != 'Todos':
        mask &= (df['sexo'] == sexo)
    if idade != 'Todas':
        mask &= (df['faixa_etaria'] == idade)
    if escolaridade != 'Todas':
        mask &= (df['faixa_escolaridade'] == escolaridade)

    return df.loc[mask].copy()

# ---------------- Callbacks (Atividade Física) ----------------
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
    f = filter_dataframe(df, capitais, anos, sexo, idade, escolaridade)
    if f.empty:
        return px.line(template=fgv_template), px.bar(template=fgv_template)

    group_by_line = ['ano'] + (['cidade_nome'] if len(capitais) > 1 else [])
    line_data = calculate_weighted_proportions(f, 'ativo_lazer_unif', group_by_line)
    if line_data.empty:
        fig_line = px.line(template=fgv_template)
    else:
        color_arg = 'cidade_nome' if 'cidade_nome' in line_data.columns else None
        fig_line = px.line(
            line_data, x='ano', y='prevalencia', color=color_arg,
            title='Evolução da Prevalência de Atividade Física no Lazer',
            labels={'ano': 'Ano', 'prevalencia': 'Prevalência (%)'}, markers=True
        )
        fig_line.update_traces(hovertemplate='Ano: %{x}<br>Prevalência: %{y:.2%}')
        fig_line.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)

    a1 = int(anos[1])
    last_year_df = f[f['ano'] == a1]
    bar_data = calculate_weighted_proportions(last_year_df, 'inativo', ['faixa_etaria', 'sexo'])
    if bar_data.empty:
        fig_bar = px.bar(template=fgv_template)
    else:
        fig_bar = px.bar(
            bar_data, x='faixa_etaria', y='prevalencia', color='sexo', barmode='group',
            title=f'Inatividade Física por Faixa Etária e Sexo ({a1})',
            labels={'faixa_etaria': 'Faixa Etária', 'prevalencia': 'Prevalência (%)', 'sexo': 'Sexo'}
        )
        fig_bar.update_traces(hovertemplate='Faixa Etária: %{x}<br>Prevalência: %{y:.2%}')
        fig_bar.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)

    return fig_line, fig_bar

# ---------------- Callbacks (Nutrição) ----------------
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
    f = filter_dataframe(df, capitais, anos, sexo, idade, escolaridade)
    if f.empty:
        return px.line(template=fgv_template), px.bar(template=fgv_template)

    group_by_line = ['ano'] + (['cidade_nome'] if len(capitais) > 1 else [])
    line_data = calculate_weighted_proportions(f, 'obesid', group_by_line)
    if line_data.empty:
        fig_line = px.line(template=fgv_template)
    else:
        color_arg = 'cidade_nome' if 'cidade_nome' in line_data.columns else None
        fig_line = px.line(
            line_data, x='ano', y='prevalencia', color=color_arg,
            title='Evolução da Prevalência de Obesidade (IMC ≥ 30 kg/m²)',
            labels={'ano': 'Ano', 'prevalencia': 'Prevalência (%)'}, markers=True
        )
        fig_line.update_traces(hovertemplate='Ano: %{x}<br>Prevalência: %{y:.2%}')
        fig_line.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)

    a1 = int(anos[1])
    last_year_df = f[f['ano'] == a1]
    bar_data = calculate_weighted_proportions(last_year_df, 'excpeso', ['faixa_escolaridade', 'sexo'])
    if bar_data.empty:
        fig_bar = px.bar(template=fgv_template)
    else:
        fig_bar = px.bar(
            bar_data, x='faixa_escolaridade', y='prevalencia', color='sexo', barmode='group',
            title=f'Excesso de Peso por Escolaridade e Sexo ({a1})',
            labels={'faixa_escolaridade': 'Escolaridade', 'prevalencia': 'Prevalência (%)', 'sexo': 'Sexo'}
        )
        fig_bar.update_traces(hovertemplate='Escolaridade: %{x}<br>Prevalência: %{y:.2%}')
        fig_bar.update_layout(template=fgv_template, yaxis_tickformat=".0%", height=500)

    return fig_line, fig_bar

if __name__ == '__main__':
    app.run_server(debug=True)
