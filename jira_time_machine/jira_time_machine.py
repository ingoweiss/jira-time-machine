import pandas as pd
from tqdm import tqdm
import numpy as np
import logging
from typing import Any, List, Dict, Tuple


class JiraTimeMachine:

    BLOCKER: str = "[[BLOCKER]]"
    BLANK: str = "[[BLANK]]"

    def __init__(self, jira_instance: Any):
        """
        Initialize the JiraTimeMachine instance.

        Args:
            jira_instance: An instance of the JIRA class.
        """
        self.jira = jira_instance
        self.logger = logging.getLogger(__name__)

    def history(self, jql_query: str, tracked_fields: List[str]) -> pd.DataFrame:
        """
        Fetch the full change history of Jira issues for specified fields.

        Args:
            jql_query (str): JQL query to select issues.
            tracked_fields (list): List of Jira fields to track changes for.

        Returns:
            pd.DataFrame: A DataFrame with issue states over time.
        """
        self.tracked_fields: List[str] = tracked_fields
        self.tracked_fields_info: List[Dict] = [
            field for field in self.jira.fields() if field["name"] in tracked_fields
        ]
        self.tracked_field_ids: List[str] = [f["id"] for f in self.tracked_fields_info]
        self.issues: List = self.jira.search_issues(
            jql_query, expand="changelog", maxResults=False
        )
        record_dicts: List[Dict[Tuple[str, str], Any]] = []
        headers: List[Tuple[str, str]] = (
            [self.record_field(f) for f in ["Key", "Type", "Date", "Author"]]
            + [self.change_field(f) for f in ["ID", "Item", "Field", "From", "To"]]
            + [self.tracked_field(f) for f in tracked_fields]
        )
        record_template: Dict[Tuple[str, str], Any] = {k: np.nan for k in headers}

        for issue in tqdm(self.issues, desc="Processing issues"):
            issue_id: str = issue.key
            created_at: pd.Timestamp = pd.to_datetime(issue.fields.created)
            reporter: str = getattr(issue.fields.reporter, "displayName", "Unknown")
            changelog: List[Any] = issue.changelog.histories

            # (1) Add the issue's initial state:
            # Tracked fields will be initially empty - we will reverse engineer them from the changelog later
            initial_record: Dict[Tuple[str, str], Any] = record_template.copy()
            initial_record[self.record_field("Key")] = issue_id
            initial_record[self.record_field("Type")] = "initial"
            initial_record[self.record_field("Date")] = created_at
            initial_record[self.record_field("Author")] = reporter

            record_dicts.append(initial_record)

            # (2) Add changes from issue's changelog:
            for change in changelog:
                change_date = pd.to_datetime(change.created)
                relevant_items = [
                    i for i in change.items if i.field in self.tracked_field_ids
                ]
                for item_index, item in enumerate(relevant_items, start=1):
                    change_record = record_template.copy()

                    change_record[self.record_field("Key")] = issue_id
                    change_record[self.record_field("Type")] = "change"
                    change_record[self.record_field("Date")] = change_date
                    change_record[self.record_field("Author")] = getattr(
                        change.author, "displayName", "Unknown"
                    )
                    change_record[self.change_field("ID")] = change.id
                    change_record[self.change_field("Item")] = item_index
                    change_record[self.change_field("Field")] = item.field
                    change_record[self.change_field("From")] = (
                        self.normalize_field_value_string(item.field, item.fromString)
                    )
                    change_record[self.change_field("To")] = (
                        self.normalize_field_value_string(item.field, item.toString)
                    )

                    record_dicts.append(change_record)

            # (3) Add the issue's current state which is only needed to reverse engineer the initial state:
            current_record = record_template.copy()
            current_record[self.record_field("Date")] = pd.Timestamp.utcnow()
            current_record[self.record_field("Key")] = issue_id
            current_record[self.record_field("Type")] = "current"
            current_record[self.record_field("Author")] = "System"
            for field in tracked_fields:
                field_id = self.field_id_by_name(field)
                field_value = getattr(
                    issue.fields, field_id, np.nan
                )  # TODO: Maybe no fallback to np.nan here?
                normalized_field_value = self.normalize_field_value(
                    field_id, field_value
                )
                current_record[self.tracked_field(field)] = normalized_field_value

            record_dicts.append(current_record)

        history: pd.DataFrame = pd.DataFrame(record_dicts)
        history.columns = pd.MultiIndex.from_tuples(headers, names=["Section", "Field"])

        # Type columns appropriately
        history[self.record_field("Key")] = history[self.record_field("Key")].astype(
            str
        )
        history[self.record_field("Type")] = history[self.record_field("Type")].astype(
            str
        )
        history[self.record_field("Date")] = pd.to_datetime(
            history[self.record_field("Date")], utc=True
        )
        history[self.record_field("Author")] = history[
            self.record_field("Author")
        ].astype(str)
        history[self.change_field("ID")] = history[self.change_field("ID")].astype(
            "Int64"
        )
        history[self.change_field("Item")] = history[self.change_field("Item")].astype(
            "Int64"
        )
        history[self.change_field("Field")] = history[
            self.change_field("Field")
        ].astype(str)
        # history[self.change_field("From")] = history[self.change_field("From")].astype(str)
        # history[self.change_field("To")] = history[self.change_field("To")].astype(str)
        # TODO: Possibly leave Change From/To as string and normalize while copying to Tracked

        history.sort_values(
            # Pandas type annotations for the 'by' parameter are incorrect, calling for string or
            # list of strings, but MultiIndex requires a list of tuples instead. Hence the type: ignore
            by=[self.record_field("Key"), self.record_field("Date"), self.change_field("Item")],  # type: ignore
            inplace=True,
        )

        # (4) Reverse engineer tracked field states from the changelog:
        # First, forward fill from the change 'to' values:
        for field in tracked_fields:
            field_id = self.field_id_by_name(field)
            history.loc[
                history[self.change_field("Field")] == field_id,
                self.tracked_field(field),
            ] = history[self.change_field("To")]

        # Temporariliy replace initial 'NaN' values so that backfilled values do not
        # spill over into the next issue
        history.loc[history[self.record_field("Type")] == "initial", "Tracked"] = (
            JiraTimeMachine.BLOCKER
        )
        history["Tracked"] = history["Tracked"].ffill()
        history["Tracked"] = history["Tracked"].replace(JiraTimeMachine.BLOCKER, np.nan)

        # Second, backward fill from the change 'from' values:
        for field in tracked_fields:
            field_id = self.field_id_by_name(field)
            history.loc[
                history[self.change_field("Field")] == field_id,
                self.tracked_field(field),
            ] = history[self.change_field("From")]
        history["Tracked"] = history["Tracked"].bfill()

        # Third, restore the change 'to' values:
        for field in tracked_fields:
            field_id = self.field_id_by_name(field)
            history.loc[
                history[self.change_field("Field")] == field_id,
                self.tracked_field(field),
            ] = history[self.change_field("To")]

        # Finally, restore marked blank values to 'None'
        history["Tracked"] = history["Tracked"].replace(JiraTimeMachine.BLANK, None)

        # (5) Remove the 'current' records. They are redundant since the last 'change' record or
        # the 'initial' record (if there are no 'change' records) already has the current state
        # TODO: Might want to sanity check last change state == current state before removing
        history = history[history[self.record_field("Type")] != "current"]

        history.sort_values([("Record", "Date"), ("Change", "Item")], inplace=True)  # type: ignore
        return history

    def snapshot(self, history: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
        """
        Get the snapshot of the project at a specific timestamp.

        Args:
            history (pd.DataFrame): The history DataFrame.
            dt (pd.Timestamp): The timestamp for the snapshot.

        Returns:
            pd.DataFrame: A snapshot of the project at the given timestamp.
        """
        snapshot = (
            history[history[self.record_field("Date")] <= dt]
            .sort_values(by=[self.record_field("Date"), self.change_field("Item")]) # type: ignore
            .groupby(self.record_field("Key"))
            .tail(1)
            .set_index(self.record_field("Key"))[["Tracked"]]
        )
        snapshot.columns = snapshot.columns.droplevel("Section")
        snapshot.index.name = "Key"
        snapshot.sort_index(inplace=True)
        return snapshot

    def field_id_by_name(self, field_name: str) -> str:
        """
        Get the field ID for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            str: The ID of the field.
        """
        field_info = self.field_info_by_name(field_name)
        return field_info["id"]

    def normalize_field_value(self, field_id: str, field_value: Any) -> Any:
        """
        Normalize a field value according to its schema.

        Args:
            field_id (str): The ID of the field.
            field_value: The raw field value.

        Returns:
            The normalized field value.
        """
        # String
        # Status, Priority, Recolution: Name
        # User: DisplayName
        # Array: [String], [Version]

        field_info: Dict = self.field_info_by_id(field_id)
        field_schema: Dict = field_info["schema"]
        field_type: str = field_schema["type"]

        if field_value is None:
            # Mark blank values so that they are not overridden by ffill/bfill
            # operations. We are going to restore these to 'None' later
            return JiraTimeMachine.BLANK
        elif field_type == "string":
            return field_value
        elif field_type in ["status", "priority", "resolution"]:
            return field_value.name
        elif field_schema["type"] == "user":
            return field_value.displayName
        elif field_schema["type"] == "array":
            item_type = field_schema["items"]
            if item_type == "version":
                return [v["name"] for v in field_value]
            elif item_type == "string":
                return [v for v in field_value]
            else:
                self.logger.warning(f"Unsupported array field item type '{item_type}'")
                return field_value
        else:
            self.logger.warning(f"Unsupported field type '{field_type}'")
            return field_value

    def normalize_field_value_string(self, field_id: str, field_value: Any) -> Any:
        """
        Normalize a field value string according to its schema.

        Args:
            field_id (str): The ID of the field.
            field_value (str): The raw field value string.

        Returns:
            The normalized field value.
        """
        field_info: Dict = self.field_info_by_id(field_id)
        field_schema: Dict = field_info["schema"]
        field_type: str = field_schema["type"]

        if field_schema["type"] == "array":
            item_type = field_schema["items"]
            if item_type in ["string", "version"]:
                return field_value.split()  # this will return [] for empty strings
            else:
                self.logger.warning(f"Unsupported array field item type '{item_type}'")
                return field_value
        elif field_type in ["string", "status", "priority", "resolution", "user"]:
            if field_value == "":
                # Mark blank values so that they are not overridden by ffill/bfill
                # operations. We are going to restore these to 'None' later
                return JiraTimeMachine.BLANK
            else:
                return field_value
        else:
            self.logger.warning(f"Unsupported field type '{field_type}'")
            return field_value

    def field_info_by_id(self, field_id: str) -> Dict:
        """
        Get the field information for a given field ID.

        Args:
            field_id (str): The ID of the field.

        Returns:
            dict: The field information.

        Raises:
            ValueError: If the field ID is not found.
        """
        field_info: Dict = next(
            (
                f
                for f in self.tracked_fields_info
                if f["id"] == field_id and not f["custom"]
            ),
            {},
        )
        if not field_info:
            raise ValueError(f"Could not find field with ID '{field_id}'")
        else:
            return field_info

    def field_info_by_name(self, field_name: str) -> Dict:
        """
        Get the field information for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            dict: The field information.

        Raises:
            ValueError: If the field name is not found.
        """
        field_info: Dict = next(
            (
                f
                for f in self.tracked_fields_info
                if f["name"] == field_name and not f["custom"]
            ),
            {},
        )
        if not field_info:
            raise ValueError(f"Could not find field with name '{field_name}'")
        else:
            return field_info

    def field_schema_by_id(self, field_id: str) -> Dict:
        """
        Get the field schema for a given field ID.

        Args:
            field_id (str): The ID of the field.

        Returns:
            dict: The field schema.
        """
        field_info: Dict = self.field_info_by_id(field_id)
        return field_info["schema"]

    def record_field(self, field_name: str) -> Tuple[str, str]:
        """
        Get the record field tuple for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            tuple: The record field tuple.
        """
        return ("Record", field_name)

    def change_field(self, field_name: str) -> Tuple[str, str]:
        """
        Get the change field tuple for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            tuple: The change field tuple.
        """
        return ("Change", field_name)

    def tracked_field(self, field_name: str) -> Tuple[str, str]:
        """
        Get the tracked field tuple for a given field name.

        Args:
            field_name (str): The name of the field.

        Returns:
            tuple: The tracked field tuple.
        """
        return ("Tracked", field_name)
