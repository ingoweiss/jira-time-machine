import pytest
from .mocks import MockJira
from jira_time_machine import JiraTimeMachine

@pytest.fixture
def mock_jira():
    return MockJira("tests/mock_data/mock_jira_data.json")

@pytest.fixture
def jira_time_machine(mock_jira):
    # Initialize JiraTimeMachine with the mock Jira instance
    return JiraTimeMachine(mock_jira)

def test_fetch_backlog_history(jira_time_machine):
    # Test fetching backlog history
    jql_query = "project = TEST"
    fields_to_track = ["status", "assignee", "priority", "type"]

    history_df = jira_time_machine.fetch_backlog_history(jql_query, fields_to_track)

    records = history_df[history_df["issue_id"] == "PROJ-0001"]
    assert len(records) == 4, "Should have 5 records for PROJ-0001"
    assert len(records[records['type'] == 'created']) == 1, "Should have 1 'created' record for PROJ-0001"
    assert len(records[records['type'] == 'change']) == 2, "Should have 2 'change' records for PROJ-0001"
    assert len(records[records['type'] == 'current']) == 1, "Should have 1 'current' record for PROJ-0001"


    # Assert the structure and data of the DataFrame
    assert not history_df.empty, "History DataFrame should not be empty"
    assert "issue_id" in history_df.columns, "DataFrame should have issue_id column"
    assert "status" in history_df.columns, "DataFrame should have status column"

    # Add additional assertions based on expected mock data
    assert (history_df["issue_id"] == "PROJ-0001").any(), "Should contain PROJ-0001"

# def test_get_snapshot(jira_time_machine):
#     # Test getting a snapshot of the backlog at a specific date
#     jql_query = "project = TEST"
#     fields_to_track = ["status", "assignee", "priority", "type"]

#     history_df = jira_time_machine.fetch_backlog_history(jql_query, fields_to_track)

#     # Get a snapshot for a specific date
#     snapshot_date = "2024-11-15"
#     snapshot = jira_time_machine.get_snapshot(history_df, snapshot_date)

#     # Assert the structure and data of the snapshot
#     assert not snapshot.empty, "Snapshot DataFrame should not be empty"
#     assert "status" in snapshot.columns, "Snapshot should have status column"
#     assert (snapshot["status"] == "Submitted").any(), "Snapshot should include 'Submitted' status"

