"""
Tests hors ligne de publish_story.py — doublure complète de l'API Graph via
FakeMeta (aucun réseau). Couvre ce que le brief demande explicitement :

  - la RÈGLE D'OR : un conteneur qui échoue (à la création OU au statut)
    empêche TOUTE publication, y compris celles qui auraient réussi ;
  - la garde de quota, AVANT la création du moindre conteneur ;
  - l'ordre de publication (croissant, jamais en parallèle) ;
  - --dry-run : conteneurs créés + attendus, rien publié, rien déplacé ;
  - pause + cadence (mode --queue) ;
  - le risque résiduel que la règle d'or ne couvre PAS : media_publish qui
    échoue en cours de boucle alors que tout était FINISHED (partial_publish).

Ce que ces tests NE couvrent PAS (réseau réel, décrit dans le rapport) :
  - le comportement réel de Meta face à une vraie image STORIES 1080x1920 ;
  - le vrai quota partagé avec LIGNE et le carrousel sur le compte réel ;
  - le comportement du job GitHub Actions (sparse-checkout, push résilient).
"""
import datetime as dt
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import ig_api           # noqa: E402
import publish_story     # noqa: E402


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeMeta:
    """Doublure de l'API Graph pour tout ce que publish_story.py appelle :
    création de conteneur STORIES, lecture de statut, media_publish, quota.
    """

    def __init__(self, quota_usage=0, quota_total=100):
        self.calls = []
        self.publish_calls = 0
        self._next_id = 1
        self._created_count = 0
        self.container_status = {}
        self.fail_create_for_urls = ()      # sous-chaînes d'image_url à refuser à la création
        self.fail_status_for_nth_container = None   # 1-indexé : ce conteneur passe ERROR
        self.fail_publish_after = None      # 1-indexé : ce media_publish échoue
        self.quota_usage = quota_usage
        self.quota_total = quota_total

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        data = kwargs.get("data") or {}

        if url.endswith("/media") and data.get("media_type") == "STORIES":
            image_url = data.get("image_url", "")
            if any(bad in image_url for bad in self.fail_create_for_urls):
                return FakeResponse(400, {"error": {"message": f"refus simulé — {image_url}"}})
            self._created_count += 1
            cid = f"story_container_{self._next_id}"
            self._next_id += 1
            status = "FINISHED"
            if self.fail_status_for_nth_container == self._created_count:
                status = "ERROR"
            self.container_status[cid] = status
            return FakeResponse(200, {"id": cid})

        if url.endswith("content_publishing_limit"):
            return FakeResponse(200, {"data": [{
                "quota_usage": self.quota_usage,
                "config": {"quota_total": self.quota_total},
            }]})

        if url.endswith("/media_publish"):
            self.publish_calls += 1
            if self.fail_publish_after == self.publish_calls:
                return FakeResponse(400, {"error": {"message": "refus simulé — media_publish"}})
            cid = data.get("creation_id")
            return FakeResponse(200, {"id": f"media_{cid}"})

        # lecture de statut : GET /{GRAPH}/{VERSION}/{container_id}?fields=status_code
        cid = url.rsplit("/", 1)[-1]
        status = self.container_status.get(cid, "FINISHED")
        return FakeResponse(200, {"status_code": status})

    def publish_order(self):
        return [
            kwargs["data"]["creation_id"]
            for _, url, kwargs in self.calls
            if url.endswith("/media_publish")
        ]

    def creation_calls_count(self):
        return sum(
            1 for _, url, kwargs in self.calls
            if url.endswith("/media") and (kwargs.get("data") or {}).get("media_type") == "STORIES"
        )


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isole publish_story sur un répertoire jetable + une doublure Meta.
    Ne touche JAMAIS story/queue, story/published ni story/journal.jsonl réels."""
    queue = tmp_path / "queue"
    published = tmp_path / "published"
    queue.mkdir()
    published.mkdir()
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"paused": False, "cadence_hours": 24}))
    journal = tmp_path / "journal.jsonl"

    monkeypatch.setattr(publish_story, "STORY_DIR", tmp_path)
    monkeypatch.setattr(publish_story, "QUEUE_DIR", queue)
    monkeypatch.setattr(publish_story, "PUBLISHED_DIR", published)
    monkeypatch.setattr(publish_story, "JOURNAL", journal)
    monkeypatch.setattr(publish_story, "CONFIG_PATH", config)

    monkeypatch.setenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "IGUSER")
    monkeypatch.setenv("META_ACCESS_TOKEN", "TOKEN")

    fake = FakeMeta()
    monkeypatch.setattr(ig_api, "_request", fake.request)

    return {"tmp_path": tmp_path, "queue": queue, "published": published,
            "journal": journal, "config": config, "fake": fake}


def _write_manifest(queue_dir, sid, slides):
    (queue_dir / f"{sid}.json").write_text(json.dumps({"id": sid, "slides": slides}))


def _run(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["publish_story.py"] + argv)
    publish_story.main()


# ------------------------------------------------------------------ RÈGLE D'OR

def test_container_creation_failure_aborts_before_any_publish(env, monkeypatch):
    fake = env["fake"]
    fake.fail_create_for_urls = ("slide_3",)
    _write_manifest(env["queue"], "seqA", [1, 2, 3, 4])

    with pytest.raises(ig_api.IgApiError):
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    assert fake.publish_calls == 0
    assert not env["journal"].is_file()
    assert (env["queue"] / "seqA.json").is_file()          # jamais bougé de la file
    assert not (env["published"] / "seqA.json").exists()


def test_container_finished_status_error_aborts_before_any_publish(env, monkeypatch):
    """Cas plus retors : le conteneur est bien CRÉÉ, mais son statut passe
    ERROR au lieu de FINISHED — c'est ce que wait_all_finished() doit attraper."""
    fake = env["fake"]
    fake.fail_status_for_nth_container = 3          # slide 3 sur 4
    _write_manifest(env["queue"], "seqB", [1, 2, 3, 4])

    with pytest.raises(ig_api.IgApiError):
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    # les 4 conteneurs ont bien été CRÉÉS (règle d'or = tous d'abord)...
    assert fake.creation_calls_count() == 4
    # ...mais AUCUNE publication n'a eu lieu, car un seul a échoué au statut.
    assert fake.publish_calls == 0
    assert not env["journal"].is_file()
    assert (env["queue"] / "seqB.json").is_file()


# --------------------------------------------------------------------- QUOTA

def test_quota_gate_blocks_before_creating_any_container(env, monkeypatch):
    fake = env["fake"]
    fake.quota_usage, fake.quota_total = 97, 100     # 3 restantes, il en faut 4+5=9
    _write_manifest(env["queue"], "seqC", [1, 2, 3, 4])

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    assert exc.value.code == 0
    assert fake.creation_calls_count() == 0
    assert fake.publish_calls == 0
    assert not env["journal"].is_file()


def test_quota_gate_allows_when_margin_is_sufficient(env, monkeypatch):
    fake = env["fake"]
    fake.quota_usage, fake.quota_total = 0, 100
    _write_manifest(env["queue"], "seqD", [1, 2, 3])

    _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    assert fake.creation_calls_count() == 3
    assert fake.publish_calls == 3


# ----------------------------------------------------------------- ORDONNANCEMENT

def test_publication_order_is_ascending_slide_order(env, monkeypatch):
    fake = env["fake"]
    _write_manifest(env["queue"], "seqE", [1, 2, 3, 4, 5])

    _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    # les container_id sont attribués dans l'ordre de création, lui-même dans
    # l'ordre des slides du manifeste : story_container_1..5 == slides 1..5.
    assert fake.publish_order() == [
        "story_container_1", "story_container_2", "story_container_3",
        "story_container_4", "story_container_5",
    ]


# ----------------------------------------------------------------------- DRY-RUN

def test_dry_run_creates_and_waits_but_publishes_nothing(env, monkeypatch):
    fake = env["fake"]
    _write_manifest(env["queue"], "seqF", [1, 2, 3])

    _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story", "--dry-run"])

    assert fake.creation_calls_count() == 3
    assert fake.publish_calls == 0
    assert not env["journal"].is_file()
    assert (env["queue"] / "seqF.json").is_file()
    assert not (env["published"] / "seqF.json").exists()


# ------------------------------------------------------------- PARTIAL PUBLISH

def test_partial_publish_journals_what_shipped_and_reraises(env, monkeypatch):
    fake = env["fake"]
    fake.fail_publish_after = 3      # la 3e publication échoue, sur 5
    _write_manifest(env["queue"], "seqG", [1, 2, 3, 4, 5])

    with pytest.raises(ig_api.IgApiError):
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    assert fake.publish_calls == 3           # 2 réussies + la 3e qui échoue
    lines = env["journal"].read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "partial_publish"
    assert entry["id"] == "seqG"
    assert len(entry["media"]) == 2
    assert [m["slide"] for m in entry["media"]] == [1, 2]
    # la séquence tronquée reste en file : ni "published" propre, ni déplacement.
    assert (env["queue"] / "seqG.json").is_file()
    assert not (env["published"] / "seqG.json").exists()


# ------------------------------------------------------------------ FULL SUCCESS

def test_full_success_journals_and_moves_queue_to_published(env, monkeypatch):
    fake = env["fake"]
    _write_manifest(env["queue"], "seqH", [1, 2, 3])

    _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    assert fake.publish_calls == 3
    lines = env["journal"].read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "published"
    assert entry["id"] == "seqH"
    assert entry["slides"] == 3
    assert [m["slide"] for m in entry["media"]] == [1, 2, 3]
    assert not (env["queue"] / "seqH.json").exists()
    assert (env["published"] / "seqH.json").is_file()


# ----------------------------------------------------------------- PAUSE + CADENCE

def test_paused_skips_without_touching_the_api(env, monkeypatch):
    fake = env["fake"]
    env["config"].write_text(json.dumps({"paused": True, "cadence_hours": 24}))
    _write_manifest(env["queue"], "seqI", [1, 2])

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    assert exc.value.code == 0
    assert fake.calls == []


def test_cadence_not_elapsed_skips_without_touching_the_api(env, monkeypatch):
    fake = env["fake"]
    recent = dt.datetime.now(dt.timezone.utc).isoformat()
    env["journal"].write_text(json.dumps({"event": "published", "at": recent}) + "\n")
    _write_manifest(env["queue"], "seqJ", [1, 2])

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])

    assert exc.value.code == 0
    assert fake.calls == []


def test_force_bypasses_pause_and_cadence_but_quota_still_checked(env, monkeypatch):
    fake = env["fake"]
    env["config"].write_text(json.dumps({"paused": True, "cadence_hours": 24}))
    recent = dt.datetime.now(dt.timezone.utc).isoformat()
    env["journal"].write_text(json.dumps({"event": "published", "at": recent}) + "\n")
    _write_manifest(env["queue"], "seqK", [1, 2])

    _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story", "--force"])

    assert fake.publish_calls == 2
    lines = env["journal"].read_text().splitlines()
    assert len(lines) == 2       # l'ancienne entrée + la nouvelle
    assert json.loads(lines[-1])["event"] == "published"


def test_empty_queue_skips(env, monkeypatch):
    fake = env["fake"]
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])
    assert exc.value.code == 0
    assert fake.calls == []


def test_manifest_without_slides_is_a_hard_error(env, monkeypatch):
    (env["queue"] / "seqL.json").write_text(json.dumps({"id": "seqL", "slides": []}))
    with pytest.raises(SystemExit):
        _run(monkeypatch, ["--queue", "--base-url", "https://pages.example/media/story"])


def test_queue_and_explicit_id_are_mutually_exclusive(env, monkeypatch):
    with pytest.raises(SystemExit):
        _run(monkeypatch, ["seqM", "--queue", "--base-url", "https://pages.example/media/story"])
    with pytest.raises(SystemExit):
        _run(monkeypatch, ["--base-url", "https://pages.example/media/story"])


# --------------------------------------------------------------------- EXPLICITE

def test_explicit_mode_ignores_pause_and_cadence_gates(env, monkeypatch):
    """Mode explicite (un ID nommé, pas --queue) : mêmes portes que le carrousel
    — aucune porte pause/cadence, seul le quota reste vérifié."""
    fake = env["fake"]
    env["config"].write_text(json.dumps({"paused": True, "cadence_hours": 24}))
    _write_manifest(env["queue"], "seqN", [1, 2])

    _run(monkeypatch, ["seqN", "--base-url", "https://pages.example/media/story"])

    assert fake.publish_calls == 2
