# theme.py
# ============================================================
# Tema visual mínimo e funções auxiliares para Plotly
# (neutro, leve e consistente com FGV-like azul)
# ============================================================

import plotly.io as pio

FGV_BLUE = "#003b70"
FGV_LIGHT = "#5da1d3"
FGV_GRAY = "#6c757d"

pio.templates["vigitel_min"] = dict(
    layout=dict(
        font=dict(family="Arial, sans-serif", size=13, color="#222"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        colorway=[FGV_BLUE, FGV_LIGHT, "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"],
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=False, zeroline=False, title_standoff=8),
        yaxis=dict(showgrid=True, gridcolor="#eee", zeroline=False, title_standoff=8),
    )
)

# defina como default
pio.templates.default = "vigitel_min"
