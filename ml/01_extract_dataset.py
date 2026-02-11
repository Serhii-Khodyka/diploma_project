import os
import pandas as pd
import psycopg
from sqlalchemy import create_engine
from ml.config import DB_DSN, RAW_REVIEWS_PARQUET, DATA_DIR

SQL = """
SELECT
  r.id               AS review_id,
  r.product_id,
  r.rating,
  r.text             AS text,         
  r.pros,
  r.cons,
  r.review_date,
  r.source_url              AS review_url,
  p.id               AS product_pk,
  p.title,
  p.brand,
  p.sku,
  p.url              AS product_url,
  p.category_id
FROM reviews r
JOIN products p ON p.id = r.product_id
"""

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    engine = create_engine(DB_DSN)
    df = pd.read_sql(SQL, engine)

    # 1) чистка: прибрати без rating
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df[df["rating"].notna()].copy()

    # 2) базове: порожні тексти теж прибираємо (інакше BERT не зможе)
    df["text"] = df["text"].fillna("").astype(str).str.strip()
    df = df[df["text"].str.len() > 0].copy()

    # 3) нормалізація
    df["rating"] = df["rating"].astype(int).clip(1, 5)

    df.to_parquet(RAW_REVIEWS_PARQUET, index=False)
    print("Saved:", RAW_REVIEWS_PARQUET, "rows:", len(df))

if __name__ == "__main__":
    main()
