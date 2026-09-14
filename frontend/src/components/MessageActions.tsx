import { useRef, useState } from "react";
import { API_BASE, type MemoryMessage } from "../api";
import "./MessageActions.css";

type Props = {
  message: MemoryMessage;
  busy: boolean;
  canRegenerate: boolean;
  onBusy: (busy: boolean) => void;
  onMessages: (messages: MemoryMessage[]) => void;
  onStatus: (status: string) => void;
  onStop: () => void;
  onReplay: () => Promise<void>;
  onPrepare: () => Promise<void>;
  onPlay: () => Promise<void>;
};

export default function MessageActions({
  message, busy, canRegenerate, onBusy, onMessages, onStatus,
  onStop, onReplay, onPrepare, onPlay,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const working = useRef(false);
  const versions = message.version_ids ?? [];
  const version = message.version ?? 1;

  async function act(action: string, data: Record<string, unknown> = {}) {
    if (busy || working.current || message.id == null) return;
    if (action === "delete" && !window.confirm(
      "Delete this message and all its reply versions from memory? Later messages will stay."
    )) return;
    working.current = true;
    onBusy(true);
    onStop();
    setError("");
    const ready = action === "regenerate"
      ? onPrepare().then(() => true, () => false)
      : Promise.resolve(false);
    onStatus(action === "regenerate" ? "Amadeus is rethinking..." : "Updating message...");
    try {
      const response = await fetch(`${API_BASE}/messages/${message.id}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.message || "Message action failed");
      if (!Array.isArray(result.messages)) throw new Error("Invalid conversation response");
      onMessages(result.messages);
      setEditing(false);
      onStatus("Online");
      if (action === "regenerate") {
        if (await ready) {
          try {
            await onPlay();
          } catch {
            onStatus("Reply saved, but audio failed. Try Replay.");
          }
        } else {
          onStatus("Reply saved. Use Replay to start its voice.");
        }
      }
    } catch (cause) {
      const text = cause instanceof Error ? cause.message : "Message action failed";
      setError(text);
      onStatus(text);
    } finally {
      working.current = false;
      onBusy(false);
    }
  }

  if (message.id == null || !["user", "assistant"].includes(message.role)) return null;

  return (
    <div className="message-controls">
      <div className="message-actions" role="group" aria-label="Message actions">
        {message.role === "assistant" && message.can_replay && (
          <button type="button" disabled={busy || editing} title="Replay voice"
            onClick={() => void onReplay()}>🔊 Replay</button>
        )}
        {canRegenerate && (
          <button type="button" disabled={busy || editing} title="Generate another reply"
            onClick={() => void act("regenerate")}>↻ Regenerate</button>
        )}
        <button type="button" disabled={busy || editing} title="Edit this message"
          onClick={() => {
            onStop();
            setDraft(message.content);
            setError("");
            setEditing(true);
          }}>✏️ Edit</button>
        <button type="button" disabled={busy || editing} title="Delete this message"
          onClick={() => void act("delete")}>🗑️ Delete</button>
        {versions.length > 1 && (
          <span className="version-nav" aria-label="Reply versions">
            <button type="button" aria-label="Previous reply version"
              disabled={busy || editing || version <= 1}
              onClick={() => void act("version", { version_id: versions[version - 2] })}>◀</button>
            <span className="version-count">{version}/{versions.length}</span>
            <button type="button" aria-label="Next reply version"
              disabled={busy || editing || version >= versions.length}
              onClick={() => void act("version", { version_id: versions[version] })}>▶</button>
          </span>
        )}
      </div>
      {editing && (
        <div className="message-edit">
          <textarea autoFocus rows={3} value={draft} disabled={busy}
            aria-label="Edit message"
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (busy) return;
              if (event.key === "Escape") setEditing(false);
              if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                if (draft.trim()) void act("edit", { content: draft });
              }
            }} />
          <p>Updates saved memory; later replies stay unchanged.
            {message.role === "assistant" && " Changing the English text disables this version's old voice."}</p>
          <div className="message-edit-actions">
            <button type="button" disabled={busy || !draft.trim()}
              onClick={() => void act("edit", { content: draft })}>Save</button>
            <button type="button" disabled={busy} onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      )}
      {error && <p className="settings-error" role="alert">{error}</p>}
    </div>
  );
}
