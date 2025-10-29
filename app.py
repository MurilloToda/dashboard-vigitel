# app.py
# ============================================================
# Dash app ULTRA-LEVE lendo o CUBO WIDE agregado
# Pensado para plano gratuito do Render (512 MiB):
#  - sem preload de microdado
#  - usa apenas o cubo wide (pequeno)
#  - downcast + category (feito em data_preparation)
# Start command (Render):
#   gunicorn app:server --workers 1 --threads 2 --timeout 120
# ============================================================

from __future__ import annotations
import os
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output

from data_preparation import load_cubo
from analysis_engine import (
    series_evolucao, barras_categoria, ranking_capitais,
    ultimo_ano_disponivel, primeiras_cidades
)
import theme  # noqa: F401  (força o template)

# ---------------------------------------
# Load único (pequeno) na inicialização
# ---------------------------------------
df_cubo, META = load_cubo()

INDICATORS = META["indicators"]
ANOS = META["anos"]
CIDADES = META["cidades"]
SEXOS = META["sexos"]
FET = META["faixa_etaria"]
FESC = META["faixa_escolaridade"]

# Defaults enxutos para reduzir carga
DEFAULT_IND = next((c for c in INDICATORS if c in ("prev_ativo_lazer_unif", "prev_inativo")), INDICATORS[0])
DEFAULT_YEAR = ANOS[-1] if ANOS else None
DEFAULT_CITIES = primeiras_cidades(df_cubo, n=6)

# ---------------------------------------
# App
# ---------------------------------------
app = Dash(__name__)
server = app.server  # para gunicorn

def pct_axis(fig, axis="y"):
    if axis == "y":
        fig.update_yaxes(tickformat=".0%")
    else:
        fig.update_xaxes(tickformat=".0%")
    return fig

app.layout = html.Div(
    style={"maxWidth": "1100px", "margin": "0 auto", "padding": "16px"},
    children=[
        html.H2("VIGITEL – Amostra do BI (cubo leve)"),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px"},
            children=[
                html.Div([
                    html.Label("Indicador"),
                    dcc.Dropdown(
                        id="indicator",
                        options=[{"label": c.replace("prev_", "").replace("_", " ").title(), "value": c} for c in INDICATORS],
                        value=DEFAULT_IND,
                        clearable=False,
                    ),
                ]),
                html.Div([
                    html.Label("Ano (para barras e ranking)"),
                    dcc.Dropdown(
                        id="ano",
                        options=[{"label": int(a), "value": int(a)} for a in ANOS],
                        value=DEFAULT_YEAR, clearable=False,
                    ),
                ]),
                html.Div([
                    html.Label("Capitais (evolução da linha)"),
                    dcc.Dropdown(
                        id="cidades",
                        options=[{"label": c.title(), "value": c} for c in CIDADES],
                        value=DEFAULT_CITIES, multi=True,
                    ),
                ]),
                html.Div([
                    html.Label("Capital (barras por categoria)"),
                    dcc.Dropdown(
                        id="cidade_bar",
                        options=[{"label": c.title(), "value": c} for c in CIDADES],
                        value=DEFAULT_CITIES[0] if DEFAULT_CITIES else (CIDADES[0] if CIDADES else None),
                        clearable=False,
                    ),
                ]),
            ],
        ),
        html.Div(style={"height": "8px"}),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
            children=[
                dcc.Graph(id="fig_evolucao"),
                dcc.Graph(id="fig_barras_sexo"),
                dcc.Graph(id="fig_ranking_capitais", style={"gridColumn": "1 / span 2"}),
            ],
        ),
        html.Div(style={"marginTop": "12px", "color": "#666"},
                 children="Observação: prevalências já vêm agregadas no cubo (proporções em 0..1)."),
    ],
)

# -----------------------------
# Callbacks
# -----------------------------
@app.callback(
    Output("fig_evolucao", "figure"),
    Input("indicator", "value"),
    Input("cidades", "value"),
)
def update_evolucao(indicador: str, cidades: list[str]):
    if not indicador or not cidades:
        return px.line(title="Selecione indicador e capitais")
    d = series_evolucao(df_cubo, indicador, cidades)
    title = f"Evolução por capital • {indicador.replace('prev_', '').replace('_',' ').title()}"
    fig = px.line(d, x="ano", y=indicador, color="cidade_nome", markers=True, title=title,
                  labels={"ano": "Ano", indicador: "Prevalência", "cidade_nome": "Capital"})
    return pct_axis(fig)

@app.callback(
    Output("fig_barras_sexo", "figure"),
    Input("indicator", "value"),
    Input("ano", "value"),
    Input("cidade_bar", "value"),
)
def update_barras_sexo(indicador: str, ano: int, cidade: str):
    if not (indicador and ano and cidade):
        return px.bar(title="Selecione indicador, ano e capital")
    if "sexo" not in df_cubo.columns:
        return px.bar(title="Dimensão 'sexo' indisponível no cubo")
    d = barras_categoria(df_cubo, indicador, "sexo", ano, cidade)
    title = f"{indicador.replace('prev_', '').replace('_',' ').title()} por sexo • {cidade.title()} ({ano})"
    fig = px.bar(d, x="sexo", y=indicador, title=title,
                 labels={"sexo": "Sexo", indicador: "Prevalência"})
    return pct_axis(fig)

@app.callback(
    Output("fig_ranking_capitais", "figure"),
    Input("indicator", "value"),
    Input("ano", "value"),
)
def update_ranking(indicador: str, ano: int):
    if not (indicador and ano):
        return px.bar(title="Selecione indicador e ano")
    d = ranking_capitais(df_cubo, indicador, ano, top_k=12)
    title = f"Ranking de capitais • {indicador.replace('prev_', '').replace('_',' ').title()} ({ano})"
    fig = px.bar(d, x="cidade_nome", y=indicador, title=title,
                 labels={"cidade_nome": "Capital", indicador: "Prevalência"})
    fig.update_xaxes(tickangle=-35)
    return pct_axis(fig)

# ---------------------------------------
# Execução local
# ---------------------------------------
if __name__ == "__main__":
    # Em local dev usamos 1 worker embutido; no Render use gunicorn.
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
