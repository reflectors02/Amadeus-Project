export type MemoryMessage = {
  id?: number;
  can_replay?: boolean;
  role: string;
  content: string;
  created_at?: string;
};

export type MessageReply = {
  messageId?: number;
  response: string;
  speechUrl?: string;
};

const API_BASE = "http://127.0.0.1:5050";

export async function getPersonality(): Promise<string> {
  const data = await parseResponse(await fetch(`${API_BASE}/getPersonality`, { cache: "no-store" }));
  if (typeof data.personality !== "string") throw new Error("Could not read personality");
  return data.personality;
}

export async function setPersonality(personality: string): Promise<string> {
  const data = await parseResponse(await fetch(`${API_BASE}/setPersonality`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ personality }),
  }));
  if (typeof data.personality !== "string") throw new Error("Could not confirm saved personality");
  return data.personality;
}

export async function getApiKeyStatus(): Promise<boolean> {
  const response = await fetch(`${API_BASE}/api_key_status`, { cache: "no-store" });
  const data = await parseResponse(response);
  if (typeof data.configured !== "boolean") throw new Error("Could not read API key status");
  return data.configured;
}

export async function setApiKey(key: string): Promise<void> {
  await parseResponse(await fetch(`${API_BASE}/set_key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key }),
  }));
}

async function parseResponse(response: Response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data?.message || `Request failed (${response.status})`
    );
  }

  return data;
}

export async function sendMessage(userInput: string): Promise<MessageReply> {
  const response = await fetch(`${API_BASE}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_input: userInput,
    }),
  });

  const data = await parseResponse(response);
  if (typeof data.response !== "string") {
    throw new Error("Backend returned an invalid response");
  }

  return {
    response: data.response,
    messageId: typeof data.message_id === "number" ? data.message_id : undefined,
    speechUrl:
      typeof data.speech_id === "string"
        ? `${API_BASE}/speech/${encodeURIComponent(data.speech_id)}`
        : undefined,
  };
}

export async function getMemory(): Promise<MemoryMessage[]> {
  const response = await fetch(`${API_BASE}/getMemory`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  const data = await parseResponse(response);
  return data.messages ?? [];
}

export async function resetMemory(): Promise<void> {
  const response = await fetch(`${API_BASE}/memory_reset`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  await parseResponse(response);
}

export async function getCurrentModel(): Promise<string> {
  const response = await fetch(`${API_BASE}/getCurrLLMModel`);

  const data = await parseResponse(response);
  return data.message ?? "";
}

export async function setModel(model: string): Promise<void> {
  const response = await fetch(`${API_BASE}/setLLMModel`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
    }),
  });

  await parseResponse(response);
}

export async function sendInteraction(interactionValue: number): Promise<MessageReply> {
  const response = await fetch(`${API_BASE}/doSpecialInteraction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      interaction_value: interactionValue,
    }),
  });

  const data = await parseResponse(response);
  if (typeof data.response !== "string") throw new Error("Invalid interaction response");
  return {
    response: data.response,
    messageId: typeof data.message_id === "number" ? data.message_id : undefined,
    speechUrl:
      typeof data.audio_url === "string" &&
      data.audio_url.startsWith("/reaction_audio/")
        ? `${API_BASE}${data.audio_url}`
        : undefined,
  };
}

export function messageAudioUrl(id: number): string {
  return `${API_BASE}/message_audio/${id}`;
}

export type ConversationSettings = { context_budget: number; voice_retention: number };

export async function getConversationSettings(): Promise<ConversationSettings> {
  return parseResponse(await fetch(`${API_BASE}/conversation_settings`, { cache: "no-store" }));
}

export async function saveConversationSettings(settings: ConversationSettings): Promise<ConversationSettings> {
  return parseResponse(await fetch(`${API_BASE}/conversation_settings`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  }));
}
