import pytest
from .mocks import MockJira
from jira_time_machine import JiraTimeMachine
import pandas as pd

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
    fields_to_track = ["status", "assignee", "priority"]

    history_df = jira_time_machine.history(jql_query, fields_to_track)

    records = history_df[history_df[('Record', 'issue_id')] == "PROJ-0001"]
    assert len(records) == 4, "Should have 5 records for PROJ-0001"
    assert len(records[records[("Record", "type")] == "initial"]) == 1, "Should have 1 'initial' record for PROJ-0001"
    assert len(records[records[("Record", "type")] == "change"]) == 2, "Should have 2 'change' records for PROJ-0001"
    assert len(records[records[("Record", "type")] == "current"]) == 1, "Should have 1 'current' record for PROJ-0001"

    proj_0001_current = history_df[(history_df[('Record', 'issue_id')] == 'PROJ-0001') & (history_df[('Record', 'type')] == 'current')].iloc[0]
    assert proj_0001_current[('Tracked', 'status')] == "Submitted", "PROJ-0001 current status should be 'Submitted'"
    assert proj_0001_current[('Tracked', 'priority')] == "Major", "PROJ-0001 current priority should be 'Major'"

    proj_0001_last_change = history_df[(history_df[('Record', 'issue_id')] == 'PROJ-0001') & (history_df[('Record', 'type')] == 'change')].iloc[-1]
    assert proj_0001_last_change[('Tracked', 'status')] == "Submitted", "PROJ-0001 current status should be 'Submitted'"
    assert proj_0001_last_change[('Tracked', 'priority')] == "Major", "PROJ-0001 current priority should be 'Major'"

    proj_0001_initial = history_df[(history_df[('Record', 'issue_id')] == 'PROJ-0001') & (history_df[('Record', 'type')] == 'initial')].iloc[-1]
    assert proj_0001_initial[('Tracked', 'status')] == "New", "PROJ-0001 initial status should be 'New'"
    assert proj_0001_initial[('Tracked', 'priority')] == "Minor", "PROJ-0001 initial priority should be 'Minor'"


def test_snapshot(jira_time_machine):
    # Test backlog snapshots
    jql_query = "project = TEST"
    fields_to_track = ["status", "assignee", "priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    dt = pd.to_datetime('2024-10-16', utc=True)
    snapshot = jira_time_machine.get_snapshot(history_df, dt)
    assert ('PROJ-0001' in snapshot.index), "PROJ-0001 should be in the snapshot"
    assert ('PROJ-0002' not in snapshot.index), "PROJ-0002 should NOT be in the snapshot (created later)"

    assert snapshot.at['PROJ-0001', 'status'] == 'New'
    # assert snapshot.at['PROJ-0001', 'assignee'] == 'Wynton Kelly'
    assert snapshot.at['PROJ-0001', 'priority'] == 'Major'
