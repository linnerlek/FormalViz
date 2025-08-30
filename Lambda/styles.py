lambda_cytoscape_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'background-color': '#e6e6e6', 
            'shape': 'rectangle',
            'width': 30,
            'height': 30,
            'font-size': '16px',
            'font-weight': 'normal', 
            'border-width': 1,  
            'border-color': '#888888'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'width': 2,
            'line-color': '#000000',
            'curve-style': 'bezier'
        }
    },
    {
        'selector': '.lambda-node',
        'style': {
            'shape': 'triangle',
            'background-color': '#e6e6e6',
            'text-margin-y': '5px',
        }
    },
    {
        'selector': '.apply-node',
        'style': {
            'shape': 'ellipse',
            'background-color': '#e6e6e6', 
            'width': 30, 
            'height': 30
        }
    },
    {
        'selector': '.apply-yes',
        'style': {
            'background-color': '#00CC00',
        }
    },
    {
        'selector': '.apply-no',
        'style': {
            'background-color': '#CC0000',
        }
    },
    {
        'selector': '.name-node',
        'style': {
            'shape': 'rectangle',
            'background-color': '#e6e6e6', 
        }
    },
    {
        'selector': '.num-node',
        'style': {
            'shape': 'rectangle',
            'background-color': '#e6e6e6',  
        }
    },
    {
        'selector': '.op-node',
        'style': {
            'shape': 'rectangle',
            'background-color': '#e6e6e6',  
        }
    },
]

styles = {
    'page_container': {
        'maxWidth': '1000px', 
        'margin': '0 auto'
    },
    'header': {
        'textAlign': 'center'
    },
    'controls_container': {
        'display': 'flex', 
        'alignItems': 'center', 
        'justifyContent': 'center', 
        'marginBottom': '20px'
    },
    'button': {
        'marginRight': '10px'
    },
    'input': {
        'marginRight': '10px', 
        'width': '400px'
    },
    'graph_container': {
        'display': 'flex', 
        'alignItems': 'center', 
        'justifyContent': 'center', 
        'marginBottom': '20px'
    },
    'cytoscape': {
        'width': '100%', 
        'height': '600px', 
        'border': '1px solid #ddd'
    },
    'footer': {
        'display': 'flex', 
        'alignItems': 'center', 
        'justifyContent': 'center'
    }
}