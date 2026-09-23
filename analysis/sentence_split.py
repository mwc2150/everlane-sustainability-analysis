from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Dict, Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "intermediate"
OUTPUT_PATH = OUT_DIR / "sentences_all.csv"


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    text = clean_text(text)
    if not text:
        return []

    try:
        import nltk
        from nltk.tokenize import sent_tokenize

        try:
            sentences = sent_tokenize(text)
        except LookupError:
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\(\[])", text)
    except Exception:
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\(\[])", text)

    cleaned = []
    for sentence in sentences:
        s = clean_text(sentence)
        if s:
            cleaned.append(s)
    return cleaned


def build_sentence_rows(
    df: pd.DataFrame,
    source: str,
    source_type: str,
    doc_id_col: str,
    title_col: str | None = None,
    text_col: str = "text",
    date_col: str = "date",
    url_col: str | None = None,
    subreddit_col: str | None = None,
    extra_cols: Iterable[str] = (),
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for index, row in df.iterrows():
        doc_id = row.get(doc_id_col, f"{source}_{index}")
        date_value = row.get(date_col, "")
        title_value = row.get(title_col, "") if title_col else ""
        url_value = row.get(url_col, "") if url_col else ""
        subreddit_value = row.get(subreddit_col, "") if subreddit_col else ""
        raw_text = clean_text(row.get(text_col, ""))

        if title_col and title_value:
            doc_text = f"{clean_text(title_value)} {raw_text}".strip()
        else:
            doc_text = raw_text

        sentences = split_sentences(doc_text)
        if not sentences:
            continue

        for sentence_index, sentence in enumerate(sentences, start=1):
            record = {
                "source": source,
                "source_type": source_type,
                "document_id": clean_text(doc_id),
                "date": clean_text(date_value),
                "title": clean_text(title_value),
                "url": clean_text(url_value),
                "subreddit": clean_text(subreddit_value),
                "sentence_index": sentence_index,
                "sentence": sentence,
                "document_text": doc_text,
            }
            for extra_col in extra_cols:
                record[extra_col] = row.get(extra_col, "")
            rows.append(record)

    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: List[Dict[str, Any]] = []

    reddit_posts = pd.read_csv(RAW_DIR / "reddit_posts.csv")
    all_rows.extend(
        build_sentence_rows(
            reddit_posts,
            source="reddit",
            source_type="post",
            doc_id_col="url",
            title_col="title",
            text_col="text",
            date_col="date",
            url_col="url",
            subreddit_col="subreddit",
        )
    )

    reddit_comments = pd.read_csv(RAW_DIR / "reddit_comments.csv")
    all_rows.extend(
        build_sentence_rows(
            reddit_comments,
            source="reddit",
            source_type="comment",
            doc_id_col="post_id",
            title_col=None,
            text_col="text",
            date_col="date",
            url_col=None,
            subreddit_col="subreddit",
            extra_cols=("score",),
        )
    )

    everlane_web = pd.read_csv(RAW_DIR / "everlane_web.csv")
    all_rows.extend(
        build_sentence_rows(
            everlane_web,
            source="everlane_web",
            source_type="page",
            doc_id_col="url",
            title_col="page",
            text_col="text",
            date_col="date",
            url_col="url",
            subreddit_col=None,
            extra_cols=("page",),
        )
    )

    gdelt_articles = pd.read_csv(RAW_DIR / "gdelt_articles_usable.csv")
    all_rows.extend(
        build_sentence_rows(
            gdelt_articles,
            source="gdelt",
            source_type="article",
            doc_id_col="url",
            title_col="title",
            text_col="text",
            date_col="publish_date",
            url_col="url",
            subreddit_col=None,
            extra_cols=("status",),
        )
    )

    sentence_df = pd.DataFrame(all_rows)
    sentence_df = sentence_df[
        [
            "source",
            "source_type",
            "document_id",
            "subreddit",
            "date",
            "title",
            "url",
            "sentence_index",
            "sentence",
            "document_text",
        ]
    ]
    sentence_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(sentence_df)} sentences to {OUTPUT_PATH}")
    print(sentence_df.groupby(["source", "source_type"]).size().to_string())


if __name__ == "__main__":
    main()
