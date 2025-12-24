"""
Performance and type comparison between different approaches.
"""

import pandas as pd
import numpy as np
import time


def create_vertical_concat_df(n_accounts: int = 100, n_dates: int = 12) -> pd.DataFrame:
    """Create DataFrame using vertical concatenation (bad approach)."""
    accounts = [f"Account {i}" for i in range(n_accounts)]
    dates = pd.date_range("2024-01-01", periods=n_dates, freq="MS")
    
    # Create layers
    layers = []
    for layer_name, values in [
        ("Amount", np.random.uniform(100, 10000, n_accounts * n_dates)),
        ("Currency", np.random.choice(["USD", "EUR", "GBP"], n_accounts * n_dates)),
        ("Category", np.random.choice(["Revenue", "Expense"], n_accounts * n_dates))
    ]:
        layer_df = pd.DataFrame({
            "Account": [acc for acc in accounts for _ in dates],
            "Date": [date for _ in accounts for date in dates],
            "Layer": layer_name,
            "Value": values
        })
        layers.append(layer_df)
    
    return pd.concat(layers, ignore_index=True)


def create_flat_columns_df(n_accounts: int = 100, n_dates: int = 12) -> pd.DataFrame:
    """Create DataFrame using flat columns (good approach)."""
    accounts = [f"Account {i}" for i in range(n_accounts)]
    dates = pd.date_range("2024-01-01", periods=n_dates, freq="MS")
    
    index = pd.MultiIndex.from_product([accounts, dates], names=["Account", "Date"])
    
    return pd.DataFrame({
        "Amount": np.random.uniform(100, 10000, n_accounts * n_dates),
        "Currency": np.random.choice(["USD", "EUR", "GBP"], n_accounts * n_dates),
        "Category": np.random.choice(["Revenue", "Expense"], n_accounts * n_dates)
    }, index=index)


def benchmark_access(df_concat: pd.DataFrame, df_flat: pd.DataFrame) -> None:
    """Benchmark data access performance."""
    print("\n" + "=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)
    
    # Vertical concat: Get all data for one account/date
    start = time.time()
    for _ in range(100):
        result = df_concat[
            (df_concat["Account"] == "Account 50") & 
            (df_concat["Date"] == pd.Timestamp("2024-06-01"))
        ]
    concat_time = time.time() - start
    
    # Flat columns: Get all data for one account/date
    start = time.time()
    for _ in range(100):
        result = df_flat.loc[("Account 50", pd.Timestamp("2024-06-01"))]
    flat_time = time.time() - start
    
    print(f"Access specific Account/Date (100 iterations):")
    print(f"  Vertical concatenation: {concat_time:.4f}s")
    print(f"  Flat columns:          {flat_time:.4f}s")
    print(f"  Speedup:               {concat_time/flat_time:.1f}x faster")


def demonstrate_type_issues() -> None:
    """Demonstrate typing problems with vertical concatenation."""
    print("\n" + "=" * 70)
    print("TYPE SAFETY COMPARISON")
    print("=" * 70)
    
    # Create small examples
    df_concat = create_vertical_concat_df(n_accounts=3, n_dates=3)
    df_flat = create_flat_columns_df(n_accounts=3, n_dates=3)
    
    print("\n1. Vertical Concatenation DataFrame dtypes:")
    print(df_concat.dtypes)
    print("\nNote: 'Value' column is 'object' type (stores everything as strings)")
    
    print("\n2. Flat Columns DataFrame dtypes:")
    print(df_flat.dtypes)
    print("\nNote: Each column has the correct dtype")
    
    # Try to compute mean
    print("\n3. Computing mean of amounts:")
    
    print("\n   Vertical concatenation (requires filtering and conversion):")
    try:
        amounts = df_concat[df_concat["Layer"] == "Amount"]["Value"]
        print(f"   Type of amounts: {amounts.dtype}")
        # Need to convert to numeric
        amounts_numeric = pd.to_numeric(amounts)
        print(f"   Mean after conversion: {amounts_numeric.mean():.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n   Flat columns (direct):")
    try:
        print(f"   Type of Amount column: {df_flat['Amount'].dtype}")
        print(f"   Mean: {df_flat['Amount'].mean():.2f}")
    except Exception as e:
        print(f"   Error: {e}")


def demonstrate_memory_usage() -> None:
    """Demonstrate memory usage differences."""
    print("\n" + "=" * 70)
    print("MEMORY USAGE COMPARISON")
    print("=" * 70)
    
    df_concat = create_vertical_concat_df(n_accounts=100, n_dates=12)
    df_flat = create_flat_columns_df(n_accounts=100, n_dates=12)
    
    concat_memory = df_concat.memory_usage(deep=True).sum() / 1024  # KB
    flat_memory = df_flat.memory_usage(deep=True).sum() / 1024  # KB
    
    print(f"\nDataFrame with 100 accounts × 12 dates × 3 attributes:")
    print(f"  Vertical concatenation: {concat_memory:.2f} KB")
    print(f"  Flat columns:          {flat_memory:.2f} KB")
    print(f"  Savings:               {(1 - flat_memory/concat_memory)*100:.1f}%")
    
    print(f"\nRows in each DataFrame:")
    print(f"  Vertical concatenation: {len(df_concat):,} rows")
    print(f"  Flat columns:          {len(df_flat):,} rows")


def demonstrate_query_simplicity() -> None:
    """Demonstrate query simplicity."""
    print("\n" + "=" * 70)
    print("QUERY SIMPLICITY COMPARISON")
    print("=" * 70)
    
    df_concat = create_vertical_concat_df(n_accounts=5, n_dates=3)
    df_flat = create_flat_columns_df(n_accounts=5, n_dates=3)
    
    print("\nTask: Get all attributes for Account 2 on 2024-02-01")
    
    print("\nVertical concatenation (complex):")
    code = '''df_concat[
    (df_concat["Account"] == "Account 2") & 
    (df_concat["Date"] == pd.Timestamp("2024-02-01"))
][["Layer", "Value"]]'''
    print(f"  Code: {code}")
    result = df_concat[
        (df_concat["Account"] == "Account 2") & 
        (df_concat["Date"] == pd.Timestamp("2024-02-01"))
    ][["Layer", "Value"]]
    print(f"  Result:\n{result}")
    
    print("\nFlat columns (simple):")
    code = 'df_flat.loc[("Account 2", pd.Timestamp("2024-02-01"))]'
    print(f"  Code: {code}")
    result = df_flat.loc[("Account 2", pd.Timestamp("2024-02-01"))]
    print(f"  Result:\n{result}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPARISON: Vertical Concatenation vs. Flat Columns")
    print("=" * 70)
    
    demonstrate_type_issues()
    demonstrate_memory_usage()
    benchmark_access(
        create_vertical_concat_df(n_accounts=100, n_dates=12),
        create_flat_columns_df(n_accounts=100, n_dates=12)
    )
    demonstrate_query_simplicity()
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
The flat columns approach with MultiIndex is:
  ✅ Faster for data access
  ✅ More memory efficient
  ✅ Type-safe (proper dtypes)
  ✅ Simpler to query
  ✅ Easier to maintain

Avoid vertical concatenation for simulating dimensions!
""")
