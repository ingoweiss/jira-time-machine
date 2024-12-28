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
    grouped = df.groupby("Key")

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
                "summary": None,
                "labels": [],
            },
            "changelog": {"histories": []},
        }

        for _, row in group.iterrows():
            # Handle 'initial' and 'current' fields
            if row["Type"] == "initial":
                issue_data["fields"]["created"] = row["Date"]
                issue_data["fields"]["reporter"] = {"displayName": row["Author"]}

            elif row["Type"] == "current":
                issue_data["fields"]["status"] = {"name": row["Status"]}
                issue_data["fields"]["priority"] = {"name": row["Priority"]}
                if row["Assignee"] == "":
                    issue_data["fields"]["Assignee"] = None
                else:
                    issue_data["fields"]["assignee"] = {"displayName": row["Assignee"]}
                issue_data["fields"]["summary"] = row["Summary"]
                issue_data["fields"]["labels"] = row["Labels"].split()

        # Handle changes
        changes_grouped = group[group["Type"] == "change"].groupby(
            ["Change ID", "Date", "Author"]
        )
        for (change_id, change_date, change_author), change_group in changes_grouped:
            change_items = []
            for _, change_row in change_group.iterrows():
                change_item = {
                    "field": change_row["Field"],
                    "fromString": change_row["From"],
                    "toString": change_row["To"],
                }
                change_items.append(change_item)

            change_data = {
                "id": change_id,
                "created": change_date,
                "author": {"displayName": change_author},
                "items": change_items,
            }
            issue_data["changelog"]["histories"].append(change_data)

        mock_data["issues"].append(issue_data)

    # Write the JSON output
    with open(output_json, "w") as f:
        json.dump(mock_data, f, indent=4)
