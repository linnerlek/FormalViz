import dash
import dash_cytoscape as cyto
from dash import html

# dash.register_page(
#     __name__,
#     path='/drc',
#     name='DRC Visualizer',
#     order=4
# )

# Temporary static tree for the DRC query
elements = [
    # Root node: D
    # EXISTS Z
    {'data': {'id': 'existsZ', 'label': 'EXISTS Z'}},
    # AND node for MOVIES(Z, D) AND NOT(...)
    {'data': {'id': 'AND1', 'label': 'AND'}, 'classes': 'AND-node'},
    {'data': {'source': 'existsZ', 'target': 'AND1'}},
    # MOVIES(Z, D) (base relation)
    {'data': {'id': 'MOVIESZD',
              'label': 'MOVIES(Z, D)'}, 'classes': 'relation-node'},
    {'data': {'source': 'AND1', 'target': 'MOVIESZD'}},
    # NOT(...)
    {'data': {'id': 'not1', 'label': 'NOT'}, 'classes': 'NOT-node'},
    {'data': {'source': 'AND1', 'target': 'not1'}},
    # EXISTS A,X,Y
    {'data': {'id': 'existsAXY', 'label': 'EXISTS A, X, Y'}},
    {'data': {'source': 'not1', 'target': 'existsAXY'}},
    # AND node for MOVIES(X, D) AND ACTORS(Y, A) AND NOT(...)
    {'data': {'id': 'AND2', 'label': 'AND'}, 'classes': 'AND-node'},
    {'data': {'source': 'existsAXY', 'target': 'AND2'}},
    # MOVIES(X, D) (base relation)
    {'data': {'id': 'MOVIESXD',
              'label': 'MOVIES(X, D)'}, 'classes': 'relation-node'},
    {'data': {'source': 'AND2', 'target': 'MOVIESXD'}},
    # ACTORS(Y, A) (base relation)
    {'data': {'id': 'ACTORSYA',
              'label': 'ACTORS(Y, A)'}, 'classes': 'relation-node'},
    {'data': {'source': 'AND2', 'target': 'ACTORSYA'}},
    # NOT(...)
    {'data': {'id': 'not2', 'label': 'NOT'}, 'classes': 'NOT-node'},
    {'data': {'source': 'AND2', 'target': 'not2'}},
    # EXISTS T
    {'data': {'id': 'existsT', 'label': 'EXISTS T'}},
    {'data': {'source': 'not2', 'target': 'existsT'}},
    # AND node for ACTORS(T, A) AND MOVIES(T, D)
    {'data': {'id': 'AND3', 'label': 'AND'}, 'classes': 'AND-node'},
    {'data': {'source': 'existsT', 'target': 'AND3'}},
    # ACTORS(T, A) (base relation)
    {'data': {'id': 'ACTORSTA',
              'label': 'ACTORS(T, A)'}, 'classes': 'relation-node'},
    {'data': {'source': 'AND3', 'target': 'ACTORSTA'}},
    # MOVIES(T, D) (base relation)
    {'data': {'id': 'MOVIESTD',
              'label': 'MOVIES(T, D)'}, 'classes': 'relation-node'},
    {'data': {'source': 'AND3', 'target': 'MOVIESTD'}},
]

cytoscape_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': 200,
            'height': 'label',
            'font-size': '25px',
            'text-wrap': 'wrap',
            'text-max-width': 180,
            'padding': '20px',
            'text-justification': 'center',
            'min-height': 60,
            'background-color': '#6FB1FC',
            'border-width': 3,
            'border-color': '#0066CC',
            'shape': 'round-rectangle',
            'text-margin-y': 5
        }
    },
    {
        'selector': '.relation-node',
        'style': {
            'background-color': '#86B342',
            'border-width': 3,
            'border-color': '#476E23',
            'shape': 'round-rectangle',
        }
    },
    {
        'selector': '.AND-node',
        'style': {
            'background-color': '#FFFFFF',
            'border-width': 2,
            'border-color': '#0071CE',
            'shape': 'ellipse',
            'width': 40,
            'height': 40,
            'font-size': '18px',
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
        'selector': '.NOT-node',
        'style': {
            'background-color': '#ffffff',
            'border-width': 2,
            'border-color': '#C82333',
            'shape': 'ellipse',
            'width': 40,
            'height': 40,
            'font-size': '18px',
            'color': '#C82333',
            'font-weight': 'bold',
            'text-outline-width': 0,
            'text-valign': 'center',
            'text-halign': 'center',
            'text-margin-y': 0,
            'z-index': 10
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': '#778899',
            'width': 3,
            'curve-style': 'bezier',
        }
    },
    {
        'selector': ':selected',
        'style': {
            'border-width': 3,
            'border-color': "#FF0019",
            'border-style': 'solid',
            'font-weight': 'bold',
        }
    }
]

layout = html.Div([
    cyto.Cytoscape(
        id='drc-cytoscape-tree',
        layout={
            'name': 'dagre',
            'rankDir': 'TB',
            'nodeSep': 60,
            'edgeSep': 30,
            'rankSep': 100,
        },
        elements=elements,
        stylesheet=cytoscape_stylesheet,
        style={
            'width': '100%',
            'height': 'calc(100vh - 80px)',
        },
    ),
])
