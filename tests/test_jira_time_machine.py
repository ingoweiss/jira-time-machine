import pytest
from .mocks import MockJira
from jira_time_machine import JiraTimeMachine
import pandas as pd

@pytest.fixture
def mock_jira():
    return MockJira("tests/mock_data/mock_jira_issues.json", "tests/mock_data/mock_jira_fields.json")

@pytest.fixture
def jira_time_machine(mock_jira):
    # Initialize JiraTimeMachine with the mock Jira instance
    return JiraTimeMachine(mock_jira)

def test_history(jira_time_machine):
    # Test fetching backlog history
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]

    history_df = jira_time_machine.history(jql_query, fields_to_track)

    records = history_df[history_df[('Record', 'issue_id')] == "PROJ-0001"]
    assert len(records) == 4
    assert len(records[records[("Record", "type")] == "initial"]) == 1
    assert len(records[records[("Record", "type")] == "change"]) == 2
    # assert len(records[records[("Record", "type")] == "current"]) == 1

    proj_0001_current = history_df[(history_df[('Record', 'issue_id')] == 'PROJ-0001') & (history_df[('Record', 'type')] == 'current')].iloc[0]
    assert proj_0001_current[('Tracked', 'Status')] == "Submitted"
    assert proj_0001_current[('Tracked', 'Priority')] == "Major"

    proj_0001_last_change = history_df[(history_df[('Record', 'issue_id')] == 'PROJ-0001') & (history_df[('Record', 'type')] == 'change')].iloc[-1]
    assert proj_0001_last_change[('Tracked', 'Status')] == "Submitted"
    assert proj_0001_last_change[('Tracked', 'Priority')] == "Major"

    proj_0001_initial = history_df[(history_df[('Record', 'issue_id')] == 'PROJ-0001') & (history_df[('Record', 'type')] == 'initial')].iloc[-1]
    assert proj_0001_initial[('Tracked', 'Status')] == "New"
    assert proj_0001_initial[('Tracked', 'Priority')] == "Minor"


def test_snapshot(jira_time_machine):
    # Test backlog snapshots
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    dt = pd.to_datetime('2024-10-16', utc=True)
    snapshot = jira_time_machine.get_snapshot(history_df, dt)
    assert ('PROJ-0001' in snapshot.index)
    assert ('PROJ-0002' not in snapshot.index)

    assert snapshot.at['PROJ-0001', 'Status'] == 'New'
    # assert snapshot.at['PROJ-0001', 'assignee'] == 'Wynton Kelly'
    assert snapshot.at['PROJ-0001', 'Priority'] == 'Major'
