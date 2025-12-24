# Comparison: Vertical Concatenation vs. Proper DataFrame Structure

## Problem: Simulating 3-Dimensional Data

You have data with three dimensions:
1. **Account** (e.g., "Account A", "Account B", "Account C")
2. **Date** (e.g., monthly timestamps)
3. **Attributes** (e.g., Amount, Currency, Category)

## ❌ Bad Approach: Vertical Concatenation

### Code

```python
# Create separate DataFrames for each "layer"
amount_layer = pd.DataFrame({
    "Account": ["Account A", "Account A", ...],
    "Date": ["2024-01-01", "2024-02-01", ...],
    "Layer": "Amount",
    "Value": [1000.0, 1500.0, ...]  # floats
})

currency_layer = pd.DataFrame({
    "Account": ["Account A", "Account A", ...],
    "Date": ["2024-01-01", "2024-02-01", ...],
    "Layer": "Currency", 
    "Value": ["USD", "EUR", ...]  # strings
})

# Concatenate vertically
df = pd.concat([amount_layer, currency_layer, category_layer])
```

### Result

| Account   | Date       | Layer    | Value   |
|-----------|------------|----------|---------|
| Account A | 2024-01-01 | Amount   | 1000.0  |
| Account A | 2024-02-01 | Amount   | 1500.0  |
| Account A | 2024-01-01 | Currency | USD     |
| Account A | 2024-02-01 | Currency | USD     |
| Account A | 2024-01-01 | Category | Revenue |

### Problems

1. **Type issues**: The "Value" column contains mixed types (floats, strings) so pandas stores everything as `object` dtype
2. **No type safety**: Can't do numeric operations on amounts: `df[df["Layer"] == "Amount"]["Value"].mean()` fails or gives wrong results
3. **Inefficient queries**: To get all data for one Account/Date requires filtering: `df[(df["Account"] == "A") & (df["Date"] == "2024-01-01")]`
4. **Redundant data**: Account and Date are repeated for every layer
5. **Hard to maintain**: Adding new attributes requires creating and concatenating another layer

## ✅ Good Approach 1: Flat Columns with MultiIndex

### Code

```python
# Create MultiIndex for rows (Account, Date)
index = pd.MultiIndex.from_product(
    [accounts, dates], 
    names=["Account", "Date"]
)

# Each attribute gets its own properly-typed column
df = pd.DataFrame({
    "Amount": [1000.0, 1500.0, ...],      # float64
    "Currency": ["USD", "EUR", ...],      # object
    "Category": ["Revenue", "Expense", ...] # object
}, index=index)
```

### Result

| Account   | Date       | Amount | Currency | Category |
|-----------|------------|--------|----------|----------|
| Account A | 2024-01-01 | 1000.0 | USD      | Revenue  |
| Account A | 2024-02-01 | 1500.0 | USD      | Revenue  |
| Account B | 2024-01-01 | 500.0  | EUR      | Expense  |

### Benefits

1. ✅ **Proper typing**: Each column has the correct dtype (float64, object, etc.)
2. ✅ **Type-safe operations**: `df["Amount"].mean()` works correctly
3. ✅ **Efficient access**: `df.loc[("Account A", "2024-01-01")]` returns all attributes
4. ✅ **No redundancy**: Account and Date stored once per row
5. ✅ **Easy to extend**: Just add new columns
6. ✅ **Standard pandas**: Uses the library as intended

### Example Queries

```python
# Get all data for Account A
df.loc["Account A"]

# Get specific value
df.loc[("Account B", "2024-02-01"), "Amount"]  # 750.0

# Filter by amount
df[df["Amount"] > 1000]

# Compute statistics
df.groupby("Account")["Amount"].sum()
```

## ✅ Good Approach 2: Multi-Level Column Index

Use this when you want to logically group attributes.

### Code

```python
# Create multi-level columns: (Group, Attribute)
columns = pd.MultiIndex.from_tuples([
    ("Balance", "Amount"),
    ("Balance", "Currency"),
    ("Metadata", "Category"),
    ("Metadata", "LastUpdated")
])

df = pd.DataFrame(data, index=index, columns=columns)
```

### Result

| Account   | Date       | Balance |         | Metadata |            |
|           |            | Amount  | Currency| Category | LastUpdated|
|-----------|------------|---------|---------|----------|------------|
| Account A | 2024-01-01 | 1000.0  | USD     | Revenue  | 2024-01-15 |
| Account A | 2024-02-01 | 1500.0  | USD     | Revenue  | 2024-02-15 |

### Benefits

Same as Approach 1, plus:
- **Logical grouping**: Access related columns together: `df["Balance"]`
- **Namespace separation**: Clear separation between different types of data
- **Selective operations**: `df["Balance"].sum()` operates only on balance columns

### When to Use This

- When attributes naturally fall into groups (Balance, Metadata, etc.)
- When groups have different lifecycles or purposes
- When you want to perform operations on entire groups

## Summary

| Aspect | Vertical Concat | Flat Columns | Multi-Level Columns |
|--------|----------------|--------------|---------------------|
| Type safety | ❌ | ✅ | ✅ |
| Performance | ❌ | ✅ | ✅ |
| Memory usage | ❌ | ✅ | ✅ |
| Query simplicity | ❌ | ✅ | ✅ |
| Logical grouping | ❌ | ⚠️ | ✅ |
| Complexity | Low | Low | Medium |

## Recommendation

**For most cases, use Approach 1 (Flat Columns with MultiIndex).**

It's simple, efficient, and leverages pandas' built-in capabilities. Only use multi-level columns if you have a clear need for logical grouping.

**Never use vertical concatenation** to simulate additional dimensions - it's inefficient and causes type problems.
