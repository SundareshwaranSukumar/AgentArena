import matplotlib
matplotlib.use("Agg")
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


if __name__ == "__main__":
    sample = {
        "A": {"quantity": 10, "price": 5.0, "profit": 20.0},
        "B": {"quantity": 5, "price": 8.0, "profit": 15.0},
        "C": {"quantity": 3, "price": 12.0, "profit": 9.0},
    }
    df, ax = task_func(sample, ["A", "B", "C"])
    assert list(df.columns) == [
        "Product",
        "Quantity",
        "Price",
        "Profit",
        "Average Price",
        "Average Profit",
    ]
    assert len(df) == 3
    assert df["Average Price"].iloc[0] == df["Price"].mean()
    assert df["Average Profit"].iloc[0] == df["Profit"].mean()
    assert ax is not None
    empty_df, empty_ax = task_func(sample, [])
    assert empty_ax is None
    print("ok")
