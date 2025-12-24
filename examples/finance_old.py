"""
Example Finance class demonstrating the problematic approach of vertically 
concatenating layers to simulate a 3-dimensional data structure.

This approach has typing issues because different "layers" (Amount, Currency, 
Category) need to share the same column dtypes when vertically concatenated.
"""

import pandas as pd
import numpy as np


class FinanceOld:
    """Finance class using the old approach with vertical concatenation."""

    def balances(self):
        """
        Generate balance data with Account and Date as the first two dimensions,
        and Amount, Currency, Category as the third dimension (layers).
        
        The problem: We create separate DataFrames for each layer and vertically
        concatenate them, which causes typing issues.
        """
        # Define accounts and dates
        accounts = ["Account A", "Account B", "Account C"]
        dates = pd.date_range("2024-01-01", periods=3, freq="MS")
        
        # Create a base index with Account and Date
        index = pd.MultiIndex.from_product(
            [accounts, dates], names=["Account", "Date"]
        )
        
        # Create the Amount layer
        amount_layer = pd.DataFrame(
            {
                "Account": [acc for acc in accounts for _ in dates],
                "Date": [date for _ in accounts for date in dates],
                "Layer": "Amount",
                "Value": [1000.0, 1500.0, 2000.0, 500.0, 750.0, 1000.0, 2500.0, 3000.0, 3500.0]
            }
        )
        
        # Create the Currency layer
        currency_layer = pd.DataFrame(
            {
                "Account": [acc for acc in accounts for _ in dates],
                "Date": [date for _ in accounts for date in dates],
                "Layer": "Currency",
                "Value": ["USD", "USD", "USD", "EUR", "EUR", "EUR", "GBP", "GBP", "GBP"]
            }
        )
        
        # Create the Category layer
        category_layer = pd.DataFrame(
            {
                "Account": [acc for acc in accounts for _ in dates],
                "Date": [date for _ in accounts for date in dates],
                "Layer": "Category",
                "Value": ["Revenue", "Revenue", "Revenue", "Expense", "Expense", "Expense", "Revenue", "Revenue", "Revenue"]
            }
        )
        
        # Vertically concatenate all layers - THIS IS THE PROBLEM
        # All values must be the same type (object) even though amounts should be float
        balances_df = pd.concat([amount_layer, currency_layer, category_layer], ignore_index=True)
        
        # Try to set proper types - but this is problematic
        # We can't properly type the "Value" column because it contains mixed types
        print("DataFrame dtypes (all values are 'object' type):")
        print(balances_df.dtypes)
        print("\nSample data:")
        print(balances_df.head(12))
        
        return balances_df


if __name__ == "__main__":
    finance = FinanceOld()
    df = finance.balances()
