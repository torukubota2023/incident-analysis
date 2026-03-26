"""インシデント可視化モジュール（Plotly）"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# 日本語フォント設定
FONT_FAMILY = "Hiragino Sans, Noto Sans JP, Yu Gothic, sans-serif"
CHART_HEIGHT = 400

# カラーパレット
COLORS = px.colors.qualitative.Set2


def _apply_layout(fig: go.Figure, title: str) -> go.Figure:
    """共通レイアウト設定"""
    fig.update_layout(
        title=title,
        font=dict(family=FONT_FAMILY, size=13),
        height=CHART_HEIGHT,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str = None) -> go.Figure:
    """棒グラフ"""
    fig = px.bar(df, x=x, y=y, title=title, color=color, color_discrete_sequence=COLORS,
                 text=y)
    fig.update_traces(textposition="outside")
    return _apply_layout(fig, title)


def horizontal_bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """横棒グラフ（部署別など項目名が長い場合用）"""
    fig = px.bar(df, x=x, y=y, title=title, orientation="h",
                 color_discrete_sequence=COLORS, text=x)
    fig.update_traces(textposition="outside")
    return _apply_layout(fig, title)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, y2: str = None) -> go.Figure:
    """折れ線グラフ（オプションで第2軸）"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x], y=df[y], mode="lines+markers", name=y,
                             line=dict(color="#1f77b4", width=2)))
    if y2 and y2 in df.columns:
        fig.add_trace(go.Scatter(x=df[x], y=df[y2], mode="lines", name=y2,
                                 line=dict(color="#ff7f0e", width=2, dash="dash")))
    return _apply_layout(fig, title)


def heatmap(cross_df: pd.DataFrame, title: str) -> go.Figure:
    """ヒートマップ"""
    fig = go.Figure(data=go.Heatmap(
        z=cross_df.values,
        x=cross_df.columns.tolist(),
        y=cross_df.index.tolist(),
        colorscale="YlOrRd",
        text=cross_df.values,
        texttemplate="%{text}",
        textfont={"size": 14},
        hoverongaps=False,
    ))
    fig.update_layout(
        height=max(CHART_HEIGHT, len(cross_df.index) * 40 + 100),
    )
    return _apply_layout(fig, title)


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    """円グラフ"""
    fig = px.pie(df, names=names, values=values, title=title,
                 color_discrete_sequence=COLORS)
    fig.update_traces(textposition="inside", textinfo="label+percent+value")
    return _apply_layout(fig, title)


def comparison_bar(current_data: dict, previous_data: dict,
                   current_label: str, previous_label: str, title: str) -> go.Figure:
    """前月比/前年同月比の比較棒グラフ"""
    categories = list(current_data.keys())
    current_vals = list(current_data.values())
    previous_vals = list(previous_data.values())

    fig = go.Figure()
    fig.add_trace(go.Bar(name=previous_label, x=categories, y=previous_vals,
                         marker_color="#aec7e8", text=previous_vals, textposition="outside"))
    fig.add_trace(go.Bar(name=current_label, x=categories, y=current_vals,
                         marker_color="#1f77b4", text=current_vals, textposition="outside"))
    fig.update_layout(barmode="group")
    return _apply_layout(fig, title)


def kpi_metric(label: str, value, delta=None, delta_color="normal"):
    """KPIメトリクス表示用のデータ辞書を返す"""
    return {
        "label": label,
        "value": value,
        "delta": delta,
        "delta_color": delta_color,
    }
