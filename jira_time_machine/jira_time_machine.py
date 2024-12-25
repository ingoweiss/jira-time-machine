import pandas as pd
from tqdm import tqdm
import numpy as np


class JiraTimeMachine:

    def __init__(self, jira_instance):
        """
        Initialize the JiraTimeMachine instance.

        Args:
            jira_instance: An instance of the JIRA class.
        """
        self.jira = jira_instance

    def history(self, jql_query, tracked_fields):
        """
        Fetch the full change history of Jira issues for specified fields.

        Args:
            jql_query (str): JQL query to select issues.
            tracked_fields (list): List of Jira fields to track changes for.

        Returns:
            pd.DataFrame: A DataFrame with issue states over time.
        """
        self.tracked_fields = tracked_fields
        self.tracked_fields_info = [
            field for field in self.jira.fields() if field["name"] in tracked_fields
        ]
        self.tracked_field_ids = [f["id"] for f in self.tracked_fields_info]
        self.issues = self.jira.search_issues(
            jql_query, expand="changelog", maxResults=False
        )
        record_dicts = []
        headers = (
            [self.record_field(f) for f in ["issue_id", "type", "date", "author"]]
            + [self.change_field(f) for f in ["field", "from", "to"]]
            + [self.tracked_field(f) for f in tracked_fields]
        )
        record_template = {k: np.nan for k in headers}

        for issue in tqdm(self.issues, desc="Processing issues"):
            issue_id = issue.key
            created_at = pd.to_datetime(issue.fields.created)
            reporter = getattr(issue.fields.reporter, "displayName", "Unknown")
            changelog = issue.changelog.histories

            # (1) Add the issue's initial state:
            # Tracked fields will be initially empty - we will reverse engineer them from the changelog later
            initial_record = record_template.copy()
            initial_record[self.record_field("issue_id")] = issue_id
            initial_record[self.record_field("type")] = "initial"
            initial_record[self.record_field("date")] = created_at
            initial_record[self.record_field("author")] = reporter

            record_dicts.append(initial_record)

            # (2) Add changes from issue's changelog:
            for change in changelog:
                change_date = pd.to_datetime(change.created)
                for item in change.items:
                    change_record = record_template.copy()
                    if item.field in self.tracked_field_ids:

                        change_record[self.record_field("issue_id")] = issue_id
                        change_record[self.record_field("type")] = "change"
                        change_record[self.record_field("date")] = change_date
                        change_record[self.record_field("author")] = getattr(
                            change.author, "displayName", "Unknown"
                        )
                        change_record[self.change_field("field")] = item.field
                        change_record[self.change_field("from")] = (
                            self.normalize_field_value_string(
                                item.field, item.fromString
                            )
                        )
                        change_record[self.change_field("to")] = (
                            self.normalize_field_value_string(item.field, item.toString)
                        )

                        record_dicts.append(change_record)

            # (3) Add the issue's current state which is only needed to reverse engineer the initial state:
            current_record = record_template.copy()
            current_record[self.record_field("date")] = pd.Timestamp.utcnow()
            current_record[self.record_field("issue_id")] = issue_id
            current_record[self.record_field("type")] = "current"
            current_record[self.record_field("author")] = "System"
            for field in tracked_fields:
                field_id = self.field_id_by_name(field)
                field_value = getattr(issue.fields, field_id, np.nan)
                normalized_field_value = self.normalize_field_value(
                    field_id, field_value
                )
                current_record[self.tracked_field(field)] = normalized_field_value

            record_dicts.append(current_record)

        history = pd.DataFrame(record_dicts)
        history.columns = pd.MultiIndex.from_tuples(headers, names=["Section", "Field"])
        history.sort_values(
            by=[self.record_field("issue_id"), self.record_field("date")], inplace=True
        )

        # (4) Reverse engineer tracked field states from the changelog:
        # First, forward fill from the change 'to' values:
        for field in tracked_fields:
            field_id = self.field_id_by_name(field)
            history.loc[
                history[self.change_field("field")] == field_id,
                self.tracked_field(field),
            ] = history[self.change_field("to")]

        # Temporariliy replace initial 'NaN' values so that backfilled values do not
        # spill over into the next issue
        fill_blocker = "[[BLOCKER]]"
        history.loc[history[self.record_field("type")] == "initial", "Tracked"] = (
            fill_blocker
        )
        history["Tracked"] = history["Tracked"].ffill()
        history["Tracked"] = history["Tracked"].replace(fill_blocker, np.nan)

        # Second, backward fill from the change 'from' values:
        for field in tracked_fields:
            field_id = self.field_id_by_name(field)
            history.loc[
                history[self.change_field("field")] == field_id,
                self.tracked_field(field),
            ] = history[self.change_field("from")]
        history["Tracked"] = history["Tracked"].bfill()

        # Finally, restore the change 'to' values:
        for field in tracked_fields:
            field_id = self.field_id_by_name(field)
            history.loc[
                history[self.change_field("field")] == field_id,
                self.tracked_field(field),
            ] = history[self.change_field("to")]

        # remove the 'current' records. They are redundant since the last 'change' record or
        # the 'initial' record (if there are no 'change' records) already has the current state
        # TODO: Might want to sanity check last change state == current state before removing
        history = history[history[self.record_field("type")] != "current"]
        return history

    def snapshot(self, history, dt):
        """
        Get the snapshot of the project at a specific timestamp.

        Args:
            history (pd.DataFrame): The history DataFrame.
            dt (pd.Timestamp): The timestamp for the snapshot.

        Returns:
            pd.DataFrame: A snapshot of the project at the given timestamp.
        """
        snapshot = (
            history[history[self.record_field("date")] <= dt]
            .sort_values(self.record_field("date"))
            .groupby(self.record_field("issue_id"))
            .last()[["Tracked"]]
        )
        snapshot.columns = snapshot.columns.droplevel("Section")
        snapshot.index.name = "issue_id"
        return snapshot

    def field_id_by_name(self, field_name):
        """
        Get the field ID for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            str: The ID of the field.
        """
        field_info = self.field_info_by_name(field_name)
        return field_info["id"]

    def normalize_field_value(self, field_id, field_value):
        """
        Normalize a field value according to its schema.

        Args:
            field_id (str): The ID of the field.
            field_value: The raw field value.

        Returns:
            The normalized field value.
        """
        field_info = self.field_info_by_id(field_id)
        field_schema = field_info["schema"]
        if field_value == None:
            return None
        elif field_schema["type"] == "user":
            return field_value.displayName
        elif field_schema["type"] == "array":
            if field_schema["items"] == "version":
                return [v["name"] for v in field_value]
            else:
                return field_value
        else:
            return field_value

    def normalize_field_value_string(self, field_id, field_value):
        """
        Normalize a field value string according to its schema.

        Args:
            field_id (str): The ID of the field.
            field_value (str): The raw field value string.

        Returns:
            The normalized field value.
        """
        field_info = self.field_info_by_id(field_id)
        field_schema = field_info["schema"]
        if field_schema["type"] == "user":
            if field_value == "":
                return None
            else:
                return field_value
        elif field_schema["type"] == "array":
            if field_schema["items"] in ["string", "version"]:
                return field_value.split()
        else:
            return field_value

    def field_info_by_id(self, field_id):
        """
        Get the field information for a given field ID.

        Args:
            field_id (str): The ID of the field.

        Returns:
            dict: The field information.

        Raises:
            ValueError: If the field ID is not found.
        """
        field_info = next(
            (
                f
                for f in self.tracked_fields_info
                if f["id"] == field_id and not f["custom"]
            ),
            None,
        )
        if field_info == None:
            raise ValueError(f"Could not find field with ID '{field_name}'")
        return field_info

    def field_info_by_name(self, field_name):
        """
        Get the field information for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            dict: The field information.

        Raises:
            ValueError: If the field name is not found.
        """
        field_info = next(
            (
                f
                for f in self.tracked_fields_info
                if f["name"] == field_name and not f["custom"]
            ),
            None,
        )
        if field_info == None:
            raise ValueError(f"Could not find field with name '{field_name}'")
        return field_info

    def field_schema_by_id(self, field_id):
        """
        Get the field schema for a given field ID.

        Args:
            field_id (str): The ID of the field.

        Returns:
            dict: The field schema.
        """
        field_info = self.field_info_by_id(field_id)
        return field_info["schema"]

    def record_field(self, field_name):
        """
        Get the record field tuple for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            tuple: The record field tuple.
        """
        return ("Record", field_name)

    def change_field(self, field_name):
        """
        Get the change field tuple for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            tuple: The change field tuple.
        """
        return ("Change", field_name)

    def tracked_field(self, field_name):
        """
        Get the tracked field tuple for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            tuple: The tracked field tuple.
        """
        return ("Tracked", field_name)
