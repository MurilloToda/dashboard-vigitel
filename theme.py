# theme.py
import plotly.graph_objects as go

FGV_COLORS = {
    'brown': '#40131B',
    'tangerine': '#F7941E',
    'red': '#ED1C24',
    'beige': '#F2E4B1',
    'grey': '#D0D2D3',
    'blue': '#BAD8EA',
}

UI_COLORS = {
    'background': '#F8F7F7',
    'text': '#0F204B',
    'light_grey': '#E6E6E5',
    'accent_blue': '#003591',
}

PLOTLY_COLOR_SEQUENCE = [
    FGV_COLORS['tangerine'],
    UI_COLORS['accent_blue'],
    FGV_COLORS['red'],
    FGV_COLORS['grey'],
    FGV_COLORS['blue'],
]

fgv_template = go.layout.Template()
fgv_template.layout = go.Layout(
    font=dict(family="Arial, sans-serif", size=12, color=UI_COLORS['text']),
    title_font_size=18,
    title_x=0.5,
    plot_bgcolor=UI_COLORS['background'],
    paper_bgcolor=UI_COLORS['background'],
    colorway=PLOTLY_COLOR_SEQUENCE,
    xaxis=dict(showgrid=False, linecolor=UI_COLORS['light_grey'], zeroline=False),
    yaxis=dict(gridcolor=UI_COLORS['light_grey'], zeroline=False),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    margin=dict(l=60, r=20, t=60, b=60),
)
