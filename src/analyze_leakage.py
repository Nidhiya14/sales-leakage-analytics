from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

INPUT = Path("data/simulated_sales.csv")
OUT = Path("output/leakage_results.csv")

def main():
    if not INPUT.exists():
        raise FileNotFoundError("Run python src/create_sales_dataset.py first.")
    df = pd.read_csv(INPUT)
    numeric = ["discount_pct", "profit_gbp", "revenue_gbp", "units_sold"]
    X = df[numeric].replace([np.inf, -np.inf], np.nan).fillna(0)
    z = (X["discount_pct"] - X["discount_pct"].mean()) / X["discount_pct"].std(ddof=0)
    df["discount_zscore"] = z.fillna(0).round(3)
    df["zscore_flag"] = (df["discount_zscore"].abs() >= 2).astype(int)
    scaled = StandardScaler().fit_transform(X)
    contamination = min(0.10, max(1 / len(df), 0.01)) if len(df) > 1 else 0.01
    model = IsolationForest(contamination=contamination, random_state=42)
    df["isolation_forest_flag"] = (model.fit_predict(scaled) == -1).astype(int)

    reasons = []
    for _, row in df.iterrows():
        r = []
        if row["discount_pct"] >= 30:
            r.append("high discount")
        if row["profit_gbp"] < 0:
            r.append("negative profit")
        if row["units_sold"] > 0 and row["profit_gbp"] / row["units_sold"] < 1:
            r.append("low profit per unit")
        if row["zscore_flag"]:
            r.append("unusual discount by Z-score")
        if row["isolation_forest_flag"]:
            r.append("multivariate anomaly")
        reasons.append("; ".join(r) if r else "no rule triggered")
    df["root_cause"] = reasons
    df["leakage_score"] = (
        (df["discount_pct"] / 70 * 35).clip(0, 35)
        + (df["profit_gbp"] < 0).astype(int) * 35
        + df["zscore_flag"] * 15
        + df["isolation_forest_flag"] * 15
    ).clip(0, 100).round(1)
    target_price = df["price_gbp"] * 0.85
    df["estimated_recovery_gbp"] = (((target_price - df["selling_price_gbp"]).clip(lower=0))
                                    * df["units_sold"]).round(2)
    df["priority"] = pd.cut(df["leakage_score"], bins=[-1, 24, 49, 74, 100],
                            labels=["Low", "Medium", "High", "Critical"])
    df = df.sort_values(["leakage_score", "estimated_recovery_gbp"], ascending=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    flagged = int(((df["zscore_flag"] == 1) | (df["isolation_forest_flag"] == 1)).sum())
    summary = (
        "SALES LEAKAGE DEMO SUMMARY\n"
        f"Rows analyzed: {len(df)}\n"
        f"Rows flagged by either anomaly method: {flagged}\n"
        f"Estimated recovery under illustrative 15% discount scenario: £{df['estimated_recovery_gbp'].sum():.2f}\n"
        "Sales-related fields and recovery values are illustrative simulated data.\n"
    )
    Path("output/summary.txt").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"Saved results to {OUT}")

if __name__ == "__main__":
    main()
