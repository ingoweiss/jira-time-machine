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

    records = history_df[history_df["Record", "issue_id"] == "PROJ-0001"]
    assert len(records) == 4, "Should have 5 records for PROJ-0001"
    assert len(records[records["Record", "type"] == "created"]) == 1, "Should have 1 'created' record for PROJ-0001"
    assert len(records[records["Record", "type"] == "change"]) == 2, "Should have 2 'change' records for PROJ-0001"
    assert len(records[records["Record", "type"] == "current"]) == 1, "Should have 1 'current' record for PROJ-0001"
