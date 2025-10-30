import dash
from dash import Dash, html, dcc, Input, Output, clientside_callback
import os
from argparse import ArgumentParser

app = Dash(
    __name__,
    use_pages=True
)

page_options = [
    {"label": p["name"], "value": p["relative_path"]}
    for p in sorted(dash.page_registry.values(), key=lambda x: x["order"])
]


app.layout = html.Div([
    dcc.Location(id="url"),

    html.Div(className="header", children=[
        html.H1(
            dcc.Dropdown(
                id="page-dropdown",
                options=page_options,
                clearable=False,
                value=page_options[0]['value'] if page_options else "/",
                className="dropdown-header"
            )
        )
    ]),

    dash.page_container
])


@app.callback(
    Output("page-dropdown", "value"),
    Input("url", "pathname"),
)
def sync_dropdown(pathname):
    return pathname


clientside_callback(
    """
    function(drop_value) {
        if (drop_value && drop_value !== window.location.pathname) {
            window.location.href = drop_value;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('page-dropdown', 'id'),
    Input('page-dropdown', 'value'),
    prevent_initial_call=True
)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog='Multi-Engine Dashboard',
        description='Dashboard supporting RAP and Lambda engines'
    )
    parser.add_argument('--hostname', default='localhost')
    parser.add_argument('--port', default='8050')
    args = parser.parse_args()

    app.run(debug=False, host=args.hostname, port=int(args.port))
