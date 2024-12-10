import pandas as pd
import json
import argparse
from collections import defaultdict

def convert_csv_to_mock_json(input_csv, output_json):
    # Read the CSV file
    df = pd.read_csv(input_csv)

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
                "type": None
            },
            "changelog": {
                "histories": []
            }
        }

        for _, row in group.iterrows():
            # Handle 'created' and 'current' fields
            if row['type'] == 'created':
                issue_data["fields"]["created"] = row["date"]
                issue_data["fields"]["reporter"]["displayName"] = row["author"]
                issue_data["fields"]["assignee"]["displayName"] = row["assignee"]
                issue_data["fields"]["status"] = row["status"]
                issue_data["fields"]["priority"] = row["priority"]
                issue_data["fields"]["type"] = row["type"]

            elif row['type'] == 'current':
                issue_data["fields"]["status"] = row["status"]
                issue_data["fields"]["priority"] = row["priority"]
                issue_data["fields"]["assignee"]["displayName"] = row["assignee"]

            # Handle changes
            elif row['type'] == 'change':
                change_item = {
                    "created": row["date"],
                    "author": {"displayName": row["author"]},
                    "items": [
                        {
                            "field": row["field"],
                            "fromString": row["from"],
                            "toString": row["to"]
                        }
                    ]
                }
                issue_data["changelog"]["histories"].append(change_item)

        mock_data["issues"].append(issue_data)

    # Write the JSON output
    with open(output_json, "w") as f:
        json.dump(mock_data, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CSV mock data to JSON for mocking Jira.")
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument("output_json", help="Path to the output JSON file.")
    args = parser.parse_args()

    convert_csv_to_mock_json(args.input_csv, args.output_json)