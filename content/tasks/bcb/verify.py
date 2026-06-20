import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def task_func(product_dict, product_keys):
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
        empty = pd.DataFrame(
            columns=[
                "Product",
                "Quantity",
                "Price",
                "Profit",
                "Average Price",
                "Average Profit",
            ]
        )
        return empty, None

    df = pd.DataFrame(rows)
    avg_price = float(np.mean(df["Price"]))
    avg_profit = float(np.mean(df["Profit"]))
    df["Average Price"] = avg_price
    df["Average Profit"] = avg_profit

    _, ax = plt.subplots()
    ax.bar(df["Product"].astype(str), df["Profit"])
    ax.set_xlabel("Product")
    ax.set_ylabel("Profit")
    ax.set_title("Profit by Product")
    return df, ax


if __name__ == "__main__":
    product_dict = {
        "Widget": {"quantity": 10, "price": 5.0, "profit": 20.0},
        "Gadget": {"quantity": 3, "price": 12.0, "profit": 9.0},
    }
    df, ax = task_func(product_dict, ["Widget", "Gadget", "Missing"])
    print(df.to_string(index=False))
    print("avg_price", df["Average Price"].iloc[0])
    print("avg_profit", df["Average Profit"].iloc[0])
    print("axes_type", type(ax).__name__)
