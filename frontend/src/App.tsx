import { FormEvent, useEffect, useRef, useState } from "react";
import Live2DCharacter from "./components/Live2DCharacter";
import type { Live2DCharacterHandle } from "./components/Live2DCharacter";
import {
  getCurrentModel,
  getPersonality,
  setPersonality,
  getApiKeyStatus,
  setApiKey,
  getMemory,
  MemoryMessage,
  resetMemory,
  sendMessage,
  setModel,
  sendInteraction,
} from "./api";

import { interactions } from "./interactions";
import type { InteractionName } from "./interactions";

export default function App() {
  const [messages, setMessages] = useState<MemoryMessage[]>([]);
  const [input, setInput] = useState("");
  const [model, setModelName] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("Connecting to Amadeus...");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [hasApiKey, setHasApiKey] = useState<boolean | null>(null);
  const [apiKey, setApiKeyInput] = useState("");
  const [savingSettings, setSavingSettings] = useState(false);
  const [settingsError, setSettingsError] = useState("");
  const [settingsNotice, setSettingsNotice] = useState("");
  const [settingsSection, setSettingsSection] = useState<"connection" | "personality">("connection");
  const [personality, setPersonalityText] = useState("");
  const [savedPersonality, setSavedPersonality] = useState("");
  const [personalityLoading, setPersonalityLoading] = useState(true);
  const [personalityLoaded, setPersonalityLoaded] = useState(false);
  const [personalitySaving, setPersonalitySaving] = useState(false);
  const [personalityError, setPersonalityError] = useState("");
  const [personalityNotice, setPersonalityNotice] = useState("");
  const [personalityReload, setPersonalityReload] = useState(0);
  const personalityDirty = personalityLoaded && personality !== savedPersonality;
  const settingsBusy = savingSettings || personalitySaving;
  const modalRef = useRef<HTMLDivElement>(null);
  const missingKey = hasApiKey === false;
  const idleStatus = status === "Online" || status === "Memory cleared" || status.startsWith("Model set to ");
  const footerStatus = missingKey && idleStatus ? "No API key" : status;

  function closeSettings() {
    if (settingsBusy) return;
    if (personalityDirty && !window.confirm("Discard your unsaved personality changes?")) return;
    setApiKeyInput("");
    setSettingsError("");
    setSettingsNotice("");
    setSettingsOpen(false);
  }

  const bottomRef = useRef<HTMLDivElement>(null);
  const characterRef = useRef<Live2DCharacterHandle>(null);

  useEffect(() => {
    void initialize();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    if (!settingsOpen) return;
    let cancelled = false;
    setPersonalityLoading(true);
    setPersonalityLoaded(false);
    setPersonalityError("");
    setPersonalityNotice("");
    void getPersonality().then((text) => {
      if (cancelled) return;
      setPersonalityText(text);
      setSavedPersonality(text);
      setPersonalityLoaded(true);
    }).catch((error) => {
      if (!cancelled) setPersonalityError(error instanceof Error ? error.message : "Could not load personality");
    }).finally(() => {
      if (!cancelled) setPersonalityLoading(false);
    });
    return () => { cancelled = true; };
  }, [settingsOpen, personalityReload]);

  useEffect(() => {
    if (!settingsOpen) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    modalRef.current?.focus();
    return () => { previousFocus?.focus(); };
  }, [settingsOpen]);

  useEffect(() => {
    if (!settingsOpen || !personalityDirty) return;
    const warnBeforeLeaving = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeLeaving);
    return () => window.removeEventListener("beforeunload", warnBeforeLeaving);
  }, [settingsOpen, personalityDirty]);

  async function savePersonality() {
    if (settingsBusy || loading || !personalityLoaded || !personalityDirty || !personality.trim()) return;
    setPersonalitySaving(true);
    setPersonalityError("");
    setPersonalityNotice("");
    try {
      const saved = await setPersonality(personality);
      setPersonalityText(saved);
      setSavedPersonality(saved);
      setPersonalityNotice("Personality saved. Changes apply to your next message.");
    } catch (error) {
      setPersonalityError(error instanceof Error ? error.message : "Could not save personality");
    } finally {
      setPersonalitySaving(false);
    }
  }

  async function initialize() {
    try {
      const [memory, currentModel, configured] = await Promise.all([
        getMemory(),
        getCurrentModel(),
        getApiKeyStatus(),
      ]);

      setMessages(memory);
      setModelName(currentModel);
      setHasApiKey(configured);
      setStatus("Online");
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : "Backend unavailable"
      );
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();

    const text = input.trim();

    if (!text || loading) {
      return;
    }

    if (hasApiKey !== true) {
      setSettingsOpen(true);
      return;
    }

    // Unlock Web Audio while this function still runs from a real user gesture.
    characterRef.current?.stopSpeech();
    const speechReady = characterRef.current?.prepareSpeech().then(
      () => true,
      () => false
    );

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: text,
      },
    ]);

    setInput("");
    setLoading(true);
    setStatus("Amadeus is thinking...");

    try {
      const reply = await sendMessage(text);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: reply.response,
        },
      ]);

      setStatus("Online");
      if (reply.speechUrl && await speechReady) {
        void characterRef.current?.playSpeech(reply.speechUrl).catch((error) => {
          setStatus(error instanceof Error ? error.message : "Speech playback failed");
        });
      } else if (reply.speechUrl) {
        setStatus("Audio could not start. Check browser audio permissions and send again.");
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            error instanceof Error ? error.message : "The request failed. Please try again.",
        },
      ]);

      setStatus(
        error instanceof Error
          ? error.message
          : "Request failed"
      );
    } finally {
      setLoading(false);
    }
  }

  async function saveModel() {
    const nextModel = model.trim();

    if (settingsBusy || loading) return;
    if (!nextModel) {
      setSettingsError("Enter an LLM model.");
      return;
    }

    setSavingSettings(true);
    setSettingsError("");
    setSettingsNotice("");
    let keySaved = false;
    try {
      if (apiKey.trim()) {
        await setApiKey(apiKey.trim());
        keySaved = true;
        setHasApiKey(true);
        setApiKeyInput("");
      }
      await setModel(nextModel);

      setStatus(`Model set to ${nextModel}`);
      setSettingsNotice("Connection settings saved.");
      // Keep Settings open so drafts in the Personality section are preserved.
    } catch (error) {
      setSettingsError(
        (keySaved ? "API key saved, but model update failed. " : "") +
        (error instanceof Error ? error.message : "Could not save settings")
      );
    } finally {
      setSavingSettings(false);
    }
  }

  async function clearMemory() {
    const confirmed = window.confirm(
      "Clear Amadeus's conversation memory?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await resetMemory();

      setMessages([]);
      setStatus("Memory cleared");
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : "Could not clear memory"
      );
    }
  }

  async function handleInteraction(name: InteractionName) {
    if (loading) return;

    const interaction = interactions[name];
    const result = characterRef.current?.playMotion(interaction.motion) ?? "not-ready";
    if (result === "busy") return;
    if (result !== "started") {
      setStatus(result === "missing" ? "Reaction animation is missing" : "Character is still loading");
      return;
    }

    // Unlock audio during the click; the recording URL arrives with the reply.
    const speechReady = characterRef.current?.prepareSpeech().then(
      () => true,
      () => false
    );
    setLoading(true);

    try {
      const reply = await sendInteraction(interaction.backendId);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: reply.response,
        },
      ]);

      setStatus("Online");
      if (reply.speechUrl && await speechReady) {
        void characterRef.current?.playSpeech(reply.speechUrl).catch((error) => {
          setStatus(error instanceof Error ? error.message : "Interaction audio failed");
        });
      } else if (reply.speechUrl) {
        setStatus("Audio could not start. Check browser audio permissions and try again.");
      }
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : "Interaction failed"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      {/* Character Panel */}
      <section className="character-panel">
        <header className="brand">
          <div className="brand-mark">
            A
          </div>

          <div>
            <h1>AMADEUS</h1>
            <p>Personal AI Companion</p>
          </div>
        </header>

        <div className="character-stage">
          <div className="scanline" />

          <div className="character-viewport">
            <Live2DCharacter ref={characterRef} onSpeechError={setStatus} />

            {(Object.keys(interactions) as InteractionName[]).map((name) => {
              const interaction = interactions[name];
              return (
                <button
                  key={name}
                  type="button"
                  className="touch-button"
                  style={interaction.position}
                  aria-label={interaction.label}
                  disabled={loading}
                  onClick={() => void handleInteraction(name)}
                >
                  {interaction.label}
                </button>
              );
            })}
          </div>
        </div>

        <footer className="system-footer" role="status" aria-live="polite">
          <span
            className={
              footerStatus === "No API key" ? "status-dot warning" : status === "Online"
                ? "status-dot online"
                : "status-dot"
            }
          />

          <span>
            {footerStatus}
          </span>
        </footer>
      </section>

      {/* Chat Panel */}
      <section className="chat-panel">
        <div className="chat-toolbar">
          <div>
            <span className="eyebrow">
              LAB MEMBER 004
            </span>

            <h2>
              Conversation
            </h2>
          </div>

          <div className="toolbar-actions">
            <button
              className="ghost-button"
              onClick={() => setSettingsOpen(true)}
            >
              Settings
            </button>

            <button
              className="ghost-button danger"
              onClick={clearMemory}
            >
              Reset memory
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <span>
                AMADEUS SYSTEM READY
              </span>

              <h3>
                Start a conversation.
              </h3>

              <p>
                Your existing Flask backend and memory system
                are still doing the actual work.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <article
              key={`${message.created_at ?? "message"}-${index}`}
              className={`message ${
                message.role === "user"
                  ? "user"
                  : "assistant"
              }`}
            >
              <div className="message-meta">
                {message.role === "user"
                  ? "YOU"
                  : "AMADEUS"}

                {message.created_at && (
                  <time>
                    {message.created_at}
                  </time>
                )}
              </div>

              <div className="bubble">
                {message.content}
              </div>
            </article>
          ))}

          {/* Typing Indicator */}
          {loading && (
            <article className="message assistant">
              <div className="message-meta">
                AMADEUS
              </div>

              <div className="bubble typing">
                <i />
                <i />
                <i />
              </div>
            </article>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Message Input */}
        <form
          className="composer"
          onSubmit={submit}
        >
          <textarea
            value={input}
            onChange={(event) => {
              setInput(event.target.value);
            }}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();

                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="Message Amadeus..."
            rows={1}
          />

          <button
            type="submit"
            disabled={!input.trim() || loading}
          >
            Send
          </button>
        </form>
        <div className="build-label">
          <span className="build-dot" aria-hidden="true" />
          DEVELOPER BUILD
        </div>
      </section>

      {/* Settings Modal */}
      {settingsOpen && (
        <div
          className="modal-backdrop"
          onMouseDown={closeSettings}
        >
          <div
            className="modal settings-modal"
            ref={modalRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
            tabIndex={-1}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                closeSettings();
              }
              if (event.key === "Tab") {
                const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(
                  'button:not(:disabled), input:not(:disabled), textarea:not(:disabled)'
                )).filter((element) => element.getClientRects().length > 0);
                const first = controls[0];
                const last = controls[controls.length - 1];
                if (event.shiftKey && (document.activeElement === first || document.activeElement === event.currentTarget)) {
                  event.preventDefault(); last?.focus();
                } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === event.currentTarget)) {
                  event.preventDefault(); first?.focus();
                }
              }
            }}
            onMouseDown={(event) => {
              event.stopPropagation();
            }}
          >
            <div className="modal-heading">
              <div>
                <span className="eyebrow">
                  SYSTEM CONFIGURATION
                </span>

                <h3 id="settings-title">
                  Settings
                </h3>
              </div>

              <button
                className="close-button"
                aria-label="Close settings"
                onClick={closeSettings}
                disabled={settingsBusy}
              >
                ×
              </button>
            </div>

            <nav className="settings-sections" aria-label="Settings sections">
              <button type="button" aria-pressed={settingsSection === "connection"}
                onClick={() => setSettingsSection("connection")}>Connection</button>
              <button type="button" aria-pressed={settingsSection === "personality"}
                onClick={() => setSettingsSection("personality")}>
                Personality{personalityDirty && <span className="unsaved-dot" aria-label="Unsaved changes" />}
              </button>
            </nav>

            <div hidden={settingsSection !== "connection"}>
              <label>
                OpenRouter API key
                <input
                  type="password"
                  value={apiKey}
                  onChange={(event) => setApiKeyInput(event.target.value)}
                  placeholder={hasApiKey ? "Enter a replacement key" : "Enter your API key"}
                  autoComplete="new-password"
                  spellCheck={false}
                  disabled={settingsBusy}
                  aria-describedby="api-key-help"
                />
              </label>
              <p className="settings-help" id="api-key-help">
                {hasApiKey ? "A key is saved. Leave blank to keep it." : "No API key is saved."}
                {" "}Saved on the computer running Amadeus. Saving does not verify the key.
              </p>

              <label>
                LLM model

                <input
                  value={model}
                  disabled={settingsBusy}
                  onChange={(event) => {
                    setModelName(event.target.value);
                  }}
                  placeholder="deepseek/deepseek-v3.2-exp"
                />
              </label>

              {settingsError && <p className="settings-error" role="alert">{settingsError}</p>}
              {settingsNotice && <p className="settings-success" role="status">{settingsNotice}</p>}

              <div className="modal-actions">
                <button
                  className="ghost-button"
                  onClick={closeSettings}
                  disabled={settingsBusy}
                >
                  Close
                </button>

                <button
                  className="primary-button"
                  onClick={saveModel}
                  disabled={settingsBusy || loading}
                >
                  {savingSettings ? "Saving..." : "Save connection"}
                </button>
              </div>
            </div>

            <section hidden={settingsSection !== "personality"} aria-label="Personality editor">
              <p className="personality-intro" id="personality-help">
                Shape how Amadeus speaks and responds. Edit the current personality below.
              </p>
              {personalityLoading ? <p className="settings-help" role="status">Loading personality...</p> : (
                <>
                  {personalityLoaded && <>
                    <label htmlFor="personality-text">Personality instructions</label>
                    <textarea id="personality-text" className="personality-text"
                      value={personality} disabled={personalitySaving}
                      aria-describedby="personality-help personality-hint"
                      placeholder="Describe Amadeus’s personality, tone, and behavior..."
                      onChange={(event) => {
                        setPersonalityText(event.target.value);
                        setPersonalityNotice("");
                        setPersonalityError("");
                      }} />
                    <div className="personality-meta">
                      <span>{personalityDirty ? "Unsaved changes" : "Current personality"}</span>
                      <span>{personality.length.toLocaleString()} characters</span>
                    </div>
                    <p className="settings-help" id="personality-hint">
                      Saved changes apply to your next message. Your conversation memory stays intact.
                    </p>
                    {personalityDirty && !personality.trim() && <p className="settings-help">Enter a personality before saving.</p>}
                  </>}
                  {personalityError && <p className="settings-error" role="alert">{personalityError}</p>}
                  {personalityNotice && <p className="settings-success" role="status">{personalityNotice}</p>}
                  <div className="modal-actions personality-actions">
                    {!personalityLoaded ? <button className="ghost-button"
                      onClick={() => setPersonalityReload((value) => value + 1)}>Retry loading</button> : <>
                      <button className="ghost-button" disabled={settingsBusy || !personalityDirty}
                        onClick={() => {
                          setPersonalityText(savedPersonality);
                          setPersonalityError("");
                          setPersonalityNotice("");
                        }}>Discard changes</button>
                      <button className="primary-button" onClick={() => void savePersonality()}
                        disabled={settingsBusy || loading || !personalityDirty || !personality.trim()}>
                        {personalitySaving ? "Saving..." : "Save personality"}
                      </button>
                    </>}
                  </div>
                </>
              )}
            </section>
          </div>
        </div>
      )}
    </main>
  );
}
