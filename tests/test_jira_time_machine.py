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

def test_history(jira_time_machine):
    # Test fetching backlog history
    jql_query = "project = TEST"
    fields_to_track = ["status", "assignee", "priority", "type"]

    history_df = jira_time_machine.history(jql_query, fields_to_track)

    records = history_df[history_df["issue_id"] == "PROJ-0001"]
    assert len(records) == 4, "Should have 5 records for PROJ-0001"
    assert len(records[records["type"] == "initial"]) == 1, "Should have 1 'initial' record for PROJ-0001"
    assert len(records[records["type"] == "change"]) == 2, "Should have 2 'change' records for PROJ-0001"
    assert len(records[records["type"] == "current"]) == 1, "Should have 1 'current' record for PROJ-0001"

    proj_0001_current = history_df[(history_df['issue_id'] == 'PROJ-0001') & (history_df['type'] == 'current')].iloc[0]
    assert proj_0001_current[('Tracked', 'status')] == "Submitted", "PROJ-0001 current status should be 'Submitted'"
    assert proj_0001_current[('Tracked', 'priority')] == "Major", "PROJ-0001 current priority should be 'Major'"

    proj_0001_last_change = history_df[(history_df['issue_id'] == 'PROJ-0001') & (history_df['type'] == 'change')].iloc[-1]
    assert proj_0001_last_change[('Tracked', 'status')] == "Submitted", "PROJ-0001 current status should be 'Submitted'"
    assert proj_0001_last_change[('Tracked', 'priority')] == "Major", "PROJ-0001 current priority should be 'Major'"

    proj_0001_created = history_df[(history_df['issue_id'] == 'PROJ-0001') & (history_df['type'] == 'change')].iloc[-1]
    assert proj_0001_created[('Tracked', 'status')] == "New", "PROJ-0001 current status should be 'New'"
    assert proj_0001_created[('Tracked', 'priority')] == "Minor", "PROJ-0001 current priority should be 'Minor'"
