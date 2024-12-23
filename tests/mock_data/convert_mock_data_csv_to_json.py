import pandas as pd
import json

def convert_to_empty_string(value):
    if pd.isna(value):
        return ''
    return value

def convert_csv_to_mock_json():

    input_csv = "mock_data.csv"
    output_json = "mock_jira_issues.json"
    # Read the CSV file
    df = pd.read_csv(input_csv, na_filter=False, converters={
        'from': convert_to_empty_string,
        'to': convert_to_empty_string,
        'labels': convert_to_empty_string
    })

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
                "reporter": {"displayName": None},
                "assignee": {"displayName": None},
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
                issue_data["fields"]["reporter"]["displayName"] = row["author"]

            elif row["type"] == "current":
                issue_data["fields"]["status"] = row["status"]
                issue_data["fields"]["priority"] = row["priority"]
                issue_data["fields"]["assignee"]["displayName"] = row["assignee"]
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


if __name__ == "__main__":
    convert_csv_to_mock_json()
