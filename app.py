import dash
from dash import Dash, html, dcc, Input, Output
import os

# --- Asset folders for each engine ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAP_ASSETS = os.path.join(BASE_DIR, "RAP", "assets")
LAMBDA_ASSETS = os.path.join(BASE_DIR, "Lambda", "assets")


app = Dash(
    __name__,
    use_pages=True 
)


page_options = [
    {"label": p["name"], "value": p["relative_path"]}
    for p in sorted(dash.page_registry.values(), key=lambda x: x["name"])
]


app.layout = html.Div([
    dcc.Location(id="url"),

    html.Div(className="header", children=[
        html.H1(
            dcc.Dropdown(
                id="page-dropdown",
                options=page_options,
                clearable=False,
                value="/",
                className="dropdown-header"
            )
        )
    ]),

    dash.page_container
])



@app.callback(
    Output("url", "pathname"),
    Output("page-dropdown", "value"),
    Input("page-dropdown", "value"),
    Input("url", "pathname"),
)
def sync_dropdown(drop_value, pathname):
    ctx = dash.callback_context

    if ctx.triggered_id == "url":
        return pathname, pathname

    if ctx.triggered_id == "page-dropdown":
        return drop_value, drop_value

    return pathname, pathname


if __name__ == "__main__":
    app.run(debug=False)
