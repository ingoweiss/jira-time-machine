"""
Dash web application for Jira Time Machine visualization.

This app provides a web interface to explore Jira project history
and view snapshots at different points in time.
"""

import os
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import pandas as pd
from jira import JIRA
from jira_time_machine import JiraTimeMachine
from datetime import datetime

# Initialize Dash app
app = Dash(__name__)
app.title = "Jira Time Machine"

# Expose the Flask server for gunicorn
server = app.server

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("Jira Time Machine", style={'textAlign': 'center', 'color': '#0052CC'}),
        html.P(
            "Explore the state of your Jira project at any time in its history",
            style={'textAlign': 'center', 'color': '#5E6C84'}
        ),
    ], style={'marginBottom': '30px'}),
    
    html.Div([
        html.Div([
            html.Label("Jira Server URL:", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='jira-server',
                type='text',
                placeholder='https://your-instance.atlassian.net',
                value=os.environ.get('JIRA_SERVER', ''),
                style={'width': '100%', 'padding': '10px', 'marginBottom': '15px'}
            ),
        ], style={'marginBottom': '15px'}),
        
        html.Div([
            html.Label("Email:", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='jira-email',
                type='text',
                placeholder='your-email@example.com',
                value=os.environ.get('JIRA_EMAIL', ''),
                style={'width': '100%', 'padding': '10px', 'marginBottom': '15px'}
            ),
        ], style={'marginBottom': '15px'}),
        
        html.Div([
            html.Label("API Token:", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='jira-token',
                type='password',
                placeholder='Your Jira API token',
                value=os.environ.get('JIRA_API_TOKEN', ''),
                style={'width': '100%', 'padding': '10px', 'marginBottom': '15px'}
            ),
        ], style={'marginBottom': '15px'}),
        
        html.Div([
            html.Label("JQL Query:", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='jql-query',
                type='text',
                placeholder='project = TEST',
                value='',
                style={'width': '100%', 'padding': '10px', 'marginBottom': '15px'}
            ),
        ], style={'marginBottom': '15px'}),
        
        html.Div([
            html.Label("Fields to Track (comma-separated):", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='tracked-fields',
                type='text',
                placeholder='Status, Assignee, Priority',
                value='Status, Assignee, Priority',
                style={'width': '100%', 'padding': '10px', 'marginBottom': '15px'}
            ),
        ], style={'marginBottom': '15px'}),
        
        html.Button(
            'Fetch History',
            id='fetch-button',
            n_clicks=0,
            style={
                'width': '100%',
                'padding': '12px',
                'backgroundColor': '#0052CC',
                'color': 'white',
                'border': 'none',
                'borderRadius': '3px',
                'cursor': 'pointer',
                'fontSize': '16px',
                'fontWeight': 'bold'
            }
        ),
    ], style={
        'maxWidth': '600px',
        'margin': '0 auto',
        'padding': '20px',
        'backgroundColor': '#F4F5F7',
        'borderRadius': '3px'
    }),
    
    html.Div(id='status-message', style={'textAlign': 'center', 'marginTop': '20px'}),
    
    html.Div([
        html.Div([
            html.Label("Select Snapshot Date:", style={'fontWeight': 'bold', 'display': 'block'}),
            dcc.DatePickerSingle(
                id='snapshot-date',
                date=datetime.now().date(),
                display_format='YYYY-MM-DD',
                style={'marginTop': '10px'}
            ),
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        html.H3("Issue Snapshot", style={'textAlign': 'center'}),
        html.Div(id='snapshot-table'),
        
        html.H3("Full History", style={'textAlign': 'center', 'marginTop': '30px'}),
        html.Div(id='history-table'),
    ], id='results-container', style={'display': 'none', 'marginTop': '30px'}),
    
    # Store for history data
    dcc.Store(id='history-data'),
], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})


@callback(
    [Output('history-data', 'data'),
     Output('status-message', 'children'),
     Output('results-container', 'style')],
    Input('fetch-button', 'n_clicks'),
    [State('jira-server', 'value'),
     State('jira-email', 'value'),
     State('jira-token', 'value'),
     State('jql-query', 'value'),
     State('tracked-fields', 'value')],
    prevent_initial_call=True
)
def fetch_jira_history(n_clicks, server, email, token, jql_query, tracked_fields):
    """Fetch history from Jira when the button is clicked."""
    if not all([server, email, token, jql_query, tracked_fields]):
        return None, html.Div("Please fill in all fields", style={'color': 'red'}), {'display': 'none'}
    
    try:
        # Parse tracked fields
        fields_list = [f.strip() for f in tracked_fields.split(',')]
        
        # Connect to Jira
        jira = JIRA(server=server, basic_auth=(email, token))
        
        # Initialize JiraTimeMachine
        jtm = JiraTimeMachine(jira)
        
        # Fetch history
        history_df = jtm.history(jql_query, fields_list)
        
        # Convert to JSON for storage
        history_json = history_df.to_json(date_format='iso', orient='split')
        
        return (
            history_json,
            html.Div(f"Successfully fetched {len(history_df)} records", style={'color': 'green'}),
            {'display': 'block', 'marginTop': '30px'}
        )
    except Exception as e:
        return (
            None,
            html.Div(f"Error: {str(e)}", style={'color': 'red'}),
            {'display': 'none'}
        )


@callback(
    Output('snapshot-table', 'children'),
    [Input('history-data', 'data'),
     Input('snapshot-date', 'date')],
    prevent_initial_call=True
)
def update_snapshot(history_json, snapshot_date):
    """Update the snapshot table when date is changed."""
    if not history_json or not snapshot_date:
        return html.Div("No data available")
    
    try:
        # Load history data
        history_df = pd.read_json(history_json, orient='split')
        
        # Create snapshot
        jtm = JiraTimeMachine(None)  # We don't need Jira connection for snapshot
        snapshot_df = jtm.snapshot(history_df, pd.Timestamp(snapshot_date))
        
        if snapshot_df.empty:
            return html.Div("No issues found for this date")
        
        # Create table
        return dash_table.DataTable(
            data=snapshot_df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in snapshot_df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '14px'
            },
            style_header={
                'backgroundColor': '#0052CC',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F4F5F7'
                }
            ],
            page_size=20
        )
    except Exception as e:
        return html.Div(f"Error creating snapshot: {str(e)}", style={'color': 'red'})


@callback(
    Output('history-table', 'children'),
    Input('history-data', 'data'),
    prevent_initial_call=True
)
def update_history_table(history_json):
    """Update the history table when data is loaded."""
    if not history_json:
        return html.Div("No data available")
    
    try:
        # Load history data
        history_df = pd.read_json(history_json, orient='split')
        
        # Create table
        return dash_table.DataTable(
            data=history_df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in history_df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '14px'
            },
            style_header={
                'backgroundColor': '#0052CC',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F4F5F7'
                }
            ],
            page_size=20
        )
    except Exception as e:
        return html.Div(f"Error displaying history: {str(e)}", style={'color': 'red'})


if __name__ == '__main__':
    # Get host and port from environment variables
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run_server(host=host, port=port, debug=debug)
