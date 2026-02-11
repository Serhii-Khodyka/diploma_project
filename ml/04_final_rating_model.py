import pandas as pd
import numpy as np
from pathlib import Path
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

FEATURES = "data/features.parquet"
AGG = "data/products_agg.parquet"
OUT_MODEL = "data/models/final_rating_catboost.cbm"
OUT_DATA = "data/products_final_scores.parquet"

def main():
    Path("data/models").mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(FEATURES)
    agg = pd.read_parquet(AGG)

    # агрегуємо sentiment на рівні товару
    g = df.groupby("product_id")
    sent = g["sentiment"].value_counts(normalize=True).unstack(fill_value=0).reset_index()
    # гарантуємо колонки
    for c in ["pos","neu","neg"]:
        if c not in sent.columns:
            sent[c] = 0.0
    sent = sent.rename(columns={"pos":"share_pos", "neu":"share_neu", "neg":"share_neg"})

    other = g.agg(
        mismatch_rate=("mismatch", "mean"),
        relevant_rate=("relevant_quality", "mean"),
        avg_len=("text", lambda s: float(np.mean([len(x) for x in s.astype(str)]))),
    ).reset_index()

    prod = agg.merge(sent, on="product_id", how="left").merge(other, on="product_id", how="left")

    # заповнення NaN
    for c in ["share_pos","share_neu","share_neg","mismatch_rate","relevant_rate","avg_len"]:
        prod[c] = prod[c].fillna(0.0)

    # Фічі
    X = prod[[
        "rating_smoothed",
        "reviews_count",
        "share_pos","share_neu","share_neg",
        "mismatch_rate","relevant_rate",
        "avg_len"
    ]].copy()

    # Target: згладжений рейтинг (MVP як “псевдо-істина”)
    y = prod["rating_smoothed"].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = CatBoostRegressor(
        depth=6,
        learning_rate=0.05,
        iterations=1500,
        loss_function="MAE",
        verbose=200
    )
    model.fit(X_train, y_train, eval_set=(X_test, y_test), use_best_model=True)

    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    print("MAE:", mae)

    model.save_model(OUT_MODEL)
    print("Saved model:", OUT_MODEL)

    # Final score 1..5
    prod["final_score"] = model.predict(X).clip(1, 5)
    prod.to_parquet(OUT_DATA, index=False)
    print("Saved:", OUT_DATA, "rows:", len(prod))

if __name__ == "__main__":
    main()
