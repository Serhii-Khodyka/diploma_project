import os
import pandas as pd
from transformers import pipeline

RAW = "data/raw_reviews.parquet"
OUT = "data/features.parquet"

# Можеш замінити на інший чекпоінт
SENTIMENT_MODEL = os.environ.get("SENTIMENT_MODEL", "cardiffnlp/twitter-xlm-roberta-base-sentiment")
# Для "релевантності" у MVP краще зробити rule-based або навчити окремо.
# Тут залишу заглушку: relevant=True (або прості евристики).
# Далі ти зможеш замінити на classification pipeline.

def sentiment_to_3(label: str) -> str:
    # У cardiffnlp labels часто: "negative", "neutral", "positive"
    l = (label or "").lower()
    if "neg" in l:
        return "neg"
    if "neu" in l:
        return "neu"
    if "pos" in l:
        return "pos"
    # fallback
    return "neu"

def is_relevant_quality_rule(text: str) -> bool:
    """
    MVP-евристика: відсікаємо відгуки, що схожі на логістику/сервіс без оцінки якості.
    Пізніше заміниш на BERT-класифікатор.
    """
    t = (text or "").lower()
    bad_markers = ["доставка", "нова пошта", "кур'єр", "упаковк", "сервіс", "менеджер", "оплата", "кредит", "розстрочк"]
    good_markers = ["якість", "працює", "камера", "акум", "екран", "заряд", "потужн", "шум", "нагріва", "батар"]
    # якщо є маркери якості — релевантно
    if any(m in t for m in good_markers):
        return True
    # якщо тільки логістика/сервіс — нерелевантно
    if any(m in t for m in bad_markers) and len(t) < 250:
        return False
    return True

def mismatch_rule(sent3: str, rating: int) -> bool:
    if sent3 == "neg" and rating >= 4:
        return True
    if sent3 == "pos" and rating <= 2:
        return True
    return False

def main():
    df = pd.read_parquet(RAW)

    sent_pipe = pipeline(
        "text-classification",
        model=SENTIMENT_MODEL,
        tokenizer=SENTIMENT_MODEL,
        truncation=True,
        top_k=None
    )

    texts = df["text"].astype(str).tolist()
    preds = sent_pipe(texts, batch_size=16)

    # preds: list of dicts OR list of lists depending on top_k
    labels = []
    scores = []
    for p in preds:
        if isinstance(p, list):
            p0 = max(p, key=lambda x: x["score"])
        else:
            p0 = p
        labels.append(p0["label"])
        scores.append(float(p0["score"]))

    df["sent_label_raw"] = labels
    df["sent_score"] = scores
    df["sentiment"] = df["sent_label_raw"].apply(sentiment_to_3)

    # quality relevance (MVP rules)
    df["relevant_quality"] = df["text"].apply(is_relevant_quality_rule)

    # mismatch (MVP rules)
    df["mismatch"] = df.apply(lambda r: mismatch_rule(r["sentiment"], int(r["rating"])), axis=1)

    df.to_parquet(OUT, index=False)
    print("Saved:", OUT, "rows:", len(df))

if __name__ == "__main__":
    main()
