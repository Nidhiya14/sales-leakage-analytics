from pathlib import Path
import numpy as np
import pandas as pd

INPUT = Path("data/scraped_products.csv")
OUTPUT = Path("data/simulated_sales.csv")

def main():
    if not INPUT.exists():
        raise FileNotFoundError("Run python src/scrape_products.py first, or place scraped_products.csv in data/.")
    products = pd.read_csv(INPUT)
    rng = np.random.default_rng(42)
    n = len(products)
    df = products.copy()
    df["region"] = rng.choice(["North", "South", "East", "West"], size=n)
    df["units_sold"] = rng.integers(5, 120, size=n)
    df["unit_cost_gbp"] = (df["price_gbp"] * rng.uniform(0.45, 0.82, size=n)).round(2)
    df["discount_pct"] = rng.choice([0, 5, 10, 15, 20, 25, 35, 50], size=n,
                                    p=[.18, .12, .18, .16, .14, .10, .07, .05])
    if n >= 5:
        df.loc[df.index[0], "discount_pct"] = 70
        df.loc[df.index[1], "unit_cost_gbp"] = df.loc[df.index[1], "price_gbp"] * 1.08
    df["selling_price_gbp"] = (df["price_gbp"] * (1 - df["discount_pct"] / 100)).round(2)
    df["revenue_gbp"] = (df["selling_price_gbp"] * df["units_sold"]).round(2)
    df["profit_gbp"] = ((df["selling_price_gbp"] - df["unit_cost_gbp"]) * df["units_sold"]).round(2)
    df["data_note"] = "simulated sales fields; not actual website sales"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)
    print(f"Saved {len(df)} simulated rows to {OUTPUT}")
    print("Reminder: sales-related fields are simulated, not actual website sales.")

if __name__ == "__main__":
    main()
