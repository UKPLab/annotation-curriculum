import json
import logging
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from enum import Enum, auto
from statistics import mean, median
from typing import List, Tuple

import attr
import pandas as pd
import preprocessor
from cleantext import clean
from sklearn.model_selection import train_test_split

from ca.ext import CaDocumentClassificationAccessor, CaTaggingAccessor
from ca.paths import *


class Dataset(Enum):
    CONVINCING = auto()
    SPEC = auto()
    SIGIE = auto()
    MUC7T = auto()
    MUC7T_A = auto()
    MUC7T_B = auto()
    FAMULUS_EDA_MED = auto()
    CASG = auto()
    CASG_A = auto()
    CASG_C = auto()


class Task(Enum):
    SEQUENCE_TAGGING = auto()
    DOCUMENT_CLASSIFICATION = auto()
    PAIRWISE_CLASSIFICATION = auto()


@attr.s
class Corpus:
    all: pd.DataFrame = attr.ib()
    train: pd.DataFrame = attr.ib()
    dev: pd.DataFrame = attr.ib()
    test: pd.DataFrame = attr.ib()
    tags: List[str] = attr.ib()
    name: str = attr.ib()
    has_time: bool = attr.ib()
    task: Task = attr.ib()

    @property
    def num_tags(self) -> int:
        return len(self.tags)


def my_clean(s: str) -> str:
    return clean(s, no_urls=True, lower=False, no_line_breaks=True)


def load_famulus_eda_med() -> Corpus:
    def _convert(p: Path) -> pd.DataFrame:
        sentence_ids = []
        token_ids = []
        words = []
        labels = []
        t = []

        with p.open() as f:
            s = f.read().strip()
            chunks = re.split(r"\n\s*\n", s)

            for sentence_id, chunk in enumerate(chunks):
                chunk = chunk.strip("\n\t \uFEFF")
                if not chunk:
                    continue

                lines = chunk.split("\n")
                for token_id, line in enumerate(lines):

                    word, l1, l2, l3, l4, l5, docid, annotator, t1, t2, t3 = line.strip().split("\t")

                    sentence_ids.append(docid)
                    token_ids.append(token_id)
                    words.append(word)
                    labels.append(l5)
                    t.append(t3)

        data = {
            "document_id": sentence_ids,
            "sentence_id": sentence_ids,
            "token_id": token_ids,
            "word": words,
            "label": labels,
            "t": t,
        }

        df = pd.DataFrame(data, columns=["document_id", "sentence_id", "token_id", "word", "label", "t"])
        return df

    df_train = _convert(PATH_DATA_FAMULUS_EDA_MED_TRAIN)
    df_dev = _convert(PATH_DATA_FAMULUS_EDA_MED_DEV)
    df_test = _convert(PATH_DATA_FAMULUS_EDA_MED_TEST)

    tags = list(sorted(set(df_train["label"]) | set(df_dev["label"]) | set(df_test["label"])))

    df_all = pd.concat([df_train, df_dev, df_test])

    return Corpus(df_all, df_train, df_dev, df_test, tags, "famulus-eda-med", True, Task.SEQUENCE_TAGGING)


def load_spec() -> pd.DataFrame:
    names = ["sentence_id", "t", "label", "sentence"]
    df = pd.read_csv(PATH_DATA_SPEC, sep="\t", names=names)

    return df


def load_spec_corpus() -> Corpus:
    df = load_spec()
    tags = list(sorted(set(df["label"])))

    X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)
    return Corpus(df, X_train, None, X_test, tags, "SPEC", True, Task.DOCUMENT_CLASSIFICATION)


def load_sig_ie() -> Corpus:
    times = []
    uids = []

    with PATH_DATA_SIG_IE_ORIG.open() as f:
        for line in f:
            parts = line.split("\t")
            uids.append(parts[0])
            times.append(int(parts[1]))

    ids = []
    sentence_ids = []
    token_ids = []
    words = []
    labels = []
    t = []

    with PATH_DATA_SIG_IE_IOB.open() as f_iob:
        for sentence_id, line in enumerate(f_iob):

            token_id = 0
            for token in line.split("  "):
                if not token.strip():
                    continue

                word, label = token.strip().split("|")
                # ignore NEWLINE tokens:
                if word == "NEWLINE":
                    continue

                sentence_ids.append(sentence_id)
                token_ids.append(token_id)
                words.append(word)
                labels.append(label)
                t.append(times[sentence_id])
                ids.append(uids[sentence_id])

                token_id += 1

    data = {
        "uid": ids,
        "document_id": sentence_ids,
        "sentence_id": sentence_ids,
        "token_id": token_ids,
        "word": words,
        "label": labels,
        "t": t,
    }

    assert len(t) == len(words) == len(labels)

    df = pd.DataFrame(data, columns=["uid", "document_id", "sentence_id", "token_id", "word", "label", "t"])
    tags = list(sorted(set(df["label"])))

    X_train, X_test = train_test_split_sequence_tagging(df)
    return Corpus(df, X_train, None, X_test, tags, "SigIE", True, Task.SEQUENCE_TAGGING)


def load_convincing() -> Corpus:
    df = pd.read_csv(r"D:\git\curriculum-annotation\data\processed\convincing_A3QGFLKL2G6NJJ.csv")

    tags = list(sorted(set(df["label"])))

    X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)
    return Corpus(df, X_train, None, X_test, tags, "Convincing", True, Task.PAIRWISE_CLASSIFICATION)


def load_muc7t_a():
    return _load_muc7t_single(PATH_DATA_MUC7T_A)


def load_muc7t_b():
    return _load_muc7t_single(PATH_DATA_MUC7T_B)


def _load_muc7t_single(path: Path) -> Corpus:
    sentence_ids = []
    token_ids = []
    words = []
    labels = []
    t = []
    uids = []

    sentence_id = 0
    for p in path.iterdir():
        if p.suffix != ".xml":
            continue

        tree = ET.parse(p)
        root = tree.getroot()

        for annotation in root:
            # Convert labels to BIO
            anno_unit_labels = annotation.attrib["anno_unit_labels"].split(" ")
            bio = []
            last = "O"
            for label in anno_unit_labels:
                if label == "O":
                    cur = "O"
                elif last == "O":
                    cur = f"B-{label[:3]}"
                else:
                    cur = f"I-{label[:3]}"

                bio.append(cur)
                last = cur

            assert len(anno_unit_labels) == len(bio)
            labels.extend(bio)

            tokens = annotation.attrib["anno_unit_tokens"].split(" ")
            for token_id, word in enumerate(tokens):
                words.append(word)

                token_ids.append(token_id)
                sentence_ids.append(sentence_id)
                t.append(float(annotation.attrib["anno_time"]) / 1000.0)
                uids.append(
                    annotation.attrib["muc7_org_filename"]
                    + ":"
                    + annotation.attrib["doc_id"]
                    + ":"
                    + annotation.attrib["sent_id"]
                )

            sentence_id += 1

    data = {
        "uid": uids,
        "document_id": sentence_ids,
        "sentence_id": sentence_ids,
        "token_id": token_ids,
        "word": words,
        "label": labels,
        "t": t,
    }

    assert len(t) == len(words) == len(labels), f"{len(t)} != {len(words)} != {len(labels)}"

    df = pd.DataFrame(data, columns=["uid", "document_id", "sentence_id", "token_id", "word", "label", "t"])
    tags = list(sorted(set(df["label"])))

    X_train, X_eval = train_test_split_sequence_tagging(df, test_size=0.3)
    X_dev, X_test = train_test_split_sequence_tagging(X_eval, test_size=0.5)

    return Corpus(df, X_train, X_dev, X_test, tags, "muc7t", True, Task.SEQUENCE_TAGGING)


def load_casg() -> Corpus:
    df = pd.read_csv(PATH_DATA_CASG)
    tags = list(sorted(set(df["label"])))

    df["sentence"] = df["sentence"].apply(preprocessor.clean)

    X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)
    return Corpus(df, X_train, None, X_test, tags, "CASG", True, Task.DOCUMENT_CLASSIFICATION)


def load_casg_a() -> Corpus:
    df = load_casg().all
    df = df[df["annotator"] == "a"]

    tags = list(sorted(set(df["label"])))

    X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)
    return Corpus(df, X_train, None, X_test, tags, "CASG_A", True, Task.DOCUMENT_CLASSIFICATION)


def load_casg_c() -> Corpus:
    df = load_casg().all
    df = df[df["annotator"] == "c"]
    tags = list(sorted(set(df["label"])))

    X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)
    return Corpus(df, X_train, None, X_test, tags, "CASG_C", True, Task.DOCUMENT_CLASSIFICATION)


def load_corpus(corpus: Dataset) -> Corpus:
    logging.info("Loading [%s]", corpus.name)
    if corpus == Dataset.SPEC:
        return load_spec_corpus()
    elif corpus == Dataset.SIGIE:
        return load_sig_ie()
    elif corpus == Dataset.CONVINCING:
        return load_convincing()
    elif corpus == Dataset.MUC7T:
        return load_muc7t_a()
    elif corpus == Dataset.MUC7T_A:
        return load_muc7t_a()
    elif corpus == Dataset.MUC7T_B:
        return load_muc7t_b()
    elif corpus == Dataset.FAMULUS_EDA_MED:
        return load_famulus_eda_med()
    elif corpus == Dataset.CASG:
        return load_casg()
    elif corpus == Dataset.CASG_A:
        return load_casg_a()
    elif corpus == Dataset.CASG_C:
        return load_casg_c()
    else:
        raise RuntimeError(f"Invalid dataset name: [{corpus.name}]")


def train_test_split_sequence_tagging(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    idx = list(set(df["sentence_id"]))
    idx_train, idx_test = train_test_split(idx, test_size=test_size, random_state=42)

    train = df[df["sentence_id"].apply(lambda e: e in idx_train)]
    test = df[df["sentence_id"].apply(lambda e: e in idx_test)]

    return train, test


def dump_splits():
    def _dump_split(corpus: Corpus, field: str):
        p = PATH_RESULTS_SPLITS / (corpus.name + ".json")
        data = {}

        if corpus.train is not None:
            data["train"] = corpus.train[field].unique().tolist()

        if corpus.dev is not None:
            data["dev"] = corpus.dev[field].unique().tolist()

        if corpus.test is not None:
            data["test"] = corpus.test[field].unique().tolist()

        with p.open("w") as f:
            json.dump(data, f, indent=2)

    PATH_RESULTS_SPLITS.mkdir(parents=True, exist_ok=True)

    _dump_split(load_sig_ie(), "uid")
    _dump_split(load_spec_corpus(), "sentence_id")
    _dump_split(load_muc7t_a(), "uid")

    pass


def _main():
    dump_splits()


if __name__ == "__main__":
    _main()
