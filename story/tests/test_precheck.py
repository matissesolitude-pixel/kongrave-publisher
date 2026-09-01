import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import precheck  # noqa: E402


def _setup(tmp_path, monkeypatch, paused=False, cadence_hours=24,
           journal_lines=None, queue_files=("S1.json",), has_queue_dir=True):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"paused": paused, "cadence_hours": cadence_hours}))
    journal = tmp_path / "journal.jsonl"
    if journal_lines:
        journal.write_text(
            "\n".join(json.dumps(line) for line in journal_lines) + "\n"
        )
    queue = tmp_path / "queue"
    if has_queue_dir:
        queue.mkdir()
        for name in queue_files:
            (queue / name).write_text("{}")
    monkeypatch.setattr(precheck, "CONFIG_PATH", config)
    monkeypatch.setattr(precheck, "JOURNAL", journal)
    monkeypatch.setattr(precheck, "QUEUE_DIR", queue)


def test_paused_skips_even_with_queue(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, paused=True, queue_files=("S1.json",))
    v = precheck.verdict()
    assert v.startswith("SKIP")
    assert "pause" in v


def test_no_queue_dir_skips(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, has_queue_dir=False)
    assert precheck.verdict().startswith("SKIP")


def test_empty_queue_skips(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, queue_files=())
    v = precheck.verdict()
    assert v.startswith("SKIP")
    assert "vide" in v


def test_cadence_not_elapsed_skips(tmp_path, monkeypatch):
    recent = dt.datetime.now(dt.timezone.utc).isoformat()
    _setup(tmp_path, monkeypatch, cadence_hours=24,
           journal_lines=[{"event": "published", "at": recent}])
    v = precheck.verdict()
    assert v.startswith("SKIP")
    assert "cadence" in v


def test_cadence_elapsed_and_queue_non_empty_goes(tmp_path, monkeypatch):
    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=48)).isoformat()
    _setup(tmp_path, monkeypatch, cadence_hours=24,
           journal_lines=[{"event": "published", "at": old}])
    assert precheck.verdict().startswith("GO")


def test_partial_publish_does_not_count_as_a_publication(tmp_path, monkeypatch):
    """Une séquence tronquée par un échec en cours de boucle (partial_publish)
    n'est PAS un succès : elle ne doit pas réarmer la cadence de 24h et bloquer
    la séquence suivante."""
    recent = dt.datetime.now(dt.timezone.utc).isoformat()
    _setup(tmp_path, monkeypatch, cadence_hours=24,
           journal_lines=[{"event": "partial_publish", "at": recent}])
    assert precheck.verdict().startswith("GO")


def test_unreadable_config_defaults_to_not_paused(tmp_path, monkeypatch):
    # config.json absent -> _json() retombe sur {} -> paused par défaut = False
    monkeypatch.setattr(precheck, "CONFIG_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(precheck, "JOURNAL", tmp_path / "journal.jsonl")
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "S1.json").write_text("{}")
    monkeypatch.setattr(precheck, "QUEUE_DIR", queue)
    assert precheck.verdict().startswith("GO")


def test_verdict_always_exits_zero(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, monkeypatch, paused=True)
    # __main__ n'est pas exécuté sous pytest, mais on vérifie que verdict() ne
    # lève jamais — c'est ça, la garantie "sort toujours en code 0".
    v = precheck.verdict()
    assert isinstance(v, str) and v
