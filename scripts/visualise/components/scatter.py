from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd


def render(app: Dash, df1 : pd.DataFrame, df2 : pd.DataFrame) -> html.Div:
    

    def update_scatter(nations: list[str]) -> html.Div:
        filtered_data = MEDAL_DATA.query("nation in @nations")

        if filtered_data.shape[0] == 0:
            return html.Div("No data selected.", id=ids.BAR_CHART)

        fig = px.bar(filtered_data, x="medal", y="count", color="nation", text="nation")

        return html.Div(dcc.Graph(figure=fig), id=ids.BAR_CHART)

    return html.Div(id=ids.BAR_CHART)
