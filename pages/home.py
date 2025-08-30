import dash
from dash import html

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
            html.Div([
                html.H3("Lambda Calculus Visualizer", className="tool-title"),
                html.Img(
                    src="https://private-user-images.githubusercontent.com/89393367/436251850-520e0a27-794d-48b9-acc1-46f064a1a1ae.gif?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTY1NzI2MzksIm5iZiI6MTc1NjU3MjMzOSwicGF0aCI6Ii84OTM5MzM2Ny80MzYyNTE4NTAtNTIwZTBhMjctNzk0ZC00OGI5LWFjYzEtNDZmMDY0YTFhMWFlLmdpZj9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA4MzAlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwODMwVDE2NDUzOVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWJmMWRlYzI2ZjUzNWRiYzJhNjU4NzgzMDc4ODliNTlmMjViMjA2MmY5OGFhNzc2MWE3NGI4Y2RjMDE3MTc0MWMmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.0NBPrhFc86rmyBdyuAOvLhj3EiU7PQ5QNxHSwch4B24",
                    alt="Lambda Calculus Visualizer demo",
                    className="tool-gif"
                ),
                html.P(
                    "Enter lambda calculus expressions and follow each step of their evaluation. "
                    "Watch how function application and reduction unfold in interactive tree diagrams.",
                    className="tool-desc"
                ),
            ], className="tool-block", id="lambda-tool-block"),
            html.Div([
                html.H3("Relational Algebra Visualizer",
                        className="tool-title"),
                html.Img(
                    src="https://private-user-images.githubusercontent.com/89393367/425778753-9aeb6165-99fc-4c91-be07-0d9ef0d2ad9a.gif?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTY1NzI2NjUsIm5iZiI6MTc1NjU3MjM2NSwicGF0aCI6Ii84OTM5MzM2Ny80MjU3Nzg3NTMtOWFlYjYxNjUtOTlmYy00YzkxLWJlMDctMGQ5ZWYwZDJhZDlhLmdpZj9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA4MzAlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwODMwVDE2NDYwNVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTE5ZjNkMjlkZTQwYzE0ZDg1ZjA0NjM5MWQ5YmRlNDI5NzI4ZWFkMTFkNTExMjE3MjZiZGFhN2YzY2NhYTQzM2MmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.XT2XHYRAt3zL-fKSBzOgyuuJfyYOcWX-tQMusAv622Y",
                    alt="Relational Algebra Visualizer demo",
                    className="tool-gif"
                ),
                html.P(
                    "Write relational algebra queries and see them represented as expression trees. "
                    "Visualize how data is filtered, joined, and transformed in a database context.",
                    className="tool-desc"
                ),
            ], className="tool-block", id="ra-tool-block"),
        ], className="tools-section"),
        html.Hr(),
        html.P("Use the menu at the top to choose a tool and start exploring.",
               className="home-footer")
    ], id="home-container", className="home-container")
])
