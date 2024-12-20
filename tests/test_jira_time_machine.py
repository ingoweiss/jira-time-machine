import pytest
from unittest.mock import patch
from .mocks import MockJira
from jira_time_machine import JiraTimeMachine
import pandas as pd


@pytest.fixture
def mock_jira():
    return MockJira(
        "tests/mock_data/mock_jira_issues.json", "tests/mock_data/mock_jira_fields.json"
    )


@pytest.fixture
def jira_time_machine(mock_jira):
    with patch("jira.JIRA", return_value=mock_jira):
        return JiraTimeMachine(mock_jira)


def test_history_has_issue_initial_state_and_changes(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)
    proj_0001_records = history_df[history_df[("Record", "issue_id")] == "PROJ-0001"]
    proj_0002_records = history_df[history_df[("Record", "issue_id")] == "PROJ-0002"]

    # PROJ-0001 has 3 records: 1 initial and 2 changes
    assert len(proj_0001_records) == 3
    assert (
        len(proj_0001_records[proj_0001_records[("Record", "type")] == "initial"]) == 1
    )
    assert (
        len(proj_0001_records[proj_0001_records[("Record", "type")] == "change"]) == 2
    )

    # PROJ-0002 has 1 record: 1 initial and no changes
    assert len(proj_0002_records) == 1
    assert (
        len(proj_0002_records[proj_0002_records[("Record", "type")] == "initial"]) == 1
    )
    assert (
        len(proj_0002_records[proj_0002_records[("Record", "type")] == "change"]) == 0
    )


def test_history_has_correct_initial_states(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    proj_0001_initial_record = history_df[
        (history_df[("Record", "issue_id")] == "PROJ-0001")
        & (history_df[("Record", "type")] == "initial")
    ].iloc[0]
    assert proj_0001_initial_record[("Tracked", "Status")] == "New"
    assert proj_0001_initial_record[("Tracked", "Priority")] == "Minor"

    proj_0002_initial_record = history_df[
        (history_df[("Record", "issue_id")] == "PROJ-0002")
        & (history_df[("Record", "type")] == "initial")
    ].iloc[0]
    assert proj_0002_initial_record[("Tracked", "Status")] == "New"
    assert proj_0002_initial_record[("Tracked", "Priority")] == "Major"


def test_history_has_correct_current_states(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    proj_0001_last_record = history_df[
        history_df[("Record", "issue_id")] == "PROJ-0001"
    ].iloc[-1]
    assert proj_0001_last_record[("Tracked", "Status")] == "Submitted"
    assert proj_0001_last_record[("Tracked", "Priority")] == "Major"

    proj_0002_last_record = history_df[
        history_df[("Record", "issue_id")] == "PROJ-0002"
    ].iloc[-1]
    assert proj_0002_last_record[("Tracked", "Status")] == "New"
    assert proj_0002_last_record[("Tracked", "Priority")] == "Major"


def test_history_handles_user_type_fiels_correctly(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    proj_0001_last_record = history_df[
        history_df[("Record", "issue_id")] == "PROJ-0001"
    ].iloc[-1]

    assert proj_0001_last_record[("Tracked", "Assignee")] == "Wynton Kelly"


def test_snapshot_includes_correct_issues(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)
    dt = pd.to_datetime("2024-10-16", utc=True)
    snapshot = jira_time_machine.snapshot(history_df, dt)

    assert "PROJ-0001" in snapshot.index
    assert "PROJ-0002" not in snapshot.index  # was created after dt


def test_snapshot_has_correct_issue_states(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)
    dt = pd.to_datetime("2024-10-16", utc=True)
    snapshot = jira_time_machine.snapshot(history_df, dt)

    assert snapshot.at["PROJ-0001", "Status"] == "New"
    assert snapshot.at["PROJ-0001", "Priority"] == "Major"
