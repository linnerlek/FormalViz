import dash
import dash_cytoscape as cyto
from dash import html

# dash.register_page(
#     __name__,
#     path='/drc',
#     name='DRC Visualizer',
#     order=4
# )

elements = [
    # Root node: A
    # AND node for ACTORS(A) and NOT(...)
    {'data': {'id': 'AND1', 'label': 'AND'}, 'classes': 'AND-node'},
    {'data': {'target': 'AND1'}},
    # ACTORS(A)
    {'data': {'id': 'actorsA',
              'label': 'ACTORS(A)'}, 'classes': 'relation-node'},
    {'data': {'source': 'AND1', 'target': 'actorsA'}},
    # NOT node for (exists M)(ACTS(M,A) and not MOVIES(M,'Kurosawa'))
    {'data': {'id': 'NOT1', 'label': 'NOT'}, 'classes': 'NOT-node'},
    {'data': {'source': 'AND1', 'target': 'NOT1'}},
    # EXISTS M
    {'data': {'id': 'existsM', 'label': 'EXISTS M'}},
    {'data': {'source': 'NOT1', 'target': 'existsM'}},
    # AND node for ACTS(M,A) and NOT(MOVIES(M,'Kurosawa'))
    {'data': {'id': 'AND2', 'label': 'AND'}, 'classes': 'AND-node'},
    {'data': {'source': 'existsM', 'target': 'AND2'}},
    # ACTS(M,A)
    {'data': {'id': 'actsMA',
              'label': "ACTS(M, A)"}, 'classes': 'relation-node'},
    {'data': {'source': 'AND2', 'target': 'actsMA'}},
    # NOT node for MOVIES(M,'Kurosawa')
    {'data': {'id': 'NOT2', 'label': 'NOT'}, 'classes': 'NOT-node'},
    {'data': {'source': 'AND2', 'target': 'NOT2'}},
    # MOVIES(M,'Kurosawa')
    {'data': {'id': 'moviesMK',
              'label': "MOVIES(M, 'Kurosawa')"}, 'classes': 'relation-node'},
    {'data': {'source': 'NOT2', 'target': 'moviesMK'}},
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
            'font-size': '30px',
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
