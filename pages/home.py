import dash
from dash import html

dash.register_page(__name__, path='/', order=0)

layout = html.Div([
    html.H1("Welcome!"),
    html.P(
        "This page offers interactive tools to help make computer science concepts more visual and understandable. "
        "Explore how expressions and queries work, step by step, with clear diagrams and interactive features. "
        "The goal of this site is to provide simple, hands-on ways to see how key ideas in computer science work behind the scenes. "
        "Each tool lets you experiment and visualize important structures and processes. "
    ),
    html.H2("Available Tools"),
    html.Div([
        html.H3("Lambda Calculus Visualizer"),
        html.P(
            "Enter lambda calculus expressions and follow each step of their evaluation. "
            "Watch how function application and reduction unfold in interactive tree diagrams."
        ),
        html.H3("Relational Algebra Visualizer"),
        html.P(
            "Write relational algebra queries and see them represented as expression trees. "
            "Visualize how data is filtered, joined, and transformed in a database context."
        ),
    ])
])
