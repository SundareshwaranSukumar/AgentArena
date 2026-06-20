**Answer:**

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def task_func(product_dict, product_keys):
    cols = ["Product", "Quantity", "Price", "Profit", "Average Price", "Average Profit"]
    if not product_keys:
        return pd.DataFrame(columns=cols), None

    rows = []
    for key in product_keys:
        if key not in product_dict:
            continue
        item = product_dict[key]
        rows.append(
            {
                "Product": key,
                "Quantity": item["quantity"],
                "Price": item["price"],
                "Profit": item["profit"],
            }
        )

    if not rows:
        return pd.DataFrame(columns=cols), None

    df = pd.DataFrame(rows)
    avg_price = df["Price"].mean()
    avg_profit = df["Profit"].mean()
    df["Average Price"] = avg_price
    df["Average Profit"] = avg_profit

    fig, ax = plt.subplots()
    ax.bar(df["Product"], df["Profit"])
    ax.set_xlabel("Product")
    ax.set_ylabel("Profit")
    ax.set_title("Profit by Product")

    return df, ax
```

**Solution:**

1. Filter `product_keys` against `product_dict`; build rows with Product/Quantity/Price/Profit.
2. Compute mean price and profit across included products; broadcast as `Average Price` / `Average Profit` columns.
3. Plot bar chart of profit per product; return `(DataFrame, Axes)`.
4. Empty `product_keys` or no matches → empty DataFrame with required columns and `None` axes.

**Verification:**

Sample dict with 3 products yields DataFrame shape `(3, 6)`, constant average columns matching `Price.mean()` and `Profit.mean()`, and non-null bar-chart Axes. Empty keys returns `(empty DataFrame, None)`.
