from jira import JIRA
import pandas as pd
from tqdm import tqdm
import numpy as np

class JiraTimeMachine:
    def __init__(self, jira_instance):
        """
        Initialize the JiraTimeMachine instance with a jiRA instance.
        """
        self.jira = jira_instance

    def history(self, jql_query, tracked_fields):
        """
        Fetch the full change history of Jira issues for specified fields.

        Args:
            jql_query (str): JQL query to select issues.
            tracked_fields (list): List of Jira fields to track changes for.

        Returns:
            pd.DataFrame: A DataFrame with issue states over time.
        """
        issues = self.jira.search_issues(jql_query, expand="changelog", maxResults=False)
        history_data = []

        for issue in tqdm(issues, desc="Processing issues"):
            issue_id = issue.key
            created_at = pd.to_datetime(issue.fields.created)
            changelog = issue.changelog.histories

            # Add the initial state
            initial_state = {("Tracked", field): np.NaN for field in tracked_fields}
            initial_state.update({
                "issue_id": issue_id,
                "type": "initial",
                "date": created_at,
                "author": getattr(issue.fields.reporter, "displayName", "Unknown")
            })
            history_data.append(initial_state)

            # Add changes from changelog
            for change in changelog:
                change_date = pd.to_datetime(change.created)
                for item in change.items:
                    if item.field in tracked_fields:
                        history_data.append({
                            "issue_id": issue_id,
                            "type": "change",
                            "date": change_date,
                            "field": item.field,
                            "from": item.fromString,
                            "to": item.toString,
                            "author": getattr(change.author, "displayName", "Unknown")
                        })

            # Add the current state
            current_state = {("Tracked", field): getattr(issue.fields, field, np.NaN) for field in tracked_fields}
            current_state.update({
                "date": pd.Timestamp.utcnow(),
                "issue_id": issue_id,
                "type": "current",
                "author": "System"
            })
            history_data.append(current_state)

        history_df = pd.DataFrame(history_data)
        history_df.sort_values(by=["issue_id", "date"], inplace=True)
        history_df = history_df[['issue_id', 'type', 'date', 'author', 'field', 'from', 'to'] + [("Tracked", field) for field in tracked_fields]]

        return history_df

    def get_snapshot(self, history_df, dt):
        """
        Get the snapshot of the backlog at a specific timestamp.

        Args:
            history_df (pd.DataFrame): The history DataFrame.
            dt (pd.Timestamp): The timestamp for the snapshot.

        Returns:
            pd.DataFrame: A snapshot of the backlog at the given timestamp.
        """
        snapshot = (
            history_df[history_df["date"] > dt]
            .sort_values("date")
            .groupby("issue_id")
            .first()
        )
        return snapshot
