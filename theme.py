# theme.py
# Este arquivo centraliza todas as definições de estilo e cores da marca FGV.

import plotly.graph_objects as go

# --- Paleta de Cores FGV ---
# Baseado nos manuais de identidade corporativa 
FGV_COLORS = {
    'brown': '#40131B',      # RGB 64/19/27
    'tangerine': '#F7941E',  # RGB 247/148/30
    'red': '#ED1C24',        # RGB 237/28/36
    'beige': '#F2E4B1',      # RGB 242/228/177
    'grey': '#D0D2D3',       # RGB 208/210/211
    'blue': '#BAD8EA',       # RGB 186/216/234
}

# --- Cores da Interface ---
# Cores neutras para fundo, texto e bordas, inspiradas em paletas de design system [10, 11]
UI_COLORS = {
    'background': '#F8F7F7', # Um branco-gelo suave (Sandstone 97%)
    'text': '#0F204B',       # Azul escuro para texto, melhor legibilidade que preto puro
    'light_grey': '#E6E6E5', # Cor de borda suave
    'accent_blue': '#003591',  # Azul para elementos interativos (links, etc.)
}

# --- Paleta de Cores para Gráficos ---
# Sequência de cores para ser usada em gráficos com múltiplas categorias
PLOTLY_COLOR_SEQUENCE =,
    FGV_COLORS['tangerine'],
    UI_COLORS['accent_blue'],
    FGV_COLORS['red'],
    FGV_COLORS['grey'],
    FGV_COLORS['blue']

# --- Template Customizado do Plotly ---
# Este template será aplicado a todos os gráficos para garantir consistência visual
fgv_template = go.layout.Template()

fgv_template.layout = go.Layout(
    font=dict(
        family="Arial, sans-serif",
        size=12,
        color=UI_COLORS['text']
    ),
    title_font_size=18,
    title_x=0.5, # Centralizar título
    plot_bgcolor=UI_COLORS['background'],
    paper_bgcolor=UI_COLORS['background'],
    colorway=PLOTLY_COLOR_SEQUENCE,
    xaxis=dict(
        showgrid=False,
        linecolor=UI_COLORS['light_grey'],
        zeroline=False
    ),
    yaxis=dict(
        gridcolor=UI_COLORS['light_grey'],
        zeroline=False
    ),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1
    ),
    margin=dict(l=60, r=20, t=60, b=60) # Margens para evitar cortes de rótulos
)