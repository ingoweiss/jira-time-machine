from unittest.mock import MagicMock
import json

class MockJira:
    def __init__(self, mock_data_file):
        with open(mock_data_file, "r") as f:
            self.mock_data = json.load(f)

    def search_issues(self, jql_query, expand=None, maxResults=None):
        return [MockIssue(issue) for issue in self.mock_data["issues"]]

class MockIssue:
    def __init__(self, issue_data):
        self.key = issue_data["key"]
        self.fields = MagicMock()
        self.fields.created = issue_data["fields"]["created"]
        self.fields.reporter = MagicMock(displayName=issue_data["fields"].get("reporter", {}).get("displayName", "Unknown"))
        for field, value in issue_data["fields"].items():
            setattr(self.fields, field, value)
        self.changelog = MockChangelog(issue_data.get("changelog", {}))

class MockChangelog:
    def __init__(self, changelog_data):
        self.histories = [
            MockHistory(history) for history in changelog_data.get("histories", [])
        ]

class MockHistory:
    def __init__(self, history_data):
        self.created = history_data["created"]
        self.author = MagicMock(displayName=history_data.get("author", {}).get("displayName", "Unknown"))
        self.items = [
            MockChangeItem(item) for item in history_data.get("items", [])
        ]

class MockChangeItem:
    def __init__(self, item_data):
        self.field = item_data["field"]
        self.fromString = item_data.get("fromString")
        self.toString = item_data.get("toString")