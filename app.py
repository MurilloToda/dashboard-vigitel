# app.py
# ============================================================
# Dash app ULTRA-LEVE lendo o CUBO WIDE agregado
# Ajustes solicitados:
#   (i)   Evolução: remover legenda (apenas hover mostra a capital)
#   (ii)  Mostrar NOME do indicador e uma definição no rodapé
#   (iii) Remover observação inferior
#   (iv)  Remover "(cubo leve)" do título
# ============================================================

from __future__ import annotations
import os
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State

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

# Títulos e definições amigáveis dos indicadores mais comuns
INDICATOR_TITLES = {
    "prev_ativo_lazer_unif": "Atividade física suficiente no lazer (unificado)",
    "prev_inativo": "Inatividade física",
    "prev_excpeso": "Excesso de peso (IMC ≥ 25)",
    "prev_obesid": "Obesidade (IMC ≥ 30)",
    "prev_af3dominios": "Atividade física ≥150 min/sem em 3 domínios",
    "prev_af3dominios_insu": "Atividade física ≤150 min/sem em 3 domínios",
    "prev_tv_d_3": "TV ≥ 3 horas/dia",
    "prev_doces5": "Consumo de doces ≥5x/sem",
    "prev_refritl5": "Refrigerantes ≥5x/sem",
    "prev_feijao5": "Feijão ≥5x/sem",
    "prev_carneg": "Consumo de carne com gordura",
    "prev_franpl": "Consumo de frango com pele",
    "prev_gordura": "Carnes com excesso de gordura",
    "prev_leiteint": "Leite integral",
    "prev_flvreco": "Consumo recomendado de frutas e hortaliças",
}

INDICATOR_DEFS = {
    "prev_ativo_lazer_unif": "Proporção de adultos com prática suficiente de atividade física no lazer (regra unificada Vigitel).",
    "prev_inativo": "Proporção de adultos inativos fisicamente nos domínios avaliados.",
    "prev_excpeso": "Proporção com IMC entre 25 e 29,9 ou ≥30 (IMC ≥25).",
    "prev_obesid": "Proporção com IMC ≥30.",
    "prev_af3dominios": "Proporção com soma de minutos semanais ≥150 considerando lazer, deslocamento e trabalho.",
    "prev_af3dominios_insu": "Proporção com soma de minutos semanais ≤150 nos três domínios.",
    "prev_tv_d_3": "Proporção que assiste TV por 3 horas ou mais por dia.",
    "prev_doces5": "Proporção que consome doces em 5 dias ou mais por semana.",
    "prev_refritl5": "Proporção que consome refrigerantes em 5 dias ou mais por semana.",
    "prev_feijao5": "Proporção que consome feijão em 5 dias ou mais por semana.",
    "prev_carneg": "Proporção que consome carne com gordura.",
    "prev_franpl": "Proporção que consome frango com pele.",
    "prev_gordura": "Proporção que consome carnes com excesso de gordura (carne com gordura OU frango com pele).",
    "prev_leiteint": "Proporção que consome leite integral.",
    "prev_flvreco": "Proporção que atinge recomendação diária de frutas e hortaliças (regra Vigitel).",
}

def ind_title(ind: str) -> str:
    if ind in INDICATOR_TITLES:
        return INDICATOR_TITLES[ind]
    # fallback amigável
    return ind.replace("prev_", "").replace("_", " ").title()

def ind_def(ind: str) -> str:
    return INDICATOR_DEFS.get(ind, "Prevalência (proporção) do indicador selecionado.")

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
        html.H2("VIGITEL – Amostra do BI"),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px"},
            children=[
                html.Div([
                    html.Label("Indicador"),
                    dcc.Dropdown(
                        id="indicator",
                        options=[{"label": INDICATOR_TITLES.get(c, c.replace("prev_", "").replace("_", " ").title()), "value": c}
                                 for c in INDICATORS],
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

        # Grade de gráficos
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
            children=[
                dcc.Graph(id="fig_evolucao"),
                dcc.Graph(id="fig_barras_sexo"),
                dcc.Graph(id="fig_ranking_capitais", style={"gridColumn": "1 / span 2"}),
            ],
        ),

        # Rodapé com definição do indicador selecionado
        html.Div(
            id="indicador_def",
            style={"marginTop": "10px", "fontSize": "12px", "color": "#555"}
        ),
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
    title = f"Evolução por capital • {ind_title(indicador)}"
    fig = px.line(
        d, x="ano", y=indicador, color="cidade_nome", markers=True, title=title,
        labels={"ano": "Ano", indicador: "Prevalência", "cidade_nome": "Capital"}
    )
    # (i) legenda poluída: ocultar legenda e manter hover com nome da capital
    fig.update_layout(showlegend=False)
    fig.update_traces(hovertemplate="%{x}: %{y:.1%}<br>Capital: %{fullData.name}<extra></extra>")
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
    title = f"{ind_title(indicador)} por sexo • {cidade.title()} ({ano})"
    fig = px.bar(
        d, x="sexo", y=indicador, title=title,
        labels={"sexo": "Sexo", indicador: "Prevalência"}
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(hovertemplate="Sexo: %{x}<br>Prevalência: %{y:.1%}<extra></extra>")
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
    title = f"Ranking de capitais • {ind_title(indicador)} ({ano})"
    fig = px.bar(
        d, x="cidade_nome", y=indicador, title=title,
        labels={"cidade_nome": "Capital", indicador: "Prevalência"},
        height=520
    )

    # Mais espaço e margens automáticas p/ não cortar rótulos e título do eixo
    fig.update_layout(
        showlegend=False,
        margin=dict(l=90, r=24, t=64, b=160),   # << aumenta base e esquerda
        xaxis=dict(automargin=True),
        yaxis=dict(automargin=True),
        uniformtext_minsize=10,
        uniformtext_mode="hide"
    )
    fig.update_xaxes(tickangle=-35, title_standoff=12, tickfont=dict(size=11))
    fig.update_yaxes(title_standoff=14, tickformat=".0%")

    fig.update_traces(
        hovertemplate="Capital: %{x}<br>Prevalência: %{y:.1%}<extra></extra>"
    )
    return fig

@app.callback(
    Output("indicador_def", "children"),
    Input("indicator", "value"),
)
def update_def(instrumento: str):
    if not instrumento:
        return ""
    return html.Div([
        html.Strong("Indicador selecionado: "),
        html.Span(ind_title(instrumento)),
        html.Span(" — "),
        html.Span(ind_def(instrumento)),
    ])

# ---------------------------------------
# Execução local
# ---------------------------------------
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
