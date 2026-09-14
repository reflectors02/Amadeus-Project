"""Message controls adapted from cmh95209's feature branch (MIT).

Versions belong to one stable message ID, so deleting adjacent messages never
merges unrelated reply versions. Only the final reply can be regenerated.

"I have no idea how any of this works, but I think we won't need to touch it right? Well, if we do we can ask cmh""
    -reflectors
"""
from contextlib import contextmanager
import sqlite3
import threading

from flask import g, jsonify, request
import chat
import memory as store
import preferences

_lock = threading.Lock()


@contextmanager
def database():
    conn = sqlite3.connect(store.PATH_TO_MEMORY)
    conn.row_factory = sqlite3.Row
    try:
        store._ensure_messages_table(conn.cursor())
        conn.execute("""CREATE TABLE IF NOT EXISTS message_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            japanese TEXT,
            audio_url TEXT,
            active INTEGER NOT NULL DEFAULT 0
        )""")
        conn.commit()
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def history():
    with database() as conn:
        rows = conn.execute("SELECT * FROM messages ORDER BY id").fetchall()
        versions = conn.execute(
            "SELECT id, message_id, active FROM message_versions ORDER BY id"
        ).fetchall()
    groups = {}
    for version in versions:
        groups.setdefault(version["message_id"], []).append(version)
    result = []
    for row in rows:
        item = dict(id=row["id"], role=row["role"], content=row["content"],
                    created_at=row["created_at"],
                    can_replay=bool(row["japanese"] or row["audio_url"]))
        siblings = groups.get(row["id"], [])
        if siblings:
            item["version_ids"] = [v["id"] for v in siblings]
            item["version"] = next(
                (i + 1 for i, v in enumerate(siblings) if v["active"]), 1)
        result.append(item)
    return result


def snapshot(conn):
    return [tuple(r) for r in conn.execute("SELECT * FROM messages ORDER BY id")]


def add_version(conn, message_id, content, japanese, audio_url):
    conn.execute("UPDATE message_versions SET active = 0 WHERE message_id = ?",
                 (message_id,))
    conn.execute("""INSERT INTO message_versions
        (message_id, content, japanese, audio_url, active) VALUES (?, ?, ?, ?, 1)""",
        (message_id, content, japanese, audio_url))
    conn.execute("UPDATE messages SET content = ?, japanese = ?, audio_url = ? WHERE id = ?",
                 (content, japanese, audio_url, message_id))


def install(app):
    # Serialize conversation mutations across browser tabs in the Flask process.
    @app.before_request
    def acquire_conversation():
        paths = {"/", "/memory_reset", "/doSpecialInteraction"}
        if request.method == "POST" and (
                request.path in paths or request.path.startswith("/messages/")):
            if not _lock.acquire(blocking=False):
                return jsonify(message="Another conversation action is running. Try again."), 409
            g.message_action_lock = True

    @app.teardown_request
    def release_conversation(error=None):
        if g.pop("message_action_lock", False):
            _lock.release()

    @app.after_request
    def include_history(response):
        if (
            request.method != "OPTIONS"
            and response.status_code == 200
            and response.is_json
            and request.endpoint in {
                "request_message", "doSpecialInteraction", "getMemory"
            }
        ):
            payload = response.get_json()
            if isinstance(payload, dict):
                payload["messages"] = history()
                response.set_data(app.json.dumps(payload))
                response.headers["Cache-Control"] = "no-store"
        return response

    @app.post("/messages/<int:message_id>/<action>")
    def message_action(message_id, action):
        if action not in {"edit", "delete", "regenerate", "version"}:
            return jsonify(message="Unknown message action."), 404
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(message="Expected a JSON object."), 400

        with database() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
            if row is None:
                return jsonify(message="Message no longer exists. Reload the conversation."), 404
            if row["role"] not in {"user", "assistant"}:
                return jsonify(message="This message cannot be changed."), 400

            if action == "delete":
                conn.execute("DELETE FROM message_versions WHERE message_id = ?", (message_id,))
                conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            elif action == "edit":
                content = data.get("content")
                if not isinstance(content, str) or not content.strip():
                    return jsonify(message="Enter a message before saving."), 400
                content = content.strip()
                if content != row["content"]:
                    # English edits invalidate the old Japanese/recording.
                    conn.execute("UPDATE messages SET content = ?, japanese = NULL, audio_url = NULL WHERE id = ?",
                                 (content, message_id))
                    conn.execute("UPDATE message_versions SET content = ?, japanese = NULL, audio_url = NULL WHERE message_id = ? AND active = 1",
                                 (content, message_id))
            elif action == "version":
                version_id = data.get("version_id")
                if type(version_id) is not int:
                    return jsonify(message="Invalid reply version."), 400
                version = conn.execute("SELECT * FROM message_versions WHERE id = ? AND message_id = ?",
                                       (version_id, message_id)).fetchone()
                if version is None:
                    return jsonify(message="Reply version not found."), 404
                conn.execute("UPDATE message_versions SET active = (id = ?) WHERE message_id = ?",
                             (version_id, message_id))
                conn.execute("UPDATE messages SET content = ?, japanese = ?, audio_url = ? WHERE id = ?",
                             (version["content"], version["japanese"], version["audio_url"], message_id))
            else:
                if not chat.has_api_key():
                    return jsonify(message="Add an OpenRouter API key in Settings."), 400
                messages = conn.execute("SELECT id, role, content FROM messages ORDER BY id").fetchall()
                if (len(messages) < 2 or messages[-1]["id"] != message_id
                        or row["role"] != "assistant" or messages[-2]["role"] != "user"):
                    return jsonify(message="Regenerate the final reply after a user message."), 409
                before = snapshot(conn)
                context = [dict(role=m["role"], content=m["content"]) for m in messages[:-1]]

        if action == "regenerate":
            # Do not change the old reply until generation succeeds.
            context = preferences.trim_history(context, preferences.load()["context_budget"])
            try:
                pack = chat.getResponsePacked(context, internal_context={
                    "role": "system",
                    "content": "Regenerate the reply to the final user message. Do not treat this as a new arrival or absence."
                })
            except Exception:
                app.logger.exception("Reply regeneration failed")
                return jsonify(message="Regeneration failed. Your previous reply is unchanged."), 502
            with database() as conn:
                conn.execute("BEGIN IMMEDIATE")
                if snapshot(conn) != before:
                    return jsonify(message="Conversation changed during generation. Please try again."), 409
                if not conn.execute("SELECT 1 FROM message_versions WHERE message_id = ?", (message_id,)).fetchone():
                    add_version(conn, message_id, row["content"], row["japanese"], row["audio_url"])
                add_version(conn, message_id, pack.assistant_reply_ENG, pack.assistant_reply_JPS, None)

        return jsonify(messages=history())
