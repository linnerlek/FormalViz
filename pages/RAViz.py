import sys
import os
import re
from RAP.RAP import *
from doctest import debug
import dash
from dash import dcc, html, callback, clientside_callback
from dash.dependencies import Input, Output, State, ALL
import dash_cytoscape as cyto

cyto.load_extra_layouts()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

dash.register_page(
    __name__,
    path='/raviz',
    name='Relational Algebra Visualizer',
    order=1
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(BASE_DIR, '..', 'assets')
DB_FOLDER = os.path.join(BASE_DIR, '..', 'databases')


def get_readme_content():
    readme_path = os.path.join(ASSETS_PATH, 'RAinstructions.md')
    with open(readme_path, 'r') as file:
        return file.read()


def get_queries_content():
    queries_path = os.path.join(ASSETS_PATH, 'RAqueries.md')
    with open(queries_path, 'r') as file:
        return file.read()


def get_db_files():
    db_files = [f for f in os.listdir(DB_FOLDER) if f.endswith('.db')]
    return [{'label': f, 'value': f} for f in db_files]


def json_to_cytoscape_elements(json_tree, parent_id=None, elements=None, node_counter=[0], x=0, y=0, x_offset=150, y_offset=100, min_separation=50, level_positions=None):
    if elements is None:
        elements = []

    if json_tree is None:
        return elements

    node_id = json_tree['node_id']
    node_label = json_tree.get('node_type', 'Unknown')

    if json_tree.get('node_type') == "relation":
        node_label = json_tree.get('relation_name', 'Unknown Relation')
    elif json_tree.get('node_type') == "project":
        attributes = ', '.join(json_tree.get('columns', []))
        node_label = f"Project\n{attributes}"
    elif json_tree.get('node_type') == 'select':
        conditions = [
            f"{cond[1]} {cond[2]} {cond[4]}" for cond in json_tree.get('conditions', [])
        ]
        node_label = f"Select\n{' and '.join(conditions)}"
    elif json_tree.get('node_type') == 'rename':
        new_columns = ', '.join(json_tree.get('new_columns', []))
        node_label = f"Rename\n{new_columns}"
    elif json_tree.get('node_type') in ['aggregate1', 'aggregate2', 'aggregate3']:
        agg_project_list = json_tree.get('aggregate_project_list', [])
        agg_groupby_list = json_tree.get('aggregate_groupby_list', [])
        agg_having_condition = json_tree.get('aggregate_having_condition', [])
        renamed_columns = json_tree.get('columns', [])

        agg_info = []
        for i, item in enumerate(agg_project_list):
            if i < len(renamed_columns):
                if item[0] == 'id':
                    agg_info.append(f"{item[1]} AS {renamed_columns[i]}")
                elif item[0] == 'agg':
                    agg_info.append(
                        f"{item[1][0]}({item[1][1]}) AS {renamed_columns[i]}")

        node_label = f"Aggregate[\n{', '.join(agg_info)}]"
        if agg_groupby_list:
            node_label += f"\nGROUP BY {', '.join(agg_groupby_list)}"
        if agg_having_condition:
            having_info = [
                f"{cond[1]} {cond[2]} {cond[4]}" for cond in agg_having_condition
            ]
            node_label += f"\nHAVING {' and '.join(having_info)}"

    # Insert newlines into long labels for better wrapping
    def insert_newlines(label, max_len=22):
        words = label.split(' ')
        lines = []
        current = ''
        for word in words:
            if len(current) + len(word) + 1 > max_len:
                lines.append(current)
                current = word
            else:
                if current:
                    current += ' '
                current += word
        if current:
            lines.append(current)
        return '\n'.join(lines)

    node_label = '\n'.join([insert_newlines(line)
                           for line in node_label.split('\n')])

    elements.append({
        'data': {
            'id': node_id,
            'label': node_label,
            'node_type': json_tree.get('node_type', 'Unknown')
        }
    })

    if parent_id:
        elements.append({
            'data': {'source': parent_id, 'target': node_id}
        })

    node_counter[0] += 1

    if json_tree.get('left_child') and json_tree.get('right_child'):
        json_to_cytoscape_elements(
            json_tree['left_child'], node_id, elements, node_counter
        )
        json_to_cytoscape_elements(
            json_tree['right_child'], node_id, elements, node_counter
        )
    elif json_tree.get('left_child'):
        json_to_cytoscape_elements(
            json_tree['left_child'], node_id, elements, node_counter
        )
    elif json_tree.get('right_child'):
        json_to_cytoscape_elements(
            json_tree['right_child'], node_id, elements, node_counter
        )

    return elements


def create_table_from_node_info(node_info):
    columns = node_info['columns']
    rows = node_info['rows']

    # Do not deduplicate columns; preserve order and duplicates as returned
    table_header = [html.Th(col) for col in columns]
    table_body = [html.Tr([html.Td(cell) for cell in row]) for row in rows]

    return html.Table(
        className='classic-table',
        children=[
            html.Thead(html.Tr(table_header)),
            html.Tbody(table_body)
        ]
    )


# linn was here 042325
cytoscape_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': 200,
            'height': 'label',
            'font-size': '20px',
            'text-wrap': 'wrap',
            'text-max-width': 180,
            'padding': '20px',
            'text-margin-y': 10,
            'text-justification': 'center',
            'min-height': 60,
            'background-color': '#6FB1FC',
            'border-width': 2,
            'border-color': '#0066CC',
            'shape': 'round-rectangle',
            'text-margin-y': 5
        }
    },
    {
        'selector': "node[node_type='relation']",
        'style': {
            'background-color': "#6C9133",
            'border-width': 2,
            'border-color': "#314E15",
            'shape': 'round-rectangle',
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': '#CCCCCC',
            'width': 4,
        }
    },
    {
        'selector': ':selected',
        'style': {
            'border-width': 5,
            'border-color': "#FF0019",
            'border-style': 'solid',
            'font-weight': 'bold',
        }
    }

]
# ------------------ HTML ------------------


legend = html.Div(
    id="legend-container",
    style={
        'display': 'flex',
        'flexDirection': 'row',
        'alignItems': 'center',
        'gap': '10px',
        'margin': '5px 0 5px 0',
        'padding': '8px',
        'border': '0',
        'borderRadius': '8px',
        'width': 'fit-content',
    },
    children=[
        html.Div([
            html.Div(style={'width': '22px', 'height': '22px', 'backgroundColor': '#2ecc40',
                     'display': 'inline-block', 'borderRadius': '50%', 'marginRight': '8px'}),
            html.Span('Relation', style={'verticalAlign': 'middle'})
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Div(style={'width': '22px', 'height': '22px', 'backgroundColor': '#0071CE',
                     'display': 'inline-block', 'borderRadius': '50%', 'marginRight': '8px'}),
            html.Span('Operator', style={'verticalAlign': 'middle'})
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Div(style={'width': '22px', 'height': '22px', 'backgroundColor': '#CC0000',
                     'display': 'inline-block', 'borderRadius': '50%', 'marginRight': '8px'}),
            html.Span('Selected', style={'verticalAlign': 'middle'})
        ], style={'display': 'flex', 'alignItems': 'center'}),
    ]
)

layout = html.Div([
    html.Div(id='page-content'),
    dcc.Store(id='code-click', data=None),
    dcc.Store(id="reset-tap-data", data=0),
    html.Div(id="app-container", children=[
        html.Div(id="left-section", className="left-section", children=[
                html.Div(className="input-container", children=[
                    html.Div(className="header-dropdown-container", children=[
                        html.H3(id="db-name-header"),
                        dcc.Dropdown(id="db-dropdown", options=get_db_files(),
                                     placeholder="Select a database"),
                    ]),
                    dcc.Textarea(id="query-input",
                                 placeholder="Enter relational algebra query"),
                    html.Button("Submit", id="submit-btn"),
                ]),

            dcc.Store(id='tree-store'),
            dcc.Store(id='db-path-store'),
            dcc.Store(id="current-page", data=0),
            dcc.Store(id="prev-clicks", data=0),
            dcc.Store(id="next-clicks", data=0),
            dcc.Store(id="row-count", data=0),


            html.Div(className="tree-table-container", children=[
                cyto.Cytoscape(
                    id='cytoscape-tree',
                    layout={
                        'name': 'dagre',
                        'rankSep': 120,   # vertical separation between ranks
                        'nodeSep': 200,   # horizontal separation between nodes
                        'edgeSep': 50,    # separation between edges
                        'rankDir': 'TB',  # top-to-bottom
                        'padding': 50
                    },
                    elements=[],
                    stylesheet=cytoscape_stylesheet,
                    style={'width': '100%', 'height': '100%'}
                ),
                html.Div(id="tree-table-divider", className="divider"),
                html.Div(
                    className="table-and-pagination",
                    children=[
                        html.Div(id="node-table-placeholder",
                                 children="Click node to see info"),
                        html.Div(
                            [
                                html.Button(
                                    "Previous", id="prev-page-btn", n_clicks=0),
                                html.Button(
                                    "Next", id="next-page-btn", n_clicks=0)
                            ],
                            className="pagination-buttons"
                        ),
                        legend,
                    ],
                ),
            ]),
        ]),
        html.Div(id="divider", className="divider"),

        html.Div(id="right-section", className="right-section", children=[
            html.Div(id="documentation-placeholder", children=[
                    html.Button("Documentation",
                                id="installation-info-link", n_clicks=0, className="modal-trigger"),
                    html.Button("Examples",
                                id="open-query-modal-btn", n_clicks=0, className="modal-trigger"),

            ]),
            html.Details(id="schema-container", open=True, children=[
                html.Summary("Schema Information"),
                html.Div(id="schema-info",
                         children="Schema Info Placeholder")
            ])
        ]),
        html.Div(id="modal", className="modal", style={"display": "none"}, children=[
            html.Div(className="modal-content", children=[
                    html.Div(id="button-container", children=[
                        html.Button("Close", id="close-modal-btn")
                    ]),
                html.Div(id="modal-body", className="markdown-content"),
            ])
        ]),
        html.Div(id="query-modal", className="modal", style={"display": "none"}, children=[
            html.Div(className="modal-content", children=[
                    html.Div(id="query-button-container", children=[
                        html.Button("Close", id="close-query-modal-btn")
                    ]),
                html.Div(id="query-modal-body",
                         className="markdown-content"),
            ]),
        ]),
    ]),
    html.Div(id='error-div')
])


# ------------------ Callbacks ------------------
@callback(
    [Output("modal", "style"),
     Output("modal-body", "children")],
    [Input("installation-info-link", "n_clicks"),
     Input("close-modal-btn", "n_clicks")]
)
def toggle_modal(install_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}, ""

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger == "installation-info-link" and install_clicks:
        readme_content = get_readme_content()
        return {"display": "flex"}, dcc.Markdown(readme_content)

    return {"display": "none"}, ""


@callback(
    [Output("query-modal", "style"),
     Output("query-modal-body", "children")],
    [Input("open-query-modal-btn", "n_clicks"),
     Input("close-query-modal-btn", "n_clicks"),
     Input('db-dropdown', 'value')],
    prevent_initial_call=True
)
def toggle_query_modal(open_clicks, close_clicks, selected_db):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}, ""

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger == "open-query-modal-btn" and open_clicks:
        queries_content = get_queries_content()

        if selected_db:
            normalized_db = selected_db.replace('.db', '').lower()
            db_div_pattern = rf'<div data-db="{re.escape(normalized_db)}">.*?</div>'
            match = re.search(db_div_pattern, queries_content,
                              flags=re.DOTALL | re.IGNORECASE)

            if match:
                relevant_content = match.group(0)
                # print("Matched content:", relevant_content)
            else:
                relevant_content = "No queries available for this database."
        else:
            relevant_content = queries_content

        parts = re.split(r'(```.*?```)', relevant_content, flags=re.DOTALL)
        query_elements = []
        element_index = 1

        for part in parts:
            part = part.strip()
            if part.startswith("```") and part.endswith("```"):
                query_elements.append(
                    html.Pre(
                        part.strip('`'),
                        className='query-block',
                        id={'type': 'query-block', 'index': element_index},
                        style={'cursor': 'pointer'}
                    )
                )
                element_index += 1
            elif part.startswith("<h2") and part.endswith("</h2>"):
                query_elements.append(dcc.Markdown(
                    part, dangerously_allow_html=True))
            elif part:
                query_elements.append(dcc.Markdown(
                    part, dangerously_allow_html=True))

        return {"display": "flex"}, query_elements

    return {"display": "none"}, ""


@callback(
    [Output("db-name-header", "children"),
     Output("query-input", "value")],
    [Input("db-dropdown", "value"),
     Input({"type": "query-block", "index": ALL}, "n_clicks")],
    [State("query-modal-body", "children")],
    prevent_initial_call=True,
)
def update_db_or_insert_query(selected_db, query_block_clicks, modal_children):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update

    trigger = ctx.triggered[0]["prop_id"]

    if trigger == "db-dropdown.value":
        header = f"Selected Database: {selected_db}" if selected_db else "No Database Selected"
        return header, ""

    if "query-block" in trigger:
        triggered_id = eval(trigger.split(".")[0])
        triggered_index = triggered_id["index"]

        click_count = query_block_clicks[triggered_index - 1] or 0

        if click_count > 0:
            for element in modal_children:
                if isinstance(element, dict) and element["type"] == "Pre":
                    if "id" in element["props"] and element["props"]["id"]["type"] == "query-block" and element["props"]["id"]["index"] == triggered_index:
                        query_text = element["props"]["children"]
                        return dash.no_update, query_text

    return dash.no_update, dash.no_update


@callback(
    Output('schema-info', 'children'),
    [Input('db-dropdown', 'value')]
)
def display_schema_info(selected_db):
    if not selected_db:
        return "Select a database from the dropdown to view schema information."

    try:
        db_path = os.path.join(DB_FOLDER, selected_db)
        schema_info = fetch_schema_info(db_path)

        if isinstance(schema_info, str):
            return schema_info

        schema_elements = []
        for rname, details in schema_info.items():
            schema_elements.append(
                html.Details([
                    html.Summary(rname),
                    html.Table(className='classic-table', children=[
                        html.Thead(
                            html.Tr([html.Th("Attribute"), html.Th("Data type")])),
                        html.Tbody([html.Tr([html.Td(detail['attribute']), html.Td(
                            detail['domain'])]) for detail in details])
                    ])
                ])
            )

        return schema_elements

    except Exception as e:
        return f"Error: {str(e)}"


@callback(
    [Output('cytoscape-tree', 'elements', allow_duplicate=True),
     Output('cytoscape-tree', 'selectedNodeData', allow_duplicate=True),
     Output('tree-store', 'data', allow_duplicate=True),
     Output('db-path-store', 'data', allow_duplicate=True),
     Output('error-div', 'children', allow_duplicate=True),
     Output('error-div', 'style', allow_duplicate=True),
     Output('node-table-placeholder', 'children', allow_duplicate=True),
     Output('row-count', 'data', allow_duplicate=True),
     Output('current-page', 'data', allow_duplicate=True),
     Output('reset-tap-data', 'data', allow_duplicate=True)],
    [Input('submit-btn', 'n_clicks'),
     Input('db-dropdown', 'value')],
    [State('query-input', 'value'),
     State('reset-tap-data', 'data')],
    prevent_initial_call=True
)
def update_tree(n_clicks, selected_db, query, reset_counter):
    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('db-dropdown'):
        return [], None, {}, "", "", {'display': 'none'}, "Click node to see info.", 0, 0, reset_counter + 1

    if n_clicks is None:
        return [], None, {}, "", "", {'display': 'none'}, "Click node to see info.", 0, 0, reset_counter + 1

    if not selected_db:
        return [], None, {}, "", "Please select a database.", {'display': 'block'}, "Click node to see info.", 0, 0, reset_counter + 1

    if not query:
        return [], None, {}, "", "Please enter a query.", {'display': 'block'}, "Click node to see info.", 0, 0, reset_counter + 1

    if n_clicks and selected_db and query:
        try:
            db_path = os.path.join(DB_FOLDER, selected_db)
            db = SQLite3()
            db.open(db_path)

            json_tree = generate_tree_from_query(query, db, node_counter=[0])

            if 'error' in json_tree:
                return [], None, {}, "", f"Error in query: {json_tree['error']}.", {'display': 'block'}, "Click node to see info.", 0, 0, reset_counter + 1

            elements = json_to_cytoscape_elements(json_tree)

            db.close()
            return elements, None, json_tree, db_path, "", {'display': 'none'}, "Click node to see info.", 0, 0, reset_counter + 1

        except Exception as e:
            # Add this line to print the full stack trace to the server log
            print(traceback.format_exc())
            return [], None, {}, "", str(e), {'display': 'block'}, "Click node to see info.", 0, 0, reset_counter + 1


@callback(
    Output('cytoscape-tree', 'tapNodeData', allow_duplicate=True),
    [Input('reset-tap-data', 'data')],
    prevent_initial_call=True
)
def reset_tap_node_data(reset_counter):
    return None


@callback(
    [Output('node-table-placeholder', 'children', allow_duplicate=True),
     Output('row-count', 'data')],
    [Input('cytoscape-tree', 'tapNodeData'),
     Input('db-dropdown', 'value'),
     Input('current-page', 'data'),
     Input('reset-tap-data', 'data')],
    [State('tree-store', 'data'), State('db-path-store', 'data')],
    prevent_initial_call=True
)
def display_node_info(node_data, selected_db, current_page, reset_counter, json_tree, db_path):
    ctx = dash.callback_context

    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('db-dropdown'):
        return "Click node to see info.", 0

    trigger = ctx.triggered[0]['prop_id'].split(
        '.')[0] if ctx.triggered else None

    if trigger == 'reset-tap-data':
        return "Click node to see info.", 0

    if node_data:
        try:
            node_id = node_data['id']
            db = SQLite3()
            db.open(db_path)

            node_info = get_node_info_from_db(node_id, json_tree, db)
            db.close()

            if 'error' in node_info:
                return html.Div([html.P(f"Error: {node_info['error']}")]), 0

            rows_per_page = 8
            total_rows = len(node_info['rows'])
            max_page = (total_rows - 1) // rows_per_page

            current_page = min(current_page, max_page)
            start_index = current_page * rows_per_page
            end_index = start_index + rows_per_page
            visible_rows = node_info['rows'][start_index:end_index]

            columns = node_info['columns']
            table_header = [html.Th(col) for col in columns]
            table_body = [html.Tr([html.Td(cell) for cell in row])
                          for row in visible_rows]

            result_table = html.Table(
                className='classic-table',
                children=[
                    html.Thead(html.Tr(table_header)),
                    html.Tbody(table_body)
                ]
            )

            return html.Div([
                html.P(f"Number of tuples: {total_rows}",
                       className="tuple-count"),
                result_table
            ]), total_rows

        except Exception as e:
            return f"Error occurred: {str(e)}", 0

    return "Click node to see info.", 0


@callback(
    [Output("current-page", "data", allow_duplicate=True),
     Output("prev-clicks", "data", allow_duplicate=True),
     Output("next-clicks", "data", allow_duplicate=True)],
    [Input("prev-page-btn", "n_clicks"),
     Input("next-page-btn", "n_clicks"),
     Input('cytoscape-tree', 'tapNodeData'),
     Input('submit-btn', 'n_clicks')],
    [State("current-page", "data"),
     State("prev-clicks", "data"),
     State("next-clicks", "data"),
     State("row-count", "data")],
    prevent_initial_call=True
)
def update_page(prev_clicks, next_clicks, node_data, submit_clicks,
                current_page, last_prev_clicks, last_next_clicks, row_count):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split(
        '.')[0] if ctx.triggered else None

    if trigger in ['cytoscape-tree', 'submit-btn']:
        return 0, 0, 0

    rows_per_page = 8
    max_page = max(0, (row_count - 1) // rows_per_page) if row_count else 0

    if trigger == 'prev-page-btn' and prev_clicks > last_prev_clicks:
        new_page = max(0, current_page - 1)
    elif trigger == 'next-page-btn' and next_clicks > last_next_clicks:
        new_page = min(max_page, current_page + 1)
    else:
        new_page = current_page

    new_page = max(0, min(new_page, max_page))

    return new_page, prev_clicks, next_clicks


clientside_callback(
    """
    function(rowCount) {
        if (rowCount > 8) {
            return [{'display': 'inline-block'}, {'display': 'inline-block'}];
        } else {
            return [{'display': 'none'}, {'display': 'none'}];
        }
    }
    """,
    [Output("prev-page-btn", "style"), Output("next-page-btn", "style")],
    [Input("row-count", "data")]
)
