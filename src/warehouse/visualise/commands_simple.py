from dash import Dash, html

app = Dash(__name__)
app.title = "Warehouse"
app.layout = html.Div("Hi")
app.run()