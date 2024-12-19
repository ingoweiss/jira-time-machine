# Jira Time Machine

Jira Time Machine gives you the state of your Jira project at any time in its history.

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

```python

from jira import JIRA
from jira_time_machine import JiraTimeMachine

# Initialize a JIRA instance
jira = JIRA(server='https://your-jira-instance.atlassian.net', basic_auth=('email', 'api_token'))

# Initialize the JiraTimeMachine instance
jira_time_machine = JiraTimeMachine(jira)

# Specify a JQL query and fields to track
jql_query = "project = TEST"
fields_to_track = ["Status", "Assignee", "Priority"]

# Get the history of the issues
history_df = jira_time_machine.history(jql_query, fields_to_track)

# Get a snapshot of the backlog at a specific timestamp
snapshot = jira_time_machine.snapshot(history_df, pd.Timestamp('2023-01-01'))
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

