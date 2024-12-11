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

    def fetch_backlog_history(self, jql_query, fields_to_track):
        """
        Fetch the full change history of Jira issues for specified fields.

        Args:
            jql_query (str): JQL query to select issues.
            fields_to_track (list): List of Jira fields to track changes for.

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
            initial_state = {("Tracked Fields", field): None for field in fields_to_track}
            initial_state.update({
                ("Record", "issue_id"): issue_id,
                ("Record", "type"): "created",
                ("Record", "date"): created_at,
                ("Record", "author"): getattr(issue.fields.reporter, "displayName", "Unknown")
            })
            history_data.append(initial_state)

            # Add changes from changelog
            for change in changelog:
                change_date = pd.to_datetime(change.created)
                for item in change.items:
                    if item.field in fields_to_track:
                        history_data.append({
                            ("Record" ,"issue_id"): issue_id,
                            # ("Change", item.field): item.toString,
                            ("Record" ,"type"): "change",
                            ("Record" ,"date"): change_date,
                            ("Change" ,"field"): item.field,
                            ("Change" ,"from"): item.fromString,
                            ("Change" ,"to"): item.toString,
                            ("Change" ,"author"): getattr(change.author, "displayName", "Unknown")
                        })

            # Add the current state
            current_state = {("Tracked Fields", field): getattr(issue.fields, field, None) for field in fields_to_track}
            current_state.update({
                ("Record", "date"): pd.Timestamp.utcnow(),
                ("Record", "issue_id"): issue_id,
                ("Record", "type"): "current",
                ("Record", "author"): "System"
            })
            history_data.append(current_state)

        history_df = pd.DataFrame(history_data)
        multi_tuples = [('Record','issue_id'), ('Record','type'), ('Record','date'), ('Record','author'), ('Change','field'), ('Change','from'), ('Change','to')] + [('Tracked Fields', field) for field in fields_to_track]
        multi_cols = pd.MultiIndex.from_tuples(multi_tuples, names=['Section', 'Field'])
        history_df = pd.DataFrame(history_df, columns=multi_cols)
        # history_df.sort_values(by=["issue_id", "date", "type"], inplace=True)
        # history_df[fields_to_track] = history_df.groupby("issue_id")[fields_to_track].bfill()
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
