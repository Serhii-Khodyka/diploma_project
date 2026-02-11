import pandas as pd
import numpy as np

RAW = "data/raw_reviews.parquet"
OUT_AGG = "data/products_agg.parquet"

def dirichlet_smoothed_rating(counts_1to5: np.ndarray, alpha_1to5: np.ndarray) -> float:
    counts = counts_1to5.astype(float)
    alpha = alpha_1to5.astype(float)
    post = counts + alpha
    probs = post / post.sum()
    stars = np.arange(1, 6, dtype=float)
    return float((stars * probs).sum())

def main():
    df = pd.read_parquet(RAW)

    # counts per product per star
    pivot = (
        df.assign(cnt=1)
          .pivot_table(index="product_id", columns="rating", values="cnt", aggfunc="sum", fill_value=0)
    )

    # гарантуємо колонки 1..5
    for k in [1,2,3,4,5]:
        if k not in pivot.columns:
            pivot[k] = 0
    pivot = pivot[[1,2,3,4,5]].copy()

    # глобальний апріорі (емпіричний Байєс)
    global_counts = pivot.sum(axis=0).values.astype(float)  # [n1..n5]
    global_probs = global_counts / global_counts.sum()

    # сила апріорі: чим більше, тим сильніше тягне до середнього
    # для MVP можна 10..50. Я ставлю 20.
    prior_strength = 20.0
    alpha = global_probs * prior_strength

    # smoothed rating
    smoothed = pivot.apply(lambda row: dirichlet_smoothed_rating(row.values, alpha), axis=1)

    out = pivot.copy()
    out.columns = [f"n_{k}" for k in [1,2,3,4,5]]
    out["reviews_count"] = out.sum(axis=1)
    out["rating_smoothed"] = smoothed

    out.reset_index().to_parquet(OUT_AGG, index=False)
    print("Saved:", OUT_AGG, "rows:", len(out))

if __name__ == "__main__":
    main()
