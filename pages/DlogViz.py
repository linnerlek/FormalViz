from dash import clientside_callback
import sqlite3
from DLOG.DLOG import generate_sql
import os
import re
import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_cytoscape as cyto

from DLOG.DLOG import (
    construct_data_structure,
    construct_dependency_graph,
    construct_ordered_predicates,
    all_predicates,
    semantic_checks
)
from DLOG.SQLite3 import SQLite3
from DLOG.DLOGParser import DLOGParser

cyto.load_extra_layouts()

dash.register_page(
    __name__,
    path='/datalog',
    name='Datalog Visualizer',
    order=3
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(BASE_DIR, '..', 'assets')
DB_FOLDER = os.path.join(BASE_DIR, '..', 'databases')


def get_db_files():
    return [{'label': f, 'value': f} for f in os.listdir(DB_FOLDER) if f.endswith('.db')]


def get_md_file_content(filename):
    with open(os.path.join(ASSETS_PATH, filename), 'r', encoding='utf-8') as file:
        return file.read()


dlog_cytoscape_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': 200,
            'height': 'label',
            'font-size': '12px',
            'text-wrap': 'wrap',
            'text-max-width': 180,
            'padding': '20px',
            'text-margin-y': 10,
            'text-justification': 'center',
            'min-height': 60,
            'background-color': '#0071CE',
            'text-outline-width': 2,
            'text-outline-color': '#FFFFFF',
            'text-outline-opacity': 1
        }
    },
    {
        'selector': '.answer-node',
        'style': {
            'background-color': '#E74C3C',
            'border-width': 3,
            'border-color': '#922B21',
            'shape': 'round-rectangle',
            'text-margin-y': 5,
            'font-weight': 'bold',
            'font-size': '14px'
        }
    },
    {
        'selector': '.idb-node',
        'style': {
            'background-color': '#6FB1FC',
            'border-width': 2,
            'border-color': '#0066CC',
            'shape': 'round-rectangle',
            'text-margin-y': 5
        }
    },
    {
        'selector': '.edb-node',
        'style': {
            'background-color': '#86B342',
            'border-width': 2,
            'border-color': '#476E23',
            'shape': 'round-rectangle',
        }
    },
    {
        'selector': '.comparison-node',
        'style': {
            'background-color': '#F5A45D',
            'border-width': 2,
            'border-color': '#C66E13',
            'shape': 'diamond',
        }
    },
    {
        'selector': 'edge',
        'style': {
            'width': 3,
            'line-color': '#778899',
            'curve-style': 'straight',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#778899',
            'arrow-scale': 1.5,
            'edge-text-rotation': 'autorotate'
        }
    },
    {
        'selector': ':selected',
        'style': {
            'background-color': '#CC0000',
            'font-weight': 'bold',
        }
    }
]

# --------- Layout ---------
layout = html.Div([
    html.Div(id='page-content'),
    dcc.Store(id='datalog-parsed-data'),
    dcc.Store(id='datalog-code-click', data=None),
    dcc.Store(id="datalog-reset-tap-data", data=0),
    dcc.Store(id="datalog-current-page", data=0),
    dcc.Store(id="datalog-prev-clicks", data=0),
    dcc.Store(id="datalog-next-clicks", data=0),
    dcc.Store(id="datalog-row-count", data=0),
    html.Div(id="app-container", children=[
        html.Div(id="left-section", className="left-section", children=[
            html.Div(className="input-container", children=[
                html.Div(className="header-dropdown-container", children=[
                    html.H3(id="datalog-db-name-header"),
                    dcc.Dropdown(
                        id="datalog-db-dropdown",
                        options=get_db_files(),
                        placeholder="Select a database"
                    ),
                ]),
                dcc.Textarea(
                    id="datalog-query-input",
                    placeholder="Enter Datalog query ending with $...",
                    className="text-area-input"
                ),
                html.Div(className="control-section", children=[
                    html.Button("Submit", id="datalog-submit",
                                className="button"),
                    html.Button("Reset", id="datalog-reset",
                                className="button"),
                ]),
                dcc.ConfirmDialog(id='datalog-error', message='Parse Error!'),
            ]),
            html.Div(className="tree-table-container", children=[
                cyto.Cytoscape(
                    id='datalog-graph',
                    layout={
                        'name': 'breadthfirst',
                        'directed': True,
                        'roots': '[id = "node_answer"]',
                        'spacingFactor': 1.5,
                        'animate': False
                    },
                    elements=[],
                    stylesheet=dlog_cytoscape_stylesheet,
                    userZoomingEnabled=True,
                    userPanningEnabled=True,
                    minZoom=0.5,
                    maxZoom=2.0
                ),
                html.Div(
                    className="table-and-pagination",
                    children=[
                        html.Div(id='datalog-results-panel', className="results-panel",
                                 children="Click a node to see data."),
                        html.Div(
                            [
                                html.Button(
                                    "Previous", id="datalog-prev-page-btn", n_clicks=0),
                                html.Button(
                                    "Next", id="datalog-next-page-btn", n_clicks=0)
                            ],
                            className="pagination-buttons"
                        ),
                    ]
                )
            ]),
        ]),
        html.Div(id="divider", className="divider"),
        html.Div(id="right-section", className="right-section", children=[
            html.Div(id="documentation-placeholder", children=[
                html.Button(
                    "Documentation",
                    id="datalog-open-docs",
                    n_clicks=0,
                    className="modal-trigger"
                ),
                html.Button(
                    "Examples",
                    id="datalog-open-queries",
                    n_clicks=0,
                    className="modal-trigger"
                ),
            ]),
            html.Details(id="datalog-schema-container", open=True, children=[
                html.Summary("Schema Information"),
                html.Div(id="datalog-schema-info",
                         children="Select a database to see schema")
            ])
        ]),
    ]),
    html.Div(id="datalog-modal-docs", className="modal", style={"display": "none"}, children=[
        html.Div(className="modal-content", children=[
            html.Div(id="button-container", children=[
                html.Button("Close", id="datalog-close-docs-btn")
            ]),
            html.Div(id="datalog-docs-body", className="markdown-content")
        ])
    ]),
    html.Div(id="datalog-modal-queries", className="modal", style={"display": "none"}, children=[
        html.Div(className="modal-content", children=[
            html.Div(id="query-button-container", children=[
                html.Button("Close", id="datalog-close-queries-btn")
            ]),
            html.Div(id="datalog-queries-body", className="markdown-content")
        ])
    ]),
    html.Div(id='datalog-error-div')
])
# --- Results Panel Callback ---


# --- Results Panel Callback (now below the graph) ---


@callback(
    [Output('datalog-results-panel', 'children'),
     Output('datalog-row-count', 'data')],
    [Input('datalog-graph', 'tapNodeData'),
     Input('datalog-current-page', 'data')],
    [State('datalog-parsed-data', 'data'),
     State('datalog-db-dropdown', 'value')],
    prevent_initial_call=True
)
def show_node_data(node_data, current_page, parsed_data, db_file):
    if not node_data or not parsed_data or not db_file:
        return "Click a node to see data.", 0

    pred_name = node_data['label'].split('\n')[0]
    pred_dict = parsed_data['pred_dict']

    # If this is a comparison node, just explain it
    if node_data.get('type') == 'comparison' or pred_name.startswith('comp_') or re.match(r'^[^ ]+ [<>=!]', pred_name):
        return html.Div([
            html.P("This is a comparison/condition node. It does not produce data directly, but applies a condition to its connected predicates.",
                   style={"fontStyle": "italic"}),
            html.P(f"Condition: {node_data['label']}")
        ]), 0

    try:
        db_path = os.path.join(DB_FOLDER, db_file)
        db = SQLite3()
        db.open(db_path)

        # Use the unified generate_sql function for all predicates (both EDB and IDB)
        sql = generate_sql(pred_name, pred_dict, db=db,
                           rules=parsed_data['rules'])

        # Execute SQL and get results
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        conn.close()

        if not rows:
            return html.Div([
                html.Div([
                    html.H4("Generated SQL Query:", style={
                            "margin": "0 0 10px 0"}),
                    html.Pre(sql, style={
                        "background": "#f5f5f5",
                        "padding": "10px",
                        "border": "1px solid #ddd",
                        "border-radius": "4px",
                        "font-size": "12px",
                        "white-space": "pre-wrap",
                        "margin": "0 0 15px 0"
                    })
                ]),
                html.P("No data found for this node.")
            ]), 0

        # Pagination logic
        rows_per_page = 8
        total_rows = len(rows)
        max_page = (total_rows - 1) // rows_per_page if total_rows > 0 else 0
        current_page = min(current_page, max_page)
        start_index = current_page * rows_per_page
        end_index = start_index + rows_per_page
        visible_rows = rows[start_index:end_index]

        # Create table
        table_header = [html.Th(col) for col in col_names]
        table_body = [html.Tr([html.Td(cell) for cell in row])
                      for row in visible_rows]

        return html.Div([
            html.Div([
                html.H4("Generated SQL Query:", style={
                        "margin": "0 0 10px 0"}),
                html.Pre(sql, style={
                    "background": "#f5f5f5",
                    "padding": "10px",
                    "border": "1px solid #ddd",
                    "border-radius": "4px",
                    "font-size": "12px",
                    "white-space": "pre-wrap",
                    "margin": "0 0 15px 0"
                })
            ]),
            html.P(f"Number of tuples: {total_rows}", className="tuple-count"),
            html.Table(
                className='classic-table',
                children=[
                    html.Thead(html.Tr(table_header)),
                    html.Tbody(table_body)
                ]
            )
        ]), total_rows

    except Exception as e:
        return html.Div([html.P(f"Error: {str(e)}")]), 0


@callback(
    [Output("datalog-current-page", "data", allow_duplicate=True),
     Output("datalog-prev-clicks", "data", allow_duplicate=True),
     Output("datalog-next-clicks", "data", allow_duplicate=True)],
    [Input("datalog-prev-page-btn", "n_clicks"),
     Input("datalog-next-page-btn", "n_clicks"),
     Input('datalog-graph', 'tapNodeData'),
     Input('datalog-submit', 'n_clicks')],
    [State("datalog-current-page", "data"),
     State("datalog-prev-clicks", "data"),
     State("datalog-next-clicks", "data"),
     State("datalog-row-count", "data")],
    prevent_initial_call=True
)
def update_datalog_page(prev_clicks, next_clicks, node_data, submit_clicks,
                        current_page, last_prev_clicks, last_next_clicks, row_count):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split(
        '.')[0] if ctx.triggered else None

    if trigger in ['datalog-graph', 'datalog-submit']:
        return 0, 0, 0

    rows_per_page = 8
    max_page = max(0, (row_count - 1) // rows_per_page) if row_count else 0

    if trigger == 'datalog-prev-page-btn' and prev_clicks > last_prev_clicks:
        new_page = max(0, current_page - 1)
    elif trigger == 'datalog-next-page-btn' and next_clicks > last_next_clicks:
        new_page = min(max_page, current_page + 1)
    else:
        new_page = current_page

    new_page = max(0, min(new_page, max_page))

    return new_page, prev_clicks, next_clicks


# Add clientside callback to show/hide pagination buttons

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
    [Output("datalog-prev-page-btn", "style"),
     Output("datalog-next-page-btn", "style")],
    [Input("datalog-row-count", "data")]
)


@callback(
    Output('datalog-schema-info', 'children'),
    [Input('datalog-db-dropdown', 'value')]
)
def display_datalog_schema_info(selected_db):
    if not selected_db:
        return "Select a database to see schema information"

    try:
        # Setup database connection
        db = SQLite3()
        db.open(os.path.join(DB_FOLDER, selected_db))

        # Get list of tables
        tables = db.relations

        # Build schema information
        schema_info = {}
        for table in tables:
            attrs = db.getAttributes(table)
            domains = db.getDomains(table)
            attrs_info = []
            for i, attr in enumerate(attrs):
                domain = domains[i]
                attrs_info.append({'attribute': attr, 'domain': domain})
            schema_info[table] = attrs_info

        # Create schema display elements
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
        return f"Error retrieving schema: {str(e)}"


@callback(
    [Output("datalog-modal-docs", "style"),
     Output("datalog-docs-body", "children")],
    [Input("datalog-open-docs", "n_clicks"),
     Input("datalog-close-docs-btn", "n_clicks")],
    prevent_initial_call=True
)
def toggle_datalog_docs_modal(_, __):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}, ""

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == "datalog-open-docs":
        return {"display": "flex"}, dcc.Markdown(get_md_file_content("Dataloginstructions.md"))
    return {"display": "none"}, ""


@callback(
    Output("datalog-db-name-header", "children"),
    [Input("datalog-db-dropdown", "value")],
    prevent_initial_call=True
)
def update_db_name(selected_db):
    if selected_db:
        return f"Database: {selected_db}"
    return ""


@callback(
    [Output("datalog-modal-queries", "style"),
     Output("datalog-queries-body", "children")],
    [Input("datalog-open-queries", "n_clicks"),
     Input("datalog-close-queries-btn", "n_clicks")],
    prevent_initial_call=True
)
def toggle_datalog_queries_modal(_, __):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}, ""

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == "datalog-open-queries":
        raw_md = get_md_file_content("Datalogqueries.md")
        parts = re.split(r'(```.*?```)', raw_md, flags=re.DOTALL)
        content = []
        index = 1

        for part in parts:
            part = part.strip()
            if part.startswith("```") and part.endswith("```"):
                code = part.strip("`").strip()
                content.append(
                    html.Pre(
                        code,
                        className='datalog-query-block',
                        id={'type': 'datalog-query-block', 'index': index},
                        style={'cursor': 'pointer'}
                    )
                )
                index += 1
            else:
                content.append(dcc.Markdown(part, dangerously_allow_html=True))

        return {"display": "flex"}, content

    return {"display": "none"}, ""


# Add a new callback for handling query block clicks
@callback(
    Output("datalog-query-input", "value"),
    [Input({"type": "datalog-query-block", "index": dash.dependencies.ALL}, "n_clicks")],
    prevent_initial_call=True
)
def use_datalog_example_query(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    # Check if any button was actually clicked
    if not any(n_clicks for n_clicks in n_clicks_list if n_clicks is not None):
        return no_update

    triggered_id = ctx.triggered[0]["prop_id"]
    match = re.search(r'"index":(\d+)', triggered_id)
    if not match:
        return no_update

    # Extract the example number and fetch from our examples
    index = int(match.group(1))

    # Get the content from the clicked example
    # This is a simplified approach for demo
    raw_md = get_md_file_content("Datalogqueries.md")
    parts = re.split(r'(```.*?```)', raw_md, flags=re.DOTALL)

    example_count = 0
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            example_count += 1
            if example_count == index:
                return part.strip("`").strip()

    return no_update


# Function to parse and process the Datalog query
def parse_datalog_query(query, db_path):
    try:
        # Setup database connection
        db = SQLite3()
        db.open(os.path.join(DB_FOLDER, db_path))

        # Parse the query using DLOGParser
        parser = DLOGParser()
        rules = parser.parse(query)

        if rules is None:
            return None, "Parse error: Invalid query syntax"

        # Construct data structure
        pred_dict = construct_data_structure(rules)

        # Perform semantic checks
        check_result = semantic_checks(db, pred_dict)
        if check_result != "OK":
            return None, check_result

        # Build dependency graph
        dgraph = construct_dependency_graph(pred_dict)

        # Get all predicates and construct ordered list
        all_preds = all_predicates(dgraph)
        pred_list = construct_ordered_predicates(all_preds, dgraph)

        # Return the processed data
        return {
            'rules': rules,
            'pred_dict': pred_dict,
            'dgraph': dgraph,
            'pred_list': pred_list
        }, "OK"

    except TypeError as e:
        return None, f"Type Error: {str(e)}"
    except ValueError as e:
        return None, f"Value Error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"


# Helper function to format a variable or constant for display
def format_arg(arg):
    arg_type, arg_value = arg
    if arg_type == 'var':
        return arg_value or '_'
    if arg_type == 'num':
        return str(arg_value)
    if arg_type == 'str':
        return f"'{arg_value}'"
    return str(arg_value)


# Function to extract comparison conditions from rule bodies
def extract_comparison_conditions(rules):
    predicate_variables, comparison_conditions = {}, {}
    for _, body in rules:
        var_to_pred = {}
        for _, pred in body:
            if pred[0] == 'regular':
                pred_name = pred[1]
                predicate_variables.setdefault(pred_name, set())
                for arg in pred[2]:
                    if arg[0] == 'var' and arg[1] and arg[1] != '_':
                        predicate_variables[pred_name].add(arg[1])
                        var_to_pred.setdefault(arg[1], []).append(pred_name)
        for _, pred in body:
            if pred[0] == 'comparison':
                left_var = pred[1][1] if pred[1][0] == 'var' and pred[1][1] and pred[1][1] != '_' else None
                right_var = pred[3][1] if pred[3][0] == 'var' and pred[3][1] and pred[3][1] != '_' else None
                condition = f"{format_arg(pred[1])} {pred[2]} {format_arg(pred[3])}"
                related_preds = set()
                if left_var and left_var in var_to_pred:
                    related_preds.update(var_to_pred[left_var])
                if right_var and right_var in var_to_pred:
                    related_preds.update(var_to_pred[right_var])
                for pred_name in related_preds:
                    comparison_conditions.setdefault(pred_name, [])
                    if condition not in comparison_conditions[pred_name]:
                        comparison_conditions[pred_name].append(condition)
    return comparison_conditions


# Function to build visual graph elements from datalog structures
def build_datalog_graph(pred_dict, dgraph, rules=None):
    elements, pred_contents = [], {}
    comparison_conditions = extract_comparison_conditions(
        rules) if rules else {}
    if rules:
        for head, body in rules:
            head_name = head[1]
            pred_contents.setdefault(head_name, [])
            for _, pred in body:
                if pred[0] == 'regular':
                    pred_name = pred[1]
                    pred_contents.setdefault(pred_name, [])
                    const_values = [format_arg(
                        arg) for arg in pred[2] if arg[0] in ('str', 'num')]
                    if const_values:
                        content = ", ".join(const_values)
                        if content not in pred_contents[pred_name]:
                            pred_contents[pred_name].append(content)
    all_body_preds = {p for heads in dgraph.values() for p in heads}
    edb_preds = [p for p in all_body_preds if p not in pred_dict]
    answer_pred = next((p for p in pred_dict if p.lower() == 'answer'), None)

    def add_node(pred, node_type, classes):
        label = pred
        if pred in pred_contents and pred_contents[pred]:
            label += f"\n({', '.join(pred_contents[pred])})"
        elements.append({
            'data': {
                'id': f"node_{pred}",
                'label': label,
                'type': node_type,
                'arity': len(pred_dict[pred][0]) if pred in pred_dict else None,
                'conditions': comparison_conditions.get(pred, []),
                'contents': pred_contents.get(pred, [])
            },
            'classes': classes
        })
    if answer_pred:
        add_node(answer_pred, 'idb', 'answer-node')
    for pred in pred_dict:
        if pred != answer_pred:
            add_node(pred, 'idb', 'idb-node')
    for pred in edb_preds:
        add_node(pred, 'edb', 'edb-node')
    # Use a set to track unique edges (source, target) to avoid duplicates
    edge_set = set()
    for head in dgraph:
        for body in dgraph[head]:
            edge = (f"node_{head}", f"node_{body}")
            if edge not in edge_set:
                edge_set.add(edge)
                elements.append({
                    'data': {
                        'id': f"edge_{head}_{body}",
                        'source': edge[0],
                        'target': edge[1]
                    }
                })
    created_comparisons = {}
    for pred_name, conditions in comparison_conditions.items():
        for condition in conditions:
            comp_key = condition.replace(" ", "_")
            if comp_key not in created_comparisons:
                comp_id = f"comp_{comp_key}"
                elements.append({
                    'data': {
                        'id': f"node_{comp_id}",
                        'label': condition,
                        'type': 'comparison'
                    },
                    'classes': 'comparison-node'
                })
                created_comparisons[comp_key] = comp_id
            else:
                comp_id = created_comparisons[comp_key]
            edge = (f"node_{pred_name}", f"node_{comp_id}")
            if edge not in edge_set:
                edge_set.add(edge)
                elements.append({
                    'data': {
                        'id': f"edge_{pred_name}_{comp_id}",
                        'source': edge[0],
                        'target': edge[1]
                    }
                })
    return elements


# Main processing callback
@callback(
    [Output('datalog-parsed-data', 'data'),
     Output('datalog-graph', 'elements'),
     Output('datalog-error', 'displayed'),
     Output('datalog-error', 'message'),
     Output('datalog-reset-tap-data', 'data')],
    [Input('datalog-submit', 'n_clicks'),
     Input('datalog-reset', 'n_clicks')],
    [State('datalog-query-input', 'value'),
     State('datalog-db-dropdown', 'value'),
     State('datalog-reset-tap-data', 'data')],
    prevent_initial_call=True
)
def process_datalog_query(_, __, query, db_file, reset_counter):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, False, "", reset_counter

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'datalog-reset':
        return None, [], False, "", reset_counter + 1

    # Validate inputs
    if not query:
        return no_update, no_update, True, "Please enter a Datalog query", reset_counter

    if not db_file:
        return no_update, no_update, True, "Please select a database", reset_counter

    # Make sure query ends with $
    if not query.strip().endswith('$'):
        return no_update, no_update, True, "Query must end with $", reset_counter

    # Parse and process the query
    result, message = parse_datalog_query(query, db_file)

    if message != "OK" or result is None:
        return no_update, no_update, True, message, reset_counter

    # Build the graph visualization with rules included for conditions
    graph_elements = build_datalog_graph(
        result['pred_dict'],
        result['dgraph'],
        result['rules']
    )

    # Return the processed data (no output panel)
    return result, graph_elements, False, "", reset_counter + 1
