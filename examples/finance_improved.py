"""
Improved Finance class using a proper multi-level column index approach
to simulate a 3-dimensional data structure.

This approach properly types each attribute (Amount, Currency, Category)
in its own column with the appropriate dtype.
"""

import pandas as pd
import numpy as np


class Finance:
    """Finance class using an improved approach with multi-level columns."""

    def balances(self):
        """
        Generate balance data with Account and Date as the row index (first two dimensions),
        and Amount, Currency, Category as separate columns (third dimension).
        
        This is a much better approach: Instead of vertically concatenating layers,
        we use properly typed columns with each attribute having its own column.
        """
        # Define accounts and dates
        accounts = ["Account A", "Account B", "Account C"]
        dates = pd.date_range("2024-01-01", periods=3, freq="MS")
        
        # Create a MultiIndex for rows with Account and Date
        index = pd.MultiIndex.from_product(
            [accounts, dates], names=["Account", "Date"]
        )
        
        # Create the DataFrame with properly typed columns
        balances_df = pd.DataFrame(
            {
                "Amount": [
                    1000.0, 1500.0, 2000.0,  # Account A
                    500.0, 750.0, 1000.0,     # Account B
                    2500.0, 3000.0, 3500.0    # Account C
                ],
                "Currency": [
                    "USD", "USD", "USD",       # Account A
                    "EUR", "EUR", "EUR",       # Account B
                    "GBP", "GBP", "GBP"        # Account C
                ],
                "Category": [
                    "Revenue", "Revenue", "Revenue",  # Account A
                    "Expense", "Expense", "Expense",  # Account B
                    "Revenue", "Revenue", "Revenue"   # Account C
                ]
            },
            index=index
        )
        
        # Each column has the proper type
        print("DataFrame dtypes (properly typed):")
        print(balances_df.dtypes)
        print("\nSample data:")
        print(balances_df)
        print("\nAccess data by Account and Date:")
        print(balances_df.loc["Account A"])
        print("\nAccess specific value:")
        print(f"Amount for Account B on 2024-02-01: {balances_df.loc[('Account B', '2024-02-01'), 'Amount']}")
        
        return balances_df


class FinanceWithMultiLevelColumns:
    """
    Alternative approach using multi-level column index if you need to group
    attributes logically (e.g., separate Balance info from Metadata).
    """

    def balances(self):
        """
        Generate balance data using multi-level column index for logical grouping.
        
        This approach is useful when you have multiple groups of related attributes.
        """
        # Define accounts and dates
        accounts = ["Account A", "Account B", "Account C"]
        dates = pd.date_range("2024-01-01", periods=3, freq="MS")
        
        # Create a MultiIndex for rows with Account and Date
        index = pd.MultiIndex.from_product(
            [accounts, dates], names=["Account", "Date"]
        )
        
        # Create multi-level columns: (Group, Attribute)
        columns = pd.MultiIndex.from_tuples([
            ("Balance", "Amount"),
            ("Balance", "Currency"),
            ("Metadata", "Category"),
            ("Metadata", "LastUpdated")
        ])
        
        # Create the DataFrame
        balances_df = pd.DataFrame(
            {
                ("Balance", "Amount"): [
                    1000.0, 1500.0, 2000.0,  # Account A
                    500.0, 750.0, 1000.0,     # Account B
                    2500.0, 3000.0, 3500.0    # Account C
                ],
                ("Balance", "Currency"): [
                    "USD", "USD", "USD",       # Account A
                    "EUR", "EUR", "EUR",       # Account B
                    "GBP", "GBP", "GBP"        # Account C
                ],
                ("Metadata", "Category"): [
                    "Revenue", "Revenue", "Revenue",  # Account A
                    "Expense", "Expense", "Expense",  # Account B
                    "Revenue", "Revenue", "Revenue"   # Account C
                ],
                ("Metadata", "LastUpdated"): [
                    "2024-01-15", "2024-02-15", "2024-03-15",  # Account A
                    "2024-01-20", "2024-02-20", "2024-03-20",  # Account B
                    "2024-01-25", "2024-02-25", "2024-03-25"   # Account C
                ]
            },
            index=index
        )
        
        # Proper typing for each column
        balances_df[("Metadata", "LastUpdated")] = pd.to_datetime(
            balances_df[("Metadata", "LastUpdated")]
        )
        
        print("DataFrame dtypes (with multi-level columns):")
        print(balances_df.dtypes)
        print("\nSample data:")
        print(balances_df)
        print("\nAccess Balance group:")
        print(balances_df["Balance"])
        print("\nAccess specific column:")
        print(balances_df[("Balance", "Amount")])
        
        return balances_df


if __name__ == "__main__":
    print("=" * 60)
    print("Simple approach with flat columns (RECOMMENDED):")
    print("=" * 60)
    finance1 = Finance()
    df1 = finance1.balances()
    
    print("\n" + "=" * 60)
    print("Multi-level column approach:")
    print("=" * 60)
    finance2 = FinanceWithMultiLevelColumns()
    df2 = finance2.balances()
