import dash
from dash import html, dcc

dash.register_page(__name__, path='/', order=0)

layout = html.Div([
    html.Div([
        html.H1("Welcome!", className="home-title"),
        html.P(
            "This page offers interactive tools to help make computer science concepts more visual and understandable. "
            "Explore how expressions and queries work, step by step, with clear diagrams and interactive features. "
            "The goal of this site is to provide simple, hands-on ways to see how key ideas in computer science work behind the scenes. "
            "Each tool lets you experiment and visualize important structures and processes.",
            className="home-intro"
        ),
        html.H2("Available Tools", className="home-section-title"),
        html.Div([
            dcc.Link([
                html.Div([
                    html.H3("Lambda Calculus Visualizer",
                            className="tool-title"),
                    html.Img(
                        src="/assets/LAMBDAimg.png",
                        alt="Lambda Calculus Visualizer demo",
                        className="tool-gif"
                    ),
                    html.P(
                        "Enter lambda calculus expressions and follow each step of their evaluation. "
                        "Watch how function application and reduction unfold in interactive tree diagrams.",
                        className="tool-desc"
                    ),
                ], className="tool-block", id="lambda-tool-block")
            ], href="/lambda", style={"textDecoration": "none", "color": "inherit"}),
            dcc.Link([
                html.Div([
                    html.H3("Relational Algebra Visualizer",
                            className="tool-title"),
                    html.Img(
                        src="/assets/RAimg.png",
                        alt="Relational Algebra Visualizer demo",
                        className="tool-gif"
                    ),
                    html.P(
                        "Write relational algebra queries and see them represented as expression trees. "
                        "Visualize how data is filtered, joined, and transformed in a database context.",
                        className="tool-desc"
                    ),
                ], className="tool-block", id="ra-tool-block")
            ], href="/raviz", style={"textDecoration": "none", "color": "inherit"}),
            dcc.Link([
                html.Div([
                    html.H3("Datalog Visualizer", className="tool-title"),
                    html.Img(
                        src="/assets/DLOGimg.png",
                        alt="Datalog Visualizer demo",
                        className="tool-gif"
                    ),
                    html.P(
                        "Write Datalog queries and visualize their dependency graphs. "
                        "See how rules relate to facts and explore the data that each predicate produces.",
                        className="tool-desc"
                    ),
                ], className="tool-block", id="datalog-tool-block")
            ], href="/datalog", style={"textDecoration": "none", "color": "inherit"}),
        ], className="tools-section"),
    ], id="home-container", className="home-container")
])
