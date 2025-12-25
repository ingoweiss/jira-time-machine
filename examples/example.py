#!/usr/bin/env python3
"""
Example script demonstrating how to use Jira Time Machine.

This script shows how to:
1. Connect to a Jira instance
2. Fetch issue history
3. Create a snapshot at a specific point in time

To use this script:
1. Set the following environment variables:
   - JIRA_SERVER: Your Jira server URL (e.g., https://your-instance.atlassian.net)
   - JIRA_EMAIL: Your Jira email
   - JIRA_API_TOKEN: Your Jira API token
   - JIRA_PROJECT: Project key to query (optional, default: TEST)

2. Run the script (after starting the container):
   docker compose up -d
   docker compose exec jira-time-machine python examples/example.py
"""

import os
import sys
from datetime import datetime
import pandas as pd

try:
    from jira import JIRA
    from jira_time_machine import JiraTimeMachine
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Make sure you're running this inside the Docker container")
    sys.exit(1)


def main():
    # Get configuration from environment variables
    jira_server = os.getenv("JIRA_SERVER")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    project = os.getenv("JIRA_PROJECT", "TEST")

    if not all([jira_server, jira_email, jira_api_token]):
        print("Error: Missing required environment variables!")
        print("\nRequired environment variables:")
        print("  - JIRA_SERVER: Your Jira server URL")
        print("  - JIRA_EMAIL: Your Jira email")
        print("  - JIRA_API_TOKEN: Your Jira API token")
        print("\nOptional environment variables:")
        print("  - JIRA_PROJECT: Project key to query (default: TEST)")
        print("\nExample usage:")
        print('  docker compose run -e JIRA_SERVER="https://your-instance.atlassian.net" \\')
        print('                      -e JIRA_EMAIL="your@email.com" \\')
        print('                      -e JIRA_API_TOKEN="your-token" \\')
        print('                      -e JIRA_PROJECT="MYPROJECT" \\')
        print('                      jira-time-machine python examples/example.py')
        return 1

    print(f"Connecting to Jira server: {jira_server}")
    
    try:
        # Initialize JIRA instance
        jira = JIRA(
            server=jira_server,
            basic_auth=(jira_email, jira_api_token)
        )
        
        # Initialize JiraTimeMachine
        jira_time_machine = JiraTimeMachine(jira)
        
        # Specify JQL query and fields to track
        jql_query = f"project = {project}"
        fields_to_track = ["Status", "Assignee", "Priority"]
        
        print(f"\nFetching history for query: {jql_query}")
        print(f"Tracking fields: {', '.join(fields_to_track)}\n")
        
        # Get the history of issues
        history_df = jira_time_machine.history(jql_query, fields_to_track)
        
        print(f"Retrieved {len(history_df)} history records")
        print("\nFirst few records:")
        print(history_df.head(10))
        
        # Save history to CSV
        output_file = "/app/output/jira_history.csv"
        os.makedirs("/app/output", exist_ok=True)
        history_df.to_csv(output_file)
        print(f"\nHistory saved to: {output_file}")
        
        # Get a snapshot at a historical point in time to demonstrate the time machine
        # Using a date from 6 months ago to show historical state
        snapshot_date = pd.Timestamp.now() - pd.DateOffset(months=6)
        snapshot = jira_time_machine.snapshot(history_df, snapshot_date)
        print(f"\nSnapshot at {snapshot_date.strftime('%Y-%m-%d')} ({len(snapshot)} issues):")
        print(snapshot)
        
        # Save snapshot to CSV
        snapshot_file = "/app/output/jira_snapshot.csv"
        snapshot.to_csv(snapshot_file)
        print(f"\nSnapshot saved to: {snapshot_file}")
        
        print("\n✓ Success! Check the output directory for results.")
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
