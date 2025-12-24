# Finance Examples: 3-Dimensional Data Structure

This directory contains examples demonstrating different approaches to building a 3-dimensional data structure in pandas, where:
- First dimension: **Account** 
- Second dimension: **Date**
- Third dimension: **Attributes** (Amount, Currency, Category, etc.)

## The Problem

The original approach (`finance_old.py`) tries to simulate the 3D structure by vertically concatenating "layers":

```python
# Create separate DataFrames for each attribute layer
amount_layer = DataFrame with "Amount" values
currency_layer = DataFrame with "Currency" values  
category_layer = DataFrame with "Category" values

# Concatenate vertically - PROBLEMATIC!
df = pd.concat([amount_layer, currency_layer, category_layer])
```

**Issues with this approach:**
1. **Type problems**: All values end up as `object` dtype because pandas can't properly type a column containing both floats (amounts) and strings (currencies/categories)
2. **Inefficient**: Requires multiple lookups and filtering to access data
3. **Hard to query**: Difficult to select all attributes for a specific Account/Date combination
4. **Memory inefficient**: Stores redundant Account/Date information for each layer

## The Solution

### Approach 1: Simple Flat Columns (Recommended)

Use Account and Date as a **MultiIndex for rows**, and have each attribute as its own **properly-typed column**:

```python
# Create MultiIndex for rows
index = pd.MultiIndex.from_product([accounts, dates], names=["Account", "Date"])

# Create DataFrame with properly typed columns
df = pd.DataFrame({
    "Amount": [1000.0, 1500.0, ...],      # float64
    "Currency": ["USD", "EUR", ...],      # object (string)
    "Category": ["Revenue", "Expense", ...] # object (string)
}, index=index)
```

**Benefits:**
- ✅ Each column has the correct dtype
- ✅ Easy to access: `df.loc[("Account A", "2024-01-01"), "Amount"]`
- ✅ Efficient filtering: `df[df["Amount"] > 1000]`
- ✅ Clear and maintainable

### Approach 2: Multi-Level Column Index

If you need to logically group attributes, use a **MultiIndex for columns**:

```python
# Create multi-level columns
columns = pd.MultiIndex.from_tuples([
    ("Balance", "Amount"),
    ("Balance", "Currency"),
    ("Metadata", "Category"),
    ("Metadata", "LastUpdated")
])

df = pd.DataFrame(data, index=index, columns=columns)
```

**When to use:**
- When you have logical groups of attributes (e.g., Balance vs Metadata)
- When you want to access entire groups: `df["Balance"]`
- When the groups have different purposes or life cycles

## Running the Examples

```bash
# See the problematic old approach
python examples/finance_old.py

# See the improved approaches
python examples/finance_improved.py
```

## Key Takeaway

**Don't vertically concatenate DataFrames to simulate additional dimensions.**

Instead:
1. Use **row MultiIndex** for the first N dimensions (Account, Date, etc.)
2. Use **columns** for attributes, each with its proper dtype
3. Optionally use **column MultiIndex** if you need logical grouping

This is the same pattern used throughout pandas and is what the library is designed for.
