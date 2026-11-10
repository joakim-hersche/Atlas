"""pipeline/i18n: every metric id has a French label and EN/DE/FR units; the glossary is complete."""
from pathlib import Path

import yaml

from pipeline.harmonize.schema import load_metrics

I18N = Path(__file__).resolve().parents[1] / "i18n"
LABEL_FIELDS = ("label_fr", "unit_en", "unit_de", "unit_fr")
GLOSSARY_FIELDS = ("term_en", "term_de", "term_fr", "en", "de", "fr")


def _load(name):
    return yaml.safe_load((I18N / name).read_text(encoding="utf-8")) or {}


def test_every_metric_has_labels():
    labels = _load("labels.yaml")
    ids = set(load_metrics()["id"])
    missing = sorted(ids - set(labels))
    assert not missing, f"metric ids without an entry in pipeline/i18n/labels.yaml: {missing}"
    incomplete = sorted(k for k in ids if any(not str(labels[k].get(f) or "").strip() for f in LABEL_FIELDS))
    assert not incomplete, f"entries missing one of {LABEL_FIELDS}: {incomplete}"


def test_no_stale_labels():
    stale = sorted(set(_load("labels.yaml")) - set(load_metrics()["id"]))
    assert not stale, f"labels.yaml entries without a metric in metrics.yaml: {stale}"


def test_glossary_complete():
    g = _load("glossary.yaml")
    assert len(g) >= 15
    bad = sorted(k for k, v in g.items() if any(not str(v.get(f) or "").strip() for f in GLOSSARY_FIELDS))
    assert not bad, f"glossary entries missing one of {GLOSSARY_FIELDS}: {bad}"
