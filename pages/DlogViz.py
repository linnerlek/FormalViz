import os
import re
import dash
from dash import Dash, html, dcc, callback, Output, Input, State, no_update
import dash_cytoscape as cyto
from urllib.parse import urlparse, parse_qs
from argparse import ArgumentParser

from DLOG.DLOG import *

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
