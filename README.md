# Jira Time Machine

Jira Time Machine gives access to the state of a Jira project's issues at any time in its history.

[![Build](https://github.com/ingoweiss/jira-time-machine/actions/workflows/build.yml/badge.svg)](https://github.com/ingoweiss/jira-time-machine/actions/workflows/build.yml)
![PyPI - Version](https://img.shields.io/pypi/v/jira-time-machine)
![PyPI - License](https://img.shields.io/pypi/l/jira-time-machine)
[![Downloads](https://static.pepy.tech/badge/jira-time-machine)](https://pepy.tech/project/jira-time-machine)
![Style Black](https://img.shields.io/badge/style-black-000000)

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

To install Jira Time Machine, you can use pip:

```sh
pip install jira-time-machine
```

## Usage

### (1) Initialization

```python
from jira import JIRA
from jira_time_machine import JiraTimeMachine

# Initialize a JIRA instance
jira = JIRA(server='https://your-jira-instance.atlassian.net', basic_auth=('email', 'api_token'))

# Initialize the JiraTimeMachine instance
jira_time_machine = JiraTimeMachine(jira)
```

### (2) History

```python
# Specify a JQL query and fields to track
jql_query = "project = TEST"
fields_to_track = ["Status", "Assignee", "Priority"]

# Get the history of the issues
history_df = jira_time_machine.history(jql_query, fields_to_track)
```

```bash
| Record    |        |            |        | Change   |              |             | Tracked     |          |          |
|-----------|--------|------------|--------|----------|--------------|-------------|-------------|----------|----------|
| Key       | Type   | Date       | Author | Field    | From         | To          | Status      | Assignee | Priority |
| PROJ-0001 | initial| 2022-12-01 | Alice  |          |              |             | New         |          | Major    |
| PROJ-0001 | change | 2022-12-05 | Bob    | Status   | New          | In Progress | In Progress |          | Major    |
| PROJ-0001 | change | 2022-12-10 | Carol  | Priority | Major        | Critical    | In Progress |          | Critical |
| PROJ-0002 | initial| 2022-12-15 | Dave   |          |              |             | New         |          | Major    |
```

### (3) Snapshot

```python
# Get a snapshot of the backlog at a specific timestamp
snapshot = jira_time_machine.snapshot(history_df, pd.Timestamp('2023-01-01'))
```

```bash
| Key       | Status     | Assignee | Priority |
|-----------|------------|----------|----------|
| PROJ-0001 | Submitted  |          | Major    |
| PROJ-0002 | New        |          | Major    |
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

