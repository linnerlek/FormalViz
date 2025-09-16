from dash import clientside_callback
from DLOG.DLOG import generate_sql, generate_ra
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
            'font-size': '20px',
            'text-wrap': 'wrap',
            'text-max-width': 180,
            'padding': '20px',
            'text-margin-y': 10,
            'text-justification': 'center',
            'min-height': 60,
            'background-color': '#0071CE',
        }
    },
    {
        'selector': '.and-node',
        'style': {
            'background-color': '#FFFFFF',
            'border-width': 2,
            'border-color': '#0071CE',
            'shape': 'ellipse',
            'width': 25,
            'height': 25,
            'font-size': '14px',
            'color': '#0071CE',
            'font-weight': 'bold',
            'text-outline-width': 0,
            'text-valign': 'center',
            'text-halign': 'center',
            'text-margin-y': 0,
            'z-index': 10
        }
    },
    {
        'selector': '.or-node',
        'style': {
            'background-color': '#FFFFFF',
            'border-width': 2,
            'border-color': '#FF6B6B',
            'shape': 'ellipse',
            'width': 25,
            'height': 25,
            'font-size': '14px',
            'color': '#FF6B6B',
            'font-weight': 'bold',
            'text-outline-width': 0,
            'text-valign': 'center',
            'text-halign': 'center',
            'text-margin-y': 0,
            'z-index': 10
        }
    },
    {
        'selector': '.neg-indicator',
        'style': {
            'background-color': '#E74C3C',
            'border-width': 2,
            'border-color': '#922B21',
            'shape': 'rectangle',
            'width': 30,
            'height': 6,
            'font-size': '12px',
            'color': '#FFFFFF',
            'font-weight': 'bold',
            'text-outline-width': 0,
            'text-valign': 'center',
            'text-halign': 'center',
            'text-margin-y': 0
        }
    },
    {
        'selector': '.answer-node',
        'style': {
            'background-color': '#6FB1FC',
            'border-width': 3,
            'border-color': '#0066CC',
            'shape': 'round-rectangle',
            'text-margin-y': 5,
            'font-size': '20px'
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
            'background-color': '#86B342',
            'border-width': 2,
            'border-color': '#476E23',
            'shape': 'round-rectangle',
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
            'font-weight': 'bold',
        }
    }
]

layout = html.Div([
    html.Div(id='page-content'),
    dcc.Store(id='datalog-parsed-data'),
    dcc.Store(id='datalog-code-click', data=None),
    dcc.Store(id="datalog-reset-tap-data", data=0),
    dcc.Store(id="datalog-current-page", data=0),
    dcc.Store(id="datalog-prev-clicks", data=0),
    dcc.Store(id="datalog-next-clicks", data=0),
    dcc.Store(id="datalog-row-count", data=0),
    dcc.Store(id="datalog-highlighted-path", data=[]),
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
                    className="text-area-input-resizable"
                ),
                html.Div(className="control-section", children=[
                    html.Button("Submit", id="datalog-submit",
                                className="button"),
                    html.Button("Reset", id="datalog-reset",
                                className="button"),
                ]),
                dcc.ConfirmDialog(id='datalog-error', message='Parse Error!'),
            ]),
            html.Div(className="datalog-tree-table-container", children=[
                cyto.Cytoscape(
                    id='datalog-graph',
                    layout={
                        'name': 'dagre',
                        'rankDir': 'TB',
                        'nodeSep': 60,
                        'edgeSep': 30,
                        'rankSep': 100,
                        'roots': '[id = "node_answer"]',
                        'animate': False
                    },
                    elements=[],
                    stylesheet=dlog_cytoscape_stylesheet + [
                        {
                            'selector': 'edge',
                            'style': {
                                'curve-style': 'taxi',
                                'taxi-direction': 'downward',
                                'taxi-turn': 45,
                                'taxi-turn-min-distance': 20,
                                'taxi-turn-max-distance': 80,
                                'width': 3,
                                'line-color': '#778899',
                                'target-arrow-shape': 'triangle',
                                'target-arrow-color': '#778899',
                                'arrow-scale': 1.5,
                                'edge-text-rotation': 'autorotate'
                            }
                        }
                    ],
                    userZoomingEnabled=True,
                    userPanningEnabled=True,
                    autoungrabify=True,
                    minZoom=0.5,
                    maxZoom=2.0
                ),
                html.Div(id="datalog-tree-table-divider", className="divider"),
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


@callback(
    [Output('datalog-results-panel', 'children'),
     Output('datalog-row-count', 'data')],
    [Input('datalog-graph', 'tapNodeData'),
     Input('datalog-current-page', 'data'),
     Input('datalog-reset-tap-data', 'data'),
     Input('datalog-submit', 'n_clicks')],
    [State('datalog-parsed-data', 'data'),
     State('datalog-db-dropdown', 'value'),
     State('datalog-graph', 'elements')],
    prevent_initial_call=True
)
def show_node_data(node_data, current_page, reset_counter, submit_clicks, parsed_data, db_file, graph_elements):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Click a node to see data.", 0

    # Check if this was triggered by a reset/submit action
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id in ['datalog-reset-tap-data', 'datalog-submit']:
        return "Click a node to see data.", 0

    if not node_data or not parsed_data or not db_file:
        return "Click a node to see data.", 0

    node_id = node_data['id']
    pred_name = node_data.get('predicate_name', '')
    if not pred_name:
        full_label = node_data['label'].split('\n')[0]
        if '(' in full_label:
            pred_name = full_label.split('(')[0]
        else:
            pred_name = full_label

    pred_dict = parsed_data['pred_dict']
    node_type = node_data.get('type', '')

    is_negated = False
    if graph_elements:
        for element in graph_elements:
            if ('data' in element and
                element.get('data', {}).get('type') == 'neg_indicator' and
                    element.get('data', {}).get('parent_node_id') == node_id):
                is_negated = True
                break

    if node_type == 'and':
        return html.Div([
            html.P("This is an AND node.", style={"fontWeight": "bold"}),
            html.P("It represents that ALL connected predicates must be satisfied simultaneously for the rule to be true.",
                   style={"fontStyle": "italic"})
        ]), 0

    if node_type == 'or':
        return html.Div([
            html.P("This is an OR node.", style={"fontWeight": "bold"}),
            html.P("It represents that ANY ONE of the connected rule branches can be satisfied to make the predicate true.",
                   style={"fontStyle": "italic"}),
            html.P("Multiple rules with the same head predicate create different ways to derive the same result.",
                   style={"color": "#666"})
        ]), 0

    if node_type == 'neg_indicator':
        parent_pred = node_data.get('parent_pred', 'unknown')
        return html.Div([
            html.P("This is a NEGATION indicator.",
                   style={"fontWeight": "bold"}),
            html.P(f"It indicates that predicate '{parent_pred}' is negated in the rule.",
                   style={"fontStyle": "italic"}),
            html.P("The predicate must NOT be true for the rule to be satisfied.")
        ]), 0

    if node_type == 'comparison' or pred_name.startswith('comp_') or re.match(r'^[^ ]+ [<>=!]', pred_name):
        return html.Div([
            html.P("This is a comparison/condition node.",
                   style={"fontWeight": "bold"}),
            html.P("Comparison nodes represent conditions that filter data from other predicates.",
                   style={"fontStyle": "italic"}),
            html.P(f"Condition: {node_data['label']}", style={
                   "fontFamily": "monospace", "background": "#f5f5f5", "padding": "5px"}),
            html.P("This node doesn't contain data directly - it applies the condition to tuples from connected predicates.",
                   style={"color": "#666"})
        ]), 0

    if is_negated:
        return html.Div([
            html.P("This is a NEGATED predicate.", style={
                   "fontWeight": "bold", "color": "#E74C3C"}),
            html.P("Negated predicates represent the complement of the original relation.",
                   style={"fontStyle": "italic"}),
            html.P("In theory, this would contain all possible tuples that are NOT in the original relation, "
                   "which could be infinite in an open-world assumption.",
                   style={"fontStyle": "italic", "color": "#666"}),
            html.P("Therefore, no data or SQL query is displayed for negated predicates.",
                   style={"fontWeight": "bold", "color": "#E74C3C"})
        ]), 0

    try:
        db_path = os.path.join(DB_FOLDER, db_file)
        db = SQLite3()
        db.open(db_path)

        specific_args = None
        if pred_name not in parsed_data['pred_dict']:
            full_label = node_data['label'].split('\n')[0]
            if '(' in full_label and ')' in full_label:
                args_str = full_label[full_label.index(
                    '(')+1:full_label.rindex(')')]
                if args_str.strip():
                    arg_parts = [arg.strip() for arg in args_str.split(',')]
                    specific_args = []
                    for arg_part in arg_parts:
                        if arg_part == '_':
                            specific_args.append(('var', '_'))
                        elif arg_part.startswith("'") and arg_part.endswith("'"):
                            specific_args.append(('str', arg_part[1:-1]))
                        elif arg_part.isdigit() or (arg_part.startswith('-') and arg_part[1:].isdigit()):
                            specific_args.append(('num', int(arg_part)))
                        else:
                            specific_args.append(('var', arg_part))

        sql = generate_sql(pred_name, pred_dict, db=db,
                           rules=parsed_data['rules'], specific_args=specific_args)

        # Generate RA expression
        ra = generate_ra(pred_name, pred_dict, db=db,
                         rules=parsed_data['rules'], specific_args=specific_args)

        cur = db.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        cur.close()
        db.close()

        if not rows:
            return html.Div([
                html.Div([
                    html.Button("Show SQL Query", id={'type': 'sql-toggle', 'index': node_id},
                                n_clicks=0, className="button",
                                style={"margin": "0 10px 10px 0", "fontSize": "12px"}),
                    html.Button("Show RA Query", id={'type': 'ra-toggle', 'index': node_id},
                                n_clicks=0, className="button",
                                style={"margin": "0 0 10px 0", "fontSize": "12px"}),
                    html.Div(id={'type': 'sql-container', 'index': node_id},
                            style={"display": "none"}, children=[
                        html.H4("Generated SQL Query:", style={
                                "margin": "10px 0 10px 0"}),
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
                    html.Div(id={'type': 'ra-container', 'index': node_id},
                             style={"display": "none"}, children=[
                        html.H4("Generated RA Expression:", style={
                                "margin": "10px 0 10px 0"}),
                        html.Pre(ra, style={
                            "background": "#f0f8ff",
                            "padding": "10px",
                            "border": "1px solid #0066cc",
                            "border-radius": "4px",
                            "font-size": "12px",
                            "white-space": "pre-wrap",
                            "margin": "0 0 15px 0"
                        })
                    ])
                ]),
                html.P("No data found for this node.")
            ]), 0

        rows_per_page = 8
        total_rows = len(rows)
        max_page = (total_rows - 1) // rows_per_page if total_rows > 0 else 0
        current_page = min(current_page, max_page)
        start_index = current_page * rows_per_page
        end_index = start_index + rows_per_page
        visible_rows = rows[start_index:end_index]

        table_header = [html.Th(col) for col in col_names]
        table_body = [html.Tr([html.Td(cell) for cell in row])
                      for row in visible_rows]

        return html.Div([
            html.Div([
                html.Button("Show SQL Query", id={'type': 'sql-toggle', 'index': node_id},
                            n_clicks=0, className="button",
                            style={"margin": "0 10px 10px 0", "fontSize": "12px"}),
                html.Button("Show RA Query", id={'type': 'ra-toggle', 'index': node_id},
                            n_clicks=0, className="button",
                            style={"margin": "0 0 10px 0", "fontSize": "12px"}),
                html.Div(id={'type': 'sql-container', 'index': node_id},
                        style={"display": "none"}, children=[
                    html.H4("Generated SQL Query:", style={
                            "margin": "10px 0 10px 0"}),
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
                html.Div(id={'type': 'ra-container', 'index': node_id},
                         style={"display": "none"}, children=[
                    html.H4("Generated RA Expression:", style={
                            "margin": "10px 0 10px 0"}),
                    html.Pre(ra, style={
                        "background": "#f0f8ff",
                        "padding": "10px",
                        "border": "1px solid #0066cc",
                        "border-radius": "4px",
                        "font-size": "12px",
                        "white-space": "pre-wrap",
                        "margin": "0 0 15px 0"
                    })
                ])
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


clientside_callback(
    """
    function(elements) {
        if (!elements || elements.length === 0) {
            return window.dash_clientside.no_update;
        }
        
        const cy = document.getElementById('datalog-graph')._cyreg.cy;
        if (!cy) {
            // If cytoscape isn't ready, use a minimal timeout
            setTimeout(function() {
                const cy = document.getElementById('datalog-graph')._cyreg.cy;
                if (!cy) return;
                positionNodes();
            }, 50);
            return;
        }
        
        function positionNodes() {
            // Position negation indicators
            elements.forEach(function(element) {
                if (element.classes && element.classes.includes('neg-indicator')) {
                    const parentNodeId = element.data.parent_node_id;
                    const parentNode = cy.$('#' + parentNodeId);
                    const negNode = cy.$('#' + element.data.id);
                    
                    if (parentNode.length > 0 && negNode.length > 0) {
                        const parentPos = parentNode.position();
                        negNode.position({
                            x: parentPos.x,
                            y: parentPos.y - 50
                        });
                    }
                }
            });
            
            // Position AND nodes at branching points
            elements.forEach(function(element) {
                if (element.classes && element.classes.includes('and-node')) {
                    const andNodeId = element.data.id;
                    const parentNodeId = element.data.parent_node_id;
                    const andNode = cy.$('#' + andNodeId);
                    const parentNode = cy.$('#' + parentNodeId);
                    
                    if (parentNode.length > 0 && andNode.length > 0) {
                        // Find all edges that have this AND node associated
                        const associatedEdges = [];
                        elements.forEach(function(edgeElement) {
                            if (edgeElement.data && edgeElement.data.and_node_id === andNodeId) {
                                const edge = cy.$('#' + edgeElement.data.id);
                                if (edge.length > 0) {
                                    associatedEdges.push(edge);
                                }
                            }
                        });
                        
                        if (associatedEdges.length > 0) {
                            const parentPos = parentNode.position();
                            // Position AND node slightly below the parent node
                            andNode.position({
                                x: parentPos.x,
                                y: parentPos.y + 80
                            });
                        }
                    }
                }
            });

            // Position OR nodes at branching points
            elements.forEach(function(element) {
                if (element.classes && element.classes.includes('or-node')) {
                    const orNodeId = element.data.id;
                    const parentNodeId = element.data.parent_node_id;
                    const orNode = cy.$('#' + orNodeId);
                    const parentNode = cy.$('#' + parentNodeId);
                    
                    if (parentNode.length > 0 && orNode.length > 0) {
                        const parentPos = parentNode.position();
                        // Position OR node slightly below the parent node
                        orNode.position({
                            x: parentPos.x,
                            y: parentPos.y + 80
                        });
                    }
                }
            });
        }
        
        // Try to position immediately
        positionNodes();
        
        // Also listen for layout ready event to ensure positioning after layout
        cy.one('layoutready', function() {
            positionNodes();
        });
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('datalog-graph', 'id'),
    [Input('datalog-graph', 'elements')],
    prevent_initial_call=True
)

# show/hide pagination buttons
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

# Center the graph when new elements are loaded
clientside_callback(
    """
    function(elements) {
        if (!elements || elements.length === 0) {
            return window.dash_clientside.no_update;
        }
        
        // Use the globally available centering function
        if (window.centerDatalogGraph) {
            // Add a small delay to ensure layout is complete
            setTimeout(function() {
                window.centerDatalogGraph();
            }, 200);
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('datalog-graph', 'className'),
    [Input('datalog-graph', 'elements')],
    prevent_initial_call=True
)


@callback(
    Output('datalog-schema-info', 'children'),
    [Input('datalog-db-dropdown', 'value')]
)
def display_datalog_schema_info(selected_db):
    if not selected_db:
        return "Select a database to see schema information"

    try:
        db = SQLite3()
        db.open(os.path.join(DB_FOLDER, selected_db))
        tables = db.relations

        schema_info = {}
        for table in tables:
            attrs = db.getAttributes(table)
            domains = db.getDomains(table)
            attrs_info = []
            for i, attr in enumerate(attrs):
                domain = domains[i]
                attrs_info.append({'attribute': attr, 'domain': domain})
            schema_info[table] = attrs_info

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


@callback(
    Output("datalog-query-input", "value"),
    [Input({"type": "datalog-query-block", "index": dash.dependencies.ALL}, "n_clicks")],
    prevent_initial_call=True
)
def use_datalog_example_query(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    if not any(n_clicks for n_clicks in n_clicks_list if n_clicks is not None):
        return no_update

    triggered_id = ctx.triggered[0]["prop_id"]
    match = re.search(r'"index":(\d+)', triggered_id)
    if not match:
        return no_update

    index = int(match.group(1))
    raw_md = get_md_file_content("Datalogqueries.md")
    parts = re.split(r'(```.*?```)', raw_md, flags=re.DOTALL)

    example_count = 0
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            example_count += 1
            if example_count == index:
                return part.strip("`").strip()

    return no_update


def find_path_to_facts(start_node, dgraph, pred_dict, graph_elements):
    """Find all nodes and edges in the path from start_node to EDB facts"""
    visited_nodes = set()
    path_nodes = set()
    path_edges = set()

    def dfs(node_id):
        if node_id in visited_nodes:
            return
        visited_nodes.add(node_id)

        pred_name = None
        if node_id.startswith("node_"):
            parts = node_id[5:].split('_')  # Remove "node_" prefix
            if len(parts) >= 2 and parts[-1].isdigit():
                pred_name = '_'.join(parts[:-1])
            elif parts[0] == 'comp':
                path_nodes.add(node_id)
                return
            else:
                pred_name = '_'.join(parts)
        else:
            pred_name = node_id

        if not pred_name:
            for element in graph_elements:
                if ('data' in element and element['data'].get('id') == node_id and
                        'predicate_name' in element['data']):
                    pred_name = element['data']['predicate_name']
                    break

        if not pred_name:
            return

        path_nodes.add(node_id)

        if pred_name not in pred_dict:
            find_connected_comparisons(node_id)

        for element in graph_elements:
            if 'data' in element and 'source' in element['data']:
                edge_data = element['data']
                if edge_data['source'] == node_id:
                    target_id = edge_data['target']
                    path_edges.add(edge_data['id'])

                    if (target_id.startswith('and_') or target_id.startswith('neg_indicator_') or
                            target_id.startswith('node_comp_')):
                        path_nodes.add(target_id)

                        for next_element in graph_elements:
                            if 'data' in next_element and 'source' in next_element['data']:
                                next_edge = next_element['data']
                                if next_edge['source'] == target_id:
                                    path_edges.add(next_edge['id'])
                                    dfs(next_edge['target'])
                    else:
                        dfs(target_id)

    def find_connected_comparisons(predicate_node_id):
        """Find comparison nodes connected to a specific predicate node"""
        for element in graph_elements:
            if 'data' in element and 'source' in element['data']:
                edge_data = element['data']
                if edge_data['source'] == predicate_node_id and edge_data['target'].startswith('node_comp_'):
                    comp_node_id = edge_data['target']
                    path_nodes.add(comp_node_id)
                    path_edges.add(edge_data['id'])

    dfs(start_node)

    predicates_in_path = [node for node in path_nodes if not node.startswith(
        ('and_', 'neg_indicator_', 'node_comp_'))]
    for pred_node in predicates_in_path:
        find_connected_comparisons(pred_node)

    return list(path_nodes), list(path_edges)


@callback(
    Output("datalog-highlighted-path", "data"),
    [Input('datalog-graph', 'tapNodeData')],
    [State('datalog-parsed-data', 'data'),
     State('datalog-graph', 'elements')],
    prevent_initial_call=True
)
def update_highlighted_path(node_data, parsed_data, graph_elements):
    if not node_data or not parsed_data:
        return []

    node_id = node_data['id']
    pred_dict = parsed_data['pred_dict']
    dgraph = parsed_data['dgraph']

    path_nodes, path_edges = find_path_to_facts(
        node_id, dgraph, pred_dict, graph_elements)

    return path_nodes + path_edges


@callback(
    Output('datalog-graph', 'stylesheet'),
    [Input("datalog-highlighted-path", "data")],
    prevent_initial_call=True
)
def update_graph_highlighting(highlighted_path):
    # Base stylesheet
    base_stylesheet = dlog_cytoscape_stylesheet + [
        {
            'selector': 'edge',
            'style': {
                'curve-style': 'taxi',
                'taxi-direction': 'downward',
                'taxi-turn': 45,
                'taxi-turn-min-distance': 20,
                'taxi-turn-max-distance': 80,
                'width': 3,
                'line-color': '#778899',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#778899',
                'arrow-scale': 1.5,
                'edge-text-rotation': 'autorotate'
            }
        }
    ]

    if not highlighted_path:
        return base_stylesheet

    for element_id in highlighted_path:
        if element_id.startswith('edge_'):
            base_stylesheet.append({
                'selector': f'[id = "{element_id}"]',
                'style': {
                    'width': 5,
                    'line-color': '#FF0019',
                    'target-arrow-color': "#FF0019",
                    'source-arrow-color': '#FF0019'
                }
            })
        else:
            base_stylesheet.append({
                'selector': f'[id = "{element_id}"]',
                'style': {
                    'border-width': 5,
                    'border-color': "#FF0019",
                    'border-style': 'solid',
                }
            })

    return base_stylesheet


def parse_datalog_query(query, db_path):
    try:
        db = SQLite3()
        db.open(os.path.join(DB_FOLDER, db_path))
        parser = DLOGParser()
        rules = parser.parse(query)

        if rules is None:
            return None, "Parse error: Invalid query syntax"

        pred_dict = construct_data_structure(rules)
        check_result = semantic_checks(db, pred_dict)
        if check_result != "OK":
            return None, check_result

        dgraph = construct_dependency_graph(pred_dict)

        all_preds = all_predicates(dgraph)
        pred_list = construct_ordered_predicates(all_preds, dgraph)

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


def format_arg(arg):
    arg_type, arg_value = arg
    if arg_type == 'var':
        return arg_value or '_'
    if arg_type == 'num':
        return str(arg_value)
    if arg_type == 'str':
        return f"'{arg_value}'"
    return str(arg_value)


def extract_comparison_conditions(rules):
    predicate_variables, comparison_conditions = {}, {}
    for _, body in rules:
        var_to_pred = {}
        pred_positions = {}  # Track predicate positions in the body

        # First pass: collect variables from predicates
        for pos, (_, pred) in enumerate(body):
            if pred[0] == 'regular':
                pred_name = pred[1]
                pred_positions[pred_name] = pos
                predicate_variables.setdefault(pred_name, set())
                for arg in pred[2]:
                    if arg[0] == 'var' and arg[1] and arg[1] != '_':
                        predicate_variables[pred_name].add(arg[1])
                        var_to_pred.setdefault(
                            arg[1], []).append((pred_name, pos))

        # Second pass: process comparisons and link to predicates
        for pos, (_, pred) in enumerate(body):
            if pred[0] == 'comparison':
                left_var = pred[1][1] if pred[1][0] == 'var' and pred[1][1] and pred[1][1] != '_' else None
                right_var = pred[3][1] if pred[3][0] == 'var' and pred[3][1] and pred[3][1] != '_' else None
                condition = f"{format_arg(pred[1])} {pred[2]} {format_arg(pred[3])}"

                # Find which predicate(s) define the variables in this comparison
                related_preds = set()
                primary_pred = None

                # Collect all predicates that define variables in this comparison
                for var in [left_var, right_var]:
                    if var and var in var_to_pred:
                        for pred_name, pred_pos in var_to_pred[var]:
                            related_preds.add(pred_name)
                            # Primary predicate is the one closest before this comparison
                            if pred_pos < pos and (primary_pred is None or pred_pos > pred_positions.get(primary_pred, -1)):
                                primary_pred = pred_name

                # If we found a primary predicate, associate the comparison with it
                # Otherwise, associate with all related predicates
                target_preds = [primary_pred] if primary_pred else list(
                    related_preds)

                for pred_name in target_preds:
                    comparison_conditions.setdefault(pred_name, [])
                    if condition not in comparison_conditions[pred_name]:
                        comparison_conditions[pred_name].append(condition)

    return comparison_conditions


def build_datalog_graph(pred_dict, dgraph, rules=None):
    """
    Build graph based on dependency structure from backend.
    Each rule creates a dependency path from head to body predicates.
    Multiple rules with same head create OR relationships.
    Multiple predicates in rule body create AND relationships.
    Inter-rule dependencies connect IDB predicates to their defining rules.

    Args:
        pred_dict: Dictionary of predicate definitions from backend
        dgraph: Dependency graph (currently unused but kept for API compatibility)
        rules: List of parsed rules
    """
    elements = []
    comparison_conditions = extract_comparison_conditions(
        rules) if rules else {}

    def format_predicate_args(args):
        """Format arguments for display and comparison"""
        formatted = []
        for arg in args:
            if isinstance(arg, tuple) and len(arg) >= 2:
                if arg[0] == 'var':
                    formatted.append(
                        arg[1] if arg[1] and arg[1] != '_' else '_')
                elif arg[0] == 'num':
                    formatted.append(str(arg[1]))
                elif arg[0] == 'str':
                    formatted.append(f"'{arg[1]}'")
                else:
                    formatted.append('_')
            else:
                formatted.append('_')
        return ', '.join(formatted)

    # Track all nodes and their relationships
    node_counter = 0
    created_nodes = {}
    negated_nodes = set()
    head_nodes = {}  # Maps predicate name to single head node ID

    def get_or_create_node(pred_name, pred_args, rule_index=None, body_index=None, is_head=False):
        """Create unique node for each predicate occurrence"""
        nonlocal node_counter

        # For head nodes, use just the predicate name as key to ensure single node per predicate
        # For body nodes in different rules, create unique instances
        if is_head:
            node_key = f"head_{pred_name}"  # Single head node per predicate
        else:
            node_key = f"body_{pred_name}_{rule_index}_{body_index}"

        if node_key not in created_nodes:
            node_id = f"node_{node_counter}"
            node_counter += 1

            # Determine node type
            node_type = 'idb' if pred_name in pred_dict else 'edb'
            if pred_name.lower() == 'answer':
                node_class = 'answer-node'
            elif node_type == 'idb':
                node_class = 'idb-node'
            else:
                node_class = 'edb-node'

            label = f"{pred_name}({format_predicate_args(pred_args)})"

            elements.append({
                'data': {
                    'id': node_id,
                    'label': label,
                    'type': node_type,
                    'predicate_name': pred_name,
                    'arity': len(pred_args),
                    'conditions': comparison_conditions.get(pred_name, []),
                    'contents': []
                },
                'classes': node_class
            })

            created_nodes[node_key] = {
                'node_id': node_id,
                'pred_name': pred_name,
                'pred_args': pred_args,
                'is_head': is_head
            }

            # Track single head node by predicate name
            if is_head:
                head_nodes[pred_name] = node_id

        return created_nodes[node_key]['node_id']

    def add_negation_indicator(target_node_id, pred_name):
        """Add negation indicator for negated predicates"""
        neg_id = f"neg_indicator_{target_node_id}"
        elements.append({
            'data': {
                'id': neg_id,
                'label': 'NOT',
                'type': 'neg_indicator',
                'parent_pred': pred_name,
                'parent_node_id': target_node_id
            },
            'classes': 'neg-indicator'
        })

    def add_and_node(head_node_id, rule_index):
        """Create AND node for multiple body predicates"""
        and_id = f"and_{rule_index}_{head_node_id}"
        elements.append({
            'data': {
                'id': and_id,
                'label': 'and',
                'type': 'and',
                'parent_node_id': head_node_id
            },
            'classes': 'and-node'
        })
        return and_id

    def add_or_node(head_node_id, pred_name):
        """Create OR node for multiple rules with same head predicate"""
        or_id = f"or_{pred_name}_{head_node_id}"
        elements.append({
            'data': {
                'id': or_id,
                'label': 'or',
                'type': 'or',
                'parent_node_id': head_node_id
            },
            'classes': 'or-node'
        })
        return or_id

    def add_edge(source_id, target_id, and_node_id=None, edge_weight=None):
        """Add edge between nodes with optional ordering weight"""
        edge_id = f"edge_{source_id}_{target_id}"
        edge_data = {
            'id': edge_id,
            'source': source_id,
            'target': target_id
        }
        if and_node_id:
            edge_data['and_node_id'] = and_node_id
        if edge_weight is not None:
            edge_data['weight'] = edge_weight

        elements.append({'data': edge_data})

    def process_rule_body(rule_index, _, body, parent_node_id):
        """Process the body of a rule and connect it to the parent node"""
        # Separate regular predicates and comparisons from body
        regular_body_preds = []
        predicate_nodes = {}  # Map predicate position to node ID for this rule

        # First pass: create all predicate nodes
        for body_index, (sign, pred) in enumerate(body):
            if pred[0] == 'regular':
                pred_name = pred[1]
                pred_args = pred[2]

                # Check if this is an IDB predicate that has its own rules
                if pred_name in pred_dict:
                    # Connect to the head node of this predicate
                    target_head_id = head_nodes.get(pred_name)
                    if target_head_id:
                        regular_body_preds.append(
                            (target_head_id, sign, pred_name))
                        predicate_nodes[body_index] = target_head_id
                else:
                    # Create EDB node
                    body_node_id = get_or_create_node(
                        pred_name, pred_args, rule_index, body_index)
                    regular_body_preds.append((body_node_id, sign, pred_name))
                    predicate_nodes[body_index] = body_node_id

                # Track negated predicates for negation indicators
                if sign == 'neg':
                    if pred_name in pred_dict:
                        target_head_id = head_nodes.get(pred_name)
                        if target_head_id:
                            negated_nodes.add(target_head_id)
                    else:
                        body_node_id = get_or_create_node(
                            pred_name, pred_args, rule_index, body_index)
                        negated_nodes.add(body_node_id)

        # Second pass: process comparisons as standalone EDB nodes
        for body_index, (sign, pred) in enumerate(body):
            if pred[0] == 'comparison':
                left_arg, op, right_arg = pred[1], pred[2], pred[3]
                condition = f"{format_arg(left_arg)} {op} {format_arg(right_arg)}"
                comp_key = condition.replace(" ", "_")
                comp_id = created_comparisons[comp_key]

                # Treat comparison as a regular body predicate
                regular_body_preds.append((comp_id, sign, f"comp_{comp_key}"))

        # Create dependency structure for this rule body
        # Sort predicates so negated ones come last (rightmost in layout)
        # Sort by negation status, then by predicate name
        regular_body_preds.sort(key=lambda x: (x[1] == 'neg', x[2]))

        if len(regular_body_preds) > 1:
            # Multiple body predicates - create AND node
            and_node_id = add_and_node(parent_node_id, rule_index)

            # Connect parent to AND node
            add_edge(parent_node_id, and_node_id)

            # Connect AND node to each body predicate (negated ones will be rightmost)
            for i, (body_node_id, sign, pred_name) in enumerate(regular_body_preds):
                # Give higher weight to negated predicates to push them right
                weight = i + (10 if sign == 'neg' else 0)
                add_edge(and_node_id, body_node_id, edge_weight=weight)

        elif len(regular_body_preds) == 1:
            # Single body predicate - direct edge
            body_node_id, sign, pred_name = regular_body_preds[0]
            add_edge(parent_node_id, body_node_id)

    # Process comparison predicates first
    created_comparisons = {}
    if rules:
        for rule_index, (head, body) in enumerate(rules):
            for body_index, (sign, pred) in enumerate(body):
                if pred[0] == 'comparison':
                    left_arg, op, right_arg = pred[1], pred[2], pred[3]
                    condition = f"{format_arg(left_arg)} {op} {format_arg(right_arg)}"
                    comp_key = condition.replace(" ", "_")

                    if comp_key not in created_comparisons:
                        comp_id = f"comp_{node_counter}"
                        node_counter += 1

                        elements.append({
                            'data': {
                                'id': comp_id,
                                'label': condition,
                                'type': 'edb'
                            },
                            'classes': 'edb-node'
                        })
                        created_comparisons[comp_key] = comp_id

    # First pass: Group rules by head predicate and create head nodes
    rules_by_head = {}
    if rules:
        for rule_index, (head, body) in enumerate(rules):
            head_pred_name = head[1]
            head_args = head[2]

            if head_pred_name not in rules_by_head:
                rules_by_head[head_pred_name] = []
            rules_by_head[head_pred_name].append((rule_index, head, body))

            # Create single head node per predicate
            get_or_create_node(head_pred_name, head_args,
                               rule_index, is_head=True)

    # Second pass: Process each predicate and create OR/AND structure
    if rules:
        for pred_name, pred_rules in rules_by_head.items():
            head_node_id = head_nodes[pred_name]

            if len(pred_rules) > 1:
                # Multiple rules for same predicate - create OR node
                or_node_id = add_or_node(head_node_id, pred_name)

                # Connect head to OR node
                add_edge(head_node_id, or_node_id)

                # Process each rule as a branch of the OR
                for rule_index, head, body in pred_rules:
                    process_rule_body(rule_index, head, body, or_node_id)

            else:
                # Single rule for this predicate - direct connection
                rule_index, head, body = pred_rules[0]
                process_rule_body(rule_index, head, body, head_node_id)

    # Add negation indicators for negated predicates
    for node_id in negated_nodes:
        # Find the predicate name for this node
        pred_name = None
        for node_info in created_nodes.values():
            if node_info['node_id'] == node_id:
                pred_name = node_info['pred_name']
                break
        if pred_name:
            add_negation_indicator(node_id, pred_name)

    return elements


@callback(
    [Output('datalog-parsed-data', 'data'),
     Output('datalog-graph', 'elements'),
     Output('datalog-error', 'displayed'),
     Output('datalog-error', 'message'),
     Output('datalog-reset-tap-data', 'data'),
     Output('datalog-highlighted-path', 'data', allow_duplicate=True),
     Output('datalog-query-input', 'value', allow_duplicate=True),
     Output('datalog-results-panel', 'children', allow_duplicate=True),
     Output('datalog-current-page', 'data', allow_duplicate=True)],
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
        return no_update, no_update, False, "", reset_counter, no_update, no_update, no_update, no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'datalog-reset':
        return None, [], False, "", reset_counter + 1, [], "", "Click a node to see data.", 0

    if not query:
        return no_update, no_update, True, "Please enter a Datalog query", reset_counter, no_update, no_update, no_update, no_update

    if not db_file:
        return no_update, no_update, True, "Please select a database", reset_counter, no_update, no_update, no_update, no_update

    if not query.strip().endswith('$'):
        return no_update, no_update, True, "Query must end with $", reset_counter, no_update, no_update, no_update, no_update

    result, message = parse_datalog_query(query, db_file)

    if message != "OK" or result is None:
        return no_update, no_update, True, message, reset_counter, no_update, no_update, no_update, no_update

    graph_elements = build_datalog_graph(
        result['pred_dict'],
        result['dgraph'],
        result['rules']
    )

    return result, graph_elements, False, "", reset_counter + 1, [], no_update, "Click a node to see data.", 0


# Toggle SQL query visibility
@callback(
    [Output({'type': 'sql-container', 'index': dash.dependencies.ALL}, 'style'),
     Output({'type': 'sql-toggle', 'index': dash.dependencies.ALL}, 'children')],
    [Input({'type': 'sql-toggle', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State({'type': 'sql-container', 'index': dash.dependencies.ALL}, 'style')],
    prevent_initial_call=True
)
def toggle_sql_query(n_clicks_list, current_styles):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update

    # Find which button was clicked
    triggered_prop = ctx.triggered[0]['prop_id']
    if 'sql-toggle' not in triggered_prop:
        return no_update, no_update

    # Parse the triggered component to get the index
    import json
    triggered_id = json.loads(triggered_prop.split('.')[0])
    clicked_index = triggered_id['index']

    new_styles = []
    new_button_texts = []

    for i, (n_clicks, current_style) in enumerate(zip(n_clicks_list, current_styles)):
        if n_clicks is None:
            n_clicks = 0

        # Check if this is the button that was clicked by comparing indices
        # We need to match the pattern since we can't directly compare indices
        if i < len(n_clicks_list):
            if n_clicks > 0 and n_clicks % 2 == 1:  # Odd clicks = show
                new_styles.append({"display": "block"})
                new_button_texts.append("Hide SQL Query")
            else:  # Even clicks (including 0) = hide
                new_styles.append({"display": "none"})
                new_button_texts.append("Show SQL Query")
        else:
            new_styles.append(current_style)
            new_button_texts.append("Show SQL Query")

    return new_styles, new_button_texts


# Toggle RA query visibility
@callback(
    [Output({'type': 'ra-container', 'index': dash.dependencies.ALL}, 'style'),
     Output({'type': 'ra-toggle', 'index': dash.dependencies.ALL}, 'children')],
    [Input({'type': 'ra-toggle', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State({'type': 'ra-container', 'index': dash.dependencies.ALL}, 'style')],
    prevent_initial_call=True
)
def toggle_ra_query(n_clicks_list, current_styles):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update

    # Find which button was clicked
    triggered_prop = ctx.triggered[0]['prop_id']
    if 'ra-toggle' not in triggered_prop:
        return no_update, no_update

    # Parse the triggered component to get the index
    import json
    triggered_id = json.loads(triggered_prop.split('.')[0])
    clicked_index = triggered_id['index']

    new_styles = []
    new_button_texts = []

    for i, (n_clicks, current_style) in enumerate(zip(n_clicks_list, current_styles)):
        if n_clicks is None:
            n_clicks = 0

        # Check if this is the button that was clicked by comparing indices
        # We need to match the pattern since we can't directly compare indices
        if i < len(n_clicks_list):
            if n_clicks > 0 and n_clicks % 2 == 1:  # Odd clicks = show
                new_styles.append({"display": "block"})
                new_button_texts.append("Hide RA Query")
            else:  # Even clicks (including 0) = hide
                new_styles.append({"display": "none"})
                new_button_texts.append("Show RA Query")
        else:
            new_styles.append(current_style)
            new_button_texts.append("Show RA Query")

    return new_styles, new_button_texts


# Clear node selection when submit or reset is clicked
clientside_callback(
    """
    function(reset_counter, submit_clicks) {
        const cy = document.getElementById('datalog-graph')._cyreg?.cy;
        if (cy) {
            // Unselect all nodes
            cy.nodes().unselect();
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('datalog-graph', 'data-reset'),
    [Input('datalog-reset-tap-data', 'data'),
     Input('datalog-submit', 'n_clicks')],
    prevent_initial_call=True
)
