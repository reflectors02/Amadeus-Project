import memory as store
from llm import get_llm, reset_llm
from pydantic import BaseModel, Field
from chat_interactions import INTERACTION_EVENTS, INTERACTION_RESPONSES
import random

default_LLM_Model = store.DEFAULT_LLM_MODEL
API_KEY = store.load_api_key()
LLM_Model = store.load_llm_model(default_model=default_LLM_Model)


#pre: The intended new_model is a string e.g., "deepseek/deepseek-v3.2-exp"
#post: global LLM_Model should be changed to new_model
#      LLM_Model.txt should be updated accordingly, to store the latest model the user chose.
def setLLMModel(new_model: str):
    global LLM_Model
    LLM_Model = new_model.strip()
    store.save_llm_model(LLM_Model)
    reset_llm()  # IMPORTANT: recreate ChatOpenAI with the new model
    print("[Amadeus] Model changed to " + LLM_Model)


#pre:
#post: If LLM_Model is empty, return an Error message
#      else, return the LLM Model e.g., "deepseek/deepseek-v3.2-exp"
def getLLMModel():
    global LLM_Model
    return LLM_Model.strip() if LLM_Model else "No Model Selected."


#pre: key_string is a string in the format: "sk-or-v1-566...."
#post: API_KEY set to key_string
#      API_Key.txt should also be updated accordingly.
def setKey(key_string: str):
    global API_KEY
    next_key = key_string.strip()
    store.save_api_key(next_key)
    API_KEY = next_key
    reset_llm()  # IMPORTANT: recreate with new key
    print("[Amadeus] API key updated")


#pre: new_personality is new context for personality e.g., "This is Kurisu Makise....etc"
#post: Should update personality.txt using store.save_personality.
#      yes i know this is a bit round about, but to keep consistency.
def setPersonality(new_personality: str):
    store.save_personality(new_personality)
    print("[Amadeus] Updated personality!")


def getPersonality() -> str:
    return store.load_personality()


def has_api_key() -> bool:
    return bool(API_KEY.strip())


#pre:
#post: memory.json should be erased
def resetMemory():
    store.reset_memory()
    print("[Amadeus] Memory Reset!")


#pre:
#post: returns a dict of JSON e.g., [{"role": "user", "content": "kurisu"....}....]
def get_raw_memory():
    return store.load_memory_raw()


class AmadeusPack(BaseModel):
    assistant_reply_JPS: str = Field(..., description=(
        "PRIMARY response: Kurisu's dialogue written natively in Japanese, as she would actually speak it. "
        "Must be plain spoken Japanese for TTS."
        " Allowed: Japanese characters, ASCII letters/digits if needed, and these punctuation marks only: 、。！？"
        " Newlines are allowed. Do NOT include: parentheses/brackets/quotes/asterisks/emojis/markdown/ellipses (…)/colons/semicolons."
        " Avoid long dashes and repeated punctuation.")
    )
    assistant_reply_ENG: str = Field(..., description="English translation of assistant_reply_JPS, shown in the UI for the user to read. May include stage directions.")


# pre:
# - message_context is a List[Dict[str, str]] with keys: "role" and "content"
# - message_context contains recent user/assistant messages only (no system persona)
# - personality is read from disk for each reply; internal system context is available
# - LLM (via LangChain + OpenRouter) is properly configured
#
# post:
# - returns an AmadeusPack with:
#     - assistant_reply_JPS: Japanese dialogue written natively (primary, for TTS)
#     - assistant_reply_ENG: English translation of it, for the UI
# - exactly ONE LLM call is made under normal operation
# - on structured output failure, falls back to a plain LLM call with a safe default Japanese reply
def getResponsePacked(message_context, internal_context=None) -> AmadeusPack:
    llm = get_llm(API_KEY, LLM_Model)

    # IMPORTANT: Add a system rule that tells the model exactly what to output.
    pack_rules = {
        "role": "system",
         "content": (
            "Write only Kurisu's spoken dialogue. "
            "Do not include narration, stage directions, actions, facial expressions, "
            "body language, or inner thoughts in either response. "
            "FIRST write assistant_reply_JPS natively in Japanese: think and speak the way a native "
            "Japanese speaker (Makise Kurisu) really would — natural, idiomatic spoken Japanese, "
            "NOT a word-for-word translation from English. "
            "THEN write assistant_reply_ENG as an English translation of that Japanese dialogue, for the user to read. "
            "Keep the meaning and tone consistent between both languages."
        ),
    }

    messages = (
        store.load_default_personality_messages()
        + [internal_context if internal_context is not None else store.load_internal_context()]
        + [pack_rules]
        + message_context
    )

    try:
        structured = llm.with_structured_output(AmadeusPack, method="function_calling",)        
        out: AmadeusPack = structured.invoke(messages)
        return out
    except Exception as e:
        # Fallback: if structured output fails, degrade gracefully
        print("[Amadeus] Packed response parse failed:", repr(e))
        # Fall back to plain response and reuse it as display, with a safe minimal JA
        plain = llm.invoke(messages).content
        return AmadeusPack(
            assistant_reply_ENG=plain, 
            assistant_reply_JPS="ごめん、今ちょっと調子が悪い。もう一回言って。"
            )


# pre:
# - user_message is a non-empty string from the user
# - SQLite memory store is available and writable
# - getResponsePacked(message_context) is defined and functional
#
# post:
# - appends the user message to memory
# - builds recent conversation context from memory
# - calls getResponsePacked(...) exactly once
# - appends assistant_reply_ENG to memory
# - returns an AmadeusPack containing:
#     - assistant_reply_JPS (native Japanese dialogue, for TTS)
#     - assistant_reply_ENG (English translation, for the UI)
def getOutputPacked(user_message: str) -> AmadeusPack:
    # Snapshot the previous turn before the new message becomes the latest one.
    internal_context = store.load_internal_context()
    store.append_message("user", user_message)
    context = store.build_prompt_messages()[-80:]

    pack = getResponsePacked(context, internal_context=internal_context)

    # Store what the user actually sees
    store.append_message("assistant", pack.assistant_reply_ENG)
    return pack



# ---------- SPECIAL INTERACTIONS ---------- 

# pre:
# - interaction value represents int value of the corresponding interaction. e.g.,
#   1 -> chest touch
#   2 -> Head pat
#   3 -> Arm poke
#
# post:
# - append in format: ("user", "[Interaction event: The user touched your shoulder.]")
# - return the hard coded responses
def SpecialInteraction(interaction_value: int) -> dict:
    event = INTERACTION_EVENTS.get(interaction_value)
    response_variants = INTERACTION_RESPONSES.get(interaction_value)
    if event is None or not response_variants:
        raise ValueError("Unknown interaction")
    # Select the text AND recording together, never independently.
    variant = random.choice(response_variants)
    response = variant["text"]
    store.append_message("user", event)
    store.append_message("assistant", response);    
    return {"response": response, "audio_url": variant.get("audio_url")}

# pre:
# - hourlu
def HourlyAnnouncement(hourly_id: int) -> dict:
    response_pack = HOURLY_ANNOUNCEMENTS.get(hourly_id)
    response = response_pack["text"]
    audio_url = response_pack["audio_url"]
    store.append_message("assistant, response")
    return {"response": response, "audio_url": audio_url}
