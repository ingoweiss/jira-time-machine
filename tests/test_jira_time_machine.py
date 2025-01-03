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


def test_history_has_only_tracked_fields(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Priority"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)
    assert list(history_df["Tracked"].columns) == ["Status", "Priority"]


def test_history_has_issue_initial_state_and_changes(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority", "Labels"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)
    proj_0001_records = history_df[history_df[("Record", "Key")] == "PROJ-0001"]
    proj_0002_records = history_df[history_df[("Record", "Key")] == "PROJ-0002"]

    assert len(proj_0001_records) == 6
    assert (
        len(proj_0001_records[proj_0001_records[("Record", "Type")] == "initial"]) == 1
    )
    assert (
        len(proj_0001_records[proj_0001_records[("Record", "Type")] == "change"]) == 5
    )

    assert len(proj_0002_records) == 1
    assert (
        len(proj_0002_records[proj_0002_records[("Record", "Type")] == "initial"]) == 1
    )
    assert (
        len(proj_0002_records[proj_0002_records[("Record", "Type")] == "change"]) == 0
    )


def test_history_has_correct_initial_states(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority", "Labels"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    proj_0001_initial_record = history_df[
        (history_df[("Record", "Key")] == "PROJ-0001")
        & (history_df[("Record", "Type")] == "initial")
    ].iloc[0]
    assert proj_0001_initial_record[("Tracked", "Status")] == "New"
    assert proj_0001_initial_record[("Tracked", "Priority")] == "Minor"
    assert proj_0001_initial_record[("Tracked", "Labels")] == ["tag1"]
    assert proj_0001_initial_record[("Record", "Author")] == "Tommy Flanagan"

    proj_0002_initial_record = history_df[
        (history_df[("Record", "Key")] == "PROJ-0002")
        & (history_df[("Record", "Type")] == "initial")
    ].iloc[0]
    assert proj_0002_initial_record[("Tracked", "Status")] == "New"
    assert proj_0002_initial_record[("Tracked", "Priority")] == "Major"
    assert proj_0002_initial_record[("Tracked", "Labels")] == []
    assert proj_0002_initial_record[("Record", "Author")] == "Red Garland"


def test_history_has_correct_current_states(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Status", "Assignee", "Priority", "Labels"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    proj_0001_last_record = history_df[
        history_df[("Record", "Key")] == "PROJ-0001"
    ].iloc[-1]
    assert proj_0001_last_record[("Tracked", "Status")] == "Submitted"
    assert proj_0001_last_record[("Tracked", "Priority")] == "Major"
    assert proj_0001_last_record[("Tracked", "Labels")] == ["tag1", "tag2"]
    assert proj_0001_last_record[("Tracked", "Assignee")] is None

    proj_0002_last_record = history_df[
        history_df[("Record", "Key")] == "PROJ-0002"
    ].iloc[-1]
    assert proj_0002_last_record[("Tracked", "Status")] == "New"
    assert proj_0002_last_record[("Tracked", "Priority")] == "Major"
    assert proj_0002_last_record[("Tracked", "Labels")] == []
    assert proj_0002_last_record[("Tracked", "Assignee")] == "Red Garland"


def test_history_handles_user_type_fiels_correctly(jira_time_machine):
    jql_query = "project = TEST"
    fields_to_track = ["Assignee"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)

    proj_0001_initial_record = history_df[
        (history_df[("Record", "Key")] == "PROJ-0001")
        & (history_df[("Record", "Type")] == "initial")
    ].iloc[-1]
    assert proj_0001_initial_record[("Tracked", "Assignee")] == "Wynton Kelly"

    proj_0001_last_record = history_df[
        history_df[("Record", "Key")] == "PROJ-0001"
    ].iloc[-1]
    assert proj_0001_last_record[("Tracked", "Assignee")] is None


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
    fields_to_track = ["Status", "Assignee", "Priority", "Labels"]
    history_df = jira_time_machine.history(jql_query, fields_to_track)
    dt = pd.to_datetime("2024-10-16", utc=True)
    snapshot = jira_time_machine.snapshot(history_df, dt)

    assert snapshot.at["PROJ-0001", "Status"] == "New"
    assert snapshot.at["PROJ-0001", "Priority"] == "Major"
    assert snapshot.at["PROJ-0001", "Assignee"] == "Wynton Kelly"
    assert snapshot.at["PROJ-0001", "Labels"] == ["tag1"]

    dt = pd.to_datetime("2024-11-10", utc=True)
    snapshot = jira_time_machine.snapshot(history_df, dt)
    assert snapshot.at["PROJ-0001", "Status"] == "Submitted"
    assert snapshot.at["PROJ-0001", "Priority"] == "Major"
    assert snapshot.at["PROJ-0001", "Assignee"] is None
    assert snapshot.at["PROJ-0001", "Labels"] == ["tag1", "tag2"]


def test_history_throws_exception_on_wrong_field_name(jira_time_machine):

    jql_query = "project = TEST"
    fields_to_track = ["Not A Field Name"]
    with pytest.raises(
        ValueError, match="Could not find field with name 'Not A Field Name'"
    ):
        jira_time_machine.history(jql_query, fields_to_track)
