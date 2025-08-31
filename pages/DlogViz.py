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
    db_files = [f for f in os.listdir(DB_FOLDER) if f.endswith('.db')]
    return [{'label': f, 'value': f} for f in db_files]


def get_md_file_content(filename):
    markdown_path = os.path.join(ASSETS_PATH)
    with open(f'{markdown_path}/{filename}', 'r', encoding='utf-8') as file:
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
            'background-color': '#0071CE'
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
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#778899',
            'arrow-scale': 1.5
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
                    layout={'name': 'preset'},
                    elements=[],
                    stylesheet=dlog_cytoscape_stylesheet,
                    userZoomingEnabled=True,
                    userPanningEnabled=True,
                    minZoom=0.5,
                    maxZoom=2.0
                ),
                html.P(id='datalog-output', className="string-output")
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
        return arg_value if arg_value else '_'
    elif arg_type == 'num':
        return str(arg_value)
    elif arg_type == 'str':
        return f"'{arg_value}'"
    return str(arg_value)


# Function to extract comparison conditions from rule bodies
def extract_comparison_conditions(rules):
    # Track variables in each predicate and their associated comparisons
    predicate_variables = {}
    comparison_conditions = {}

    for rule in rules:
        _, body = rule  # We don't need the head for this analysis

        # Track which variables are used in which predicates
        var_to_pred = {}

        # First pass: collect all variables for each predicate
        for literal in body:
            _, pred = literal
            if pred[0] == 'regular':
                pred_name = pred[1]
                # Add predicate entry if it doesn't exist
                if pred_name not in predicate_variables:
                    predicate_variables[pred_name] = set()

                # Add variables from this predicate
                for arg in pred[2]:
                    if arg[0] == 'var' and arg[1] and arg[1] != '_':
                        predicate_variables[pred_name].add(arg[1])
                        if arg[1] not in var_to_pred:
                            var_to_pred[arg[1]] = []
                        var_to_pred[arg[1]].append(pred_name)

        # Second pass: associate comparison conditions with related predicates
        for literal in body:
            _, pred = literal
            if pred[0] == 'comparison':
                left_var = None
                right_var = None

                # Extract variables from comparison
                if pred[1][0] == 'var' and pred[1][1] and pred[1][1] != '_':
                    left_var = pred[1][1]
                if pred[3][0] == 'var' and pred[3][1] and pred[3][1] != '_':
                    right_var = pred[3][1]

                # Format the comparison
                left_arg = format_arg(pred[1])
                op = pred[2]
                right_arg = format_arg(pred[3])
                condition = f"{left_arg} {op} {right_arg}"

                # Find predicates related to these variables
                related_preds = set()
                if left_var and left_var in var_to_pred:
                    related_preds.update(var_to_pred[left_var])
                if right_var and right_var in var_to_pred:
                    related_preds.update(var_to_pred[right_var])

                # Add condition to each related predicate
                for pred_name in related_preds:
                    if pred_name not in comparison_conditions:
                        comparison_conditions[pred_name] = []
                    if condition not in comparison_conditions[pred_name]:
                        comparison_conditions[pred_name].append(condition)

    return comparison_conditions


# Function to build visual graph elements from datalog structures
def build_datalog_graph(pred_dict, dgraph, rules=None):
    elements = []

    # Track node positions
    node_positions = {}
    x_offset = 220  # Increased horizontal spacing
    y_offset = 150  # Vertical spacing between levels

    # Extract comparison conditions if rules are provided
    comparison_conditions = {}
    pred_contents = {}  # Track values used in predicates

    if rules:
        comparison_conditions = extract_comparison_conditions(rules)
        # Extract literal values for display
        for rule in rules:
            head, body = rule
            head_name = head[1]

            # Process head predicate arguments
            if head_name not in pred_contents:
                pred_contents[head_name] = []

            # Process body predicates
            for literal in body:
                _, pred = literal
                if pred[0] == 'regular':
                    pred_name = pred[1]
                    if pred_name not in pred_contents:
                        pred_contents[pred_name] = []

                    # Extract constant values
                    const_values = []
                    for arg in pred[2]:
                        if arg[0] in ('str', 'num'):
                            const_values.append(format_arg(arg))

                    if const_values:
                        content = ", ".join(const_values)
                        if content not in pred_contents[pred_name]:
                            pred_contents[pred_name].append(content)

    # Step 1: Calculate dependency levels for each predicate
    # Create a reverse dependency graph (who depends on me)
    reverse_deps = {}
    for pred in pred_dict:
        reverse_deps[pred] = []

    # Add EDB predicates to reverse_deps
    all_body_preds = set()
    for head in dgraph:
        all_body_preds.update(dgraph[head])
    edb_preds = [p for p in all_body_preds if p not in pred_dict]
    for edb in edb_preds:
        reverse_deps[edb] = []

    # Fill reverse dependencies
    for head in dgraph:
        for body in dgraph[head]:
            if body not in reverse_deps:
                reverse_deps[body] = []
            reverse_deps[body].append(head)

    # Identify the answer predicate
    answer_pred = next((p for p in pred_dict if p.lower() == 'answer'), None)

    # Calculate levels (0 = bottom, higher = closer to answer)
    pred_levels = {}
    level_map = {}  # Map from level to list of predicates

    def assign_level(pred, level):
        # If already assigned to a higher or equal level, keep that
        if pred in pred_levels and pred_levels[pred] >= level:
            return

        pred_levels[pred] = level
        if level not in level_map:
            level_map[level] = []
        level_map[level].append(pred)

        # Process predicates that depend on this one
        for dep in reverse_deps.get(pred, []):
            assign_level(dep, level + 1)

    # Start by setting all EDB predicates to level 0
    for edb in edb_preds:
        assign_level(edb, 0)

    # Process any IDB predicates not yet assigned
    for pred in pred_dict:
        if pred not in pred_levels:
            # Find base level based on its dependencies
            base_level = 0
            for dep in dgraph.get(pred, []):
                if dep in pred_levels:
                    base_level = max(base_level, pred_levels[dep] + 1)
            assign_level(pred, base_level)

    # Step 2: Position nodes by level
    max_level = max(pred_levels.values()) if pred_levels else 0

    # Adjust levels if answer is not at top
    if answer_pred and pred_levels[answer_pred] != max_level:
        # Move answer to top level
        old_level = pred_levels[answer_pred]
        level_map[old_level].remove(answer_pred)
        level_map[max_level + 1] = [answer_pred]
        pred_levels[answer_pred] = max_level + 1
        max_level += 1

    # For each level, position predicates
    for level in range(max_level + 1):
        if level not in level_map:
            continue

        preds = level_map[level]
        level_y = (max_level - level) * y_offset  # Top-down layout

        # Special case for answer at top level
        if level == max_level and answer_pred in preds:
            center_x = (len(preds) - 1) * x_offset / 2
            node_positions[answer_pred] = (center_x, level_y)

            # Create the node
            label = answer_pred
            if answer_pred in pred_contents and pred_contents[answer_pred]:
                label += f"\n({', '.join(pred_contents[answer_pred])})"
            if answer_pred in comparison_conditions and comparison_conditions[answer_pred]:
                label += "\n" + "\n".join(comparison_conditions[answer_pred])

            elements.append({
                'data': {
                    'id': f"node_{answer_pred}",
                    'label': label,
                    'type': 'idb',
                    'arity': len(pred_dict[answer_pred][0]),
                    'conditions': comparison_conditions.get(answer_pred, []),
                    'contents': pred_contents.get(answer_pred, [])
                },
                'position': {'x': center_x, 'y': level_y},
                'classes': 'answer-node'
            })

            # Remove from the list so it's not processed again
            preds = [p for p in preds if p != answer_pred]

        # Position the remaining predicates on this level
        preds_count = len(preds)
        if preds_count > 0:
            # Calculate total width needed
            total_width = (preds_count - 1) * x_offset

            # Start position (centered)
            start_x = -total_width / 2

            # Place each predicate
            for i, pred in enumerate(preds):
                pred_x = start_x + i * x_offset
                node_positions[pred] = (pred_x, level_y)

                # Build the label
                label = pred
                if pred in pred_contents and pred_contents[pred]:
                    label += f"\n({', '.join(pred_contents[pred])})"
                if pred in comparison_conditions and comparison_conditions[pred]:
                    label += "\n" + "\n".join(comparison_conditions[pred])

                # Determine node class
                node_class = 'edb-node' if pred in edb_preds else 'idb-node'
                node_type = 'edb' if pred in edb_preds else 'idb'

                # Add the node
                elements.append({
                    'data': {
                        'id': f"node_{pred}",
                        'label': label,
                        'type': node_type,
                        'arity': len(pred_dict[pred][0]) if pred in pred_dict else 0,
                        'conditions': comparison_conditions.get(pred, []),
                        'contents': pred_contents.get(pred, [])
                    },
                    'position': {'x': pred_x, 'y': level_y},
                    'classes': node_class
                })

    # Add edges from head predicates to body predicates (top-down direction)
    for head_pred in dgraph:
        for body_pred in dgraph[head_pred]:
            elements.append({
                'data': {
                    'source': f"node_{head_pred}",
                    'target': f"node_{body_pred}",
                    'id': f"edge_{head_pred}_{body_pred}"
                }
            })

    return elements


# Main processing callback
@callback(
    [Output('datalog-parsed-data', 'data'),
     Output('datalog-graph', 'elements'),
     Output('datalog-output', 'children'),
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
        return no_update, no_update, no_update, False, "", reset_counter

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'datalog-reset':
        return None, [], "", False, "", reset_counter + 1

    # Validate inputs
    if not query:
        return no_update, no_update, no_update, True, "Please enter a Datalog query", reset_counter

    if not db_file:
        return no_update, no_update, no_update, True, "Please select a database", reset_counter

    # Make sure query ends with $
    if not query.strip().endswith('$'):
        return no_update, no_update, no_update, True, "Query must end with $", reset_counter

    # Parse and process the query
    result, message = parse_datalog_query(query, db_file)

    if message != "OK" or result is None:
        return no_update, no_update, no_update, True, message, reset_counter

    # Build the graph visualization with rules included for conditions
    graph_elements = build_datalog_graph(
        result['pred_dict'],
        result['dgraph'],
        result['rules']
    )

    # Count comparison conditions
    condition_count = 0
    for rule in result['rules']:
        for literal in rule[1]:
            if literal[1][0] == 'comparison':
                condition_count += 1

    # Generate output message with additional details
    output_text = (
        f"Parsed {len(result['pred_dict'])} predicates, "
        f"{len(result['dgraph'])} dependencies, "
        f"and {condition_count} comparison conditions"
    )

    # Return the processed data
    return result, graph_elements, output_text, False, "", reset_counter + 1
