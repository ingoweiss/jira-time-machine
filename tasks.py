from invoke import task

import pandas as pd
import json


def convert_to_empty_string(value):
    if pd.isna(value):
        return ""
    return value


@task
def build_mock_data(c):

    input_csv = "tests/mock_data/mock_jira_history.csv"
    output_json = "tests/mock_data/mock_jira_issues.json"
    # Read the CSV file
    df = pd.read_csv(
        input_csv,
        na_filter=False,
        converters={
            "from": convert_to_empty_string,
            "to": convert_to_empty_string,
            "labels": convert_to_empty_string,
        },
    )

    # Dictionary to hold the mock data
    mock_data = {"issues": []}

    # Group data by issue_id
    grouped = df.groupby("issue_id")

    for issue_id, group in grouped:
        # Initialize issue fields
        issue_data = {
            "key": issue_id,
            "fields": {
                "created": None,
                "reporter": None,
                "assignee": None,
                "status": None,
                "priority": None,
                "type": None,
                "summary": None,
            },
            "changelog": {"histories": []},
        }

        for _, row in group.iterrows():
            # Handle 'initial' and 'current' fields
            if row["type"] == "initial":
                issue_data["fields"]["created"] = row["date"]
                issue_data["fields"]["reporter"] = {"displayName": row["author"]}

            elif row["type"] == "current":
                issue_data["fields"]["status"] = {"name": row["status"]}
                issue_data["fields"]["priority"] = {"name": row["priority"]}
                if row["assignee"] == "":
                    issue_data["fields"]["assignee"] = None
                else:
                    issue_data["fields"]["assignee"] = {"displayName": row["assignee"]}
                issue_data["fields"]["summary"] = row["summary"]
                issue_data["fields"]["labels"] = row["labels"].split()

            # Handle changes
            elif row["type"] == "change":
                change_item = {
                    "created": row["date"],
                    "author": {"displayName": row["author"]},
                    "items": [
                        {
                            "field": row["field"],
                            "fromString": row["from"],
                            "toString": row["to"],
                        }
                    ],
                }
                issue_data["changelog"]["histories"].append(change_item)

        mock_data["issues"].append(issue_data)

    # Write the JSON output
    with open(output_json, "w") as f:
        json.dump(mock_data, f, indent=4)
