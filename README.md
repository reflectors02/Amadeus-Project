# Amadeus

A *Steins;Gate*-inspired AI companion with persistent conversation memory, Japanese speech, and an animated Live2D character.

Amadeus brings together an OpenRouter-powered conversational model, local GPT-SoVITS voice synthesis, and a React WebUI. It began as a personal experiment and remains an actively developed project exploring personality, voice, and continuity in a virtual companion.

**Latest: Release Build - 091426** · [Changelog](#changelog)

[Features](#features) · [Installation](#installation) · [Configuration](#configuration) · [Launching](#launching-amadeus) · [Updating](#updating-amadeus) · [Troubleshooting](#troubleshooting)

![Amadeus conversation interface](docs/images/mainmenu.png)

<details>
<summary>Settings preview</summary>

![Amadeus settings](docs/images/settings.png)

</details>

## Features

- **Conversation:** persistent SQLite history, adjustable context budget, message editing and deletion, and response regeneration with version switching.
- **Voice:** streamed Japanese speech, audio-driven lip sync, and replay of saved responses.
- **Character:** Live2D idle and talking motions, touch reactions, and paired prerecorded interaction lines.
- **Customization:** change the OpenRouter model and edit the character's personality from Settings.
- **Web access:** enable or disable OpenRouter web search from the message composer.
- **Startup:** macOS and Windows launchers start the voice server, backend, and WebUI together.

### Conversation and voice

You can chat in English. In normal operation, one LLM call produces natural Japanese dialogue for GPT-SoVITS and an English translation for the conversation UI. Japanese is written first to improve the spoken response.

> [!IMPORTANT]
> **Amadeus uses OpenRouter for its conversational LLM.** Bring your own API key and select a supported model in Settings. The LLM does not run on your GPU, and the project does not bundle a local LLM.
>
> Voice synthesis, Live2D rendering, the frontend/backend, and SQLite history run locally. Conversation context is sent to OpenRouter to generate replies.

## Installation

### 0. Requirements

The setup uses the following tools. Install Git, Git LFS, Conda, Node.js, and the Windows Build Tools before continuing; Python and FFmpeg are covered in step 3.

| Requirement | Used for |
| --- | --- |
| Git and Git LFS | Downloading the project and pretrained model files. |
| Conda (Anaconda or Miniconda) | Managing separate Python environments for Amadeus and GPT-SoVITS. |
| Node.js and npm | Running the React WebUI. |
| Python 3.10 | Running GPT-SoVITS; installed through Conda in step 3. |
| FFmpeg | Audio processing; installed through Conda in step 3. |
| Visual Studio C++ Build Tools (Windows) | Compiling Python dependencies that require native C/C++ extensions. |

You will also need an **OpenRouter API key** for conversations. An NVIDIA GPU is strongly recommended for faster local voice synthesis; CPU operation is possible but slower.

#### Windows: install the C++ Build Tools

Install these before the GPT-SoVITS dependencies to avoid missing-compiler errors:

1. Open the [Visual Studio downloads page](https://visualstudio.microsoft.com/downloads/?q=build+tools).
2. Under **Tools for Visual Studio**, download **Build Tools for Visual Studio**.
3. Run the installer and select **Desktop development with C++**. Keep the recommended MSVC compiler tools and Windows SDK selected.
4. Complete the installation. Restart Windows if the installer requests it, then reopen your terminal before continuing.

If Build Tools is already installed, open **Visual Studio Installer → Modify** and check that the C++ workload is selected. Installing only the installer or the VS Code C/C++ extension does not install the compiler toolchain. See [Microsoft's C++ installation guide](https://learn.microsoft.com/en-us/cpp/build/vscpp-step-0-installation) for details.

#### Before running commands

Use a terminal where `conda`, `git`, `node`, and `npm` are available. On Windows, Anaconda Prompt is a convenient option.

Amadeus uses two separate Conda environments:

| Environment | Purpose |
| --- | --- |
| `amadeus` | Flask backend and conversation logic. |
| `GPTSoVits` | Local voice synthesis and its dependencies. |

Run the steps below in order and pay attention to the active environment. Unless a step says otherwise, start from the `Amadeus-Project` root directory.

### 1. Clone Amadeus

```bash
git clone https://github.com/reflectors02/Amadeus-Project.git
cd Amadeus-Project
```

Clone GPT-SoVITS into the project directory:

```bash
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
```

Your local directory will then contain both:

```text
Amadeus-Project/
├── backend/
├── frontend/
├── scripts/
└── GPT-SoVITS/      # external project, cloned locally
```

### 2. Create the Amadeus Backend Environment

From the repository root:

```bash
cd backend
conda env create -f environment.yml
```

Activate it:

```bash
conda activate amadeus
```

Return to the project root:

```bash
cd ..
```

Backend dependency information is tracked in:

```text
backend/environment.yml
backend/requirements.in
```

### 3. Create the GPT-SoVITS Environment

```bash
cd GPT-SoVITS
conda create -n GPTSoVits python=3.10
conda activate GPTSoVits
```

Install GPT-SoVITS dependencies **inside the `GPTSoVits` environment**:

```bash
python -m pip install -r extra-req.txt --no-deps
python -m pip install -r requirements.txt
conda install ffmpeg
```

#### If needed: create the language-detection cache directory

GPT-SoVITS uses `fast-langdetect` for language detection. If you encounter
a missing model cache directory error, create the directory below.

Run this while still inside the `GPT-SoVITS` directory.

##### Windows

```bat
mkdir GPT_SoVITS\pretrained_models\fast_langdetect
```

##### macOS / Linux

```bash
mkdir -p GPT_SoVITS/pretrained_models/fast_langdetect
```

Return to the Amadeus project root:

```bash
cd ..
```

### 4. Configure PyTorch

The exact PyTorch installation depends on the machine running GPT-SoVITS.

#### NVIDIA GPU

Install the CUDA-enabled PyTorch build appropriate for your system.

Example:

```bash
conda activate GPTSoVits
python -m pip uninstall -y torch torchvision torchaudio
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Check the current PyTorch installation instructions if your CUDA environment requires a different build.

#### CPU Only

A CPU-only configuration is also possible, although synthesis will be slower.

Example:

```bash
conda activate GPTSoVits
python -m pip uninstall -y torch torchvision torchaudio torchcodec
python -m pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
```

### 5. Download GPT-SoVITS Pretrained Models

Install Git LFS if necessary:

```bash
git lfs install
```

Clone the pretrained model repository into a separate temporary folder from the Amadeus project root:

```bash
git clone https://huggingface.co/lj1995/GPT-SoVITS GPT-SoVITS-pretrained
```

Using a different folder name avoids a collision with the GPT-SoVITS source folder created in step 1.

Copy the required pretrained files from `GPT-SoVITS-pretrained/` into:

```text
GPT-SoVITS/GPT_SoVITS/pretrained_models/
```

The exact files required can vary with GPT-SoVITS versions, so Amadeus should only be paired with a GPT-SoVITS version known to work with the project.

### 6. Install Frontend Dependencies

The automatic launcher runs `npm install` if `frontend/node_modules/` is missing.

You can also install the dependencies manually:

```bash
cd frontend
npm install
cd ..
```

No separate Live2D or Cubism installation is required for the WebUI. The Cubism Web runtime, framework source, shaders, and model assets used by Amadeus are part of the project frontend.

## Configuration

### OpenRouter and model selection

Open **Settings → Connection** to enter your OpenRouter API key and choose a model. You can change the active model without restarting Amadeus. The API key is saved locally in `backend/data/api_key.txt`; do not commit it.

### Web access

Use **Web on / Web off** beside the message composer to toggle OpenRouter web search. The setting is saved with the selected model and restored on restart. Web searches can add cost and response time. If the state cannot be confirmed, the button displays **Web retry**.

### Personality

Open **Settings → Personality** to edit the character's instructions. Saved changes apply to the next message and keep your conversation history intact.

### Conversation memory and voice replay

Open **Settings → Conversation** to adjust:

| Setting | Default | Range | Purpose |
| --- | --- | --- | --- |
| Conversation memory (estimated tokens) | 40,000 | 500–1,000,000 | Sets the approximate budget for recent history sent to the model. |
| Voice recordings to keep | 100 | 1–10,000 | Limits saved generated recordings; older recordings are pruned as new ones complete. |

The history budget is a rough multilingual estimate. Personality, timing, output instructions, and the response require additional context space. The newest message is kept whole even if it exceeds the budget; full history remains in SQLite.

**Replay voice** reuses completed recordings without another LLM or TTS call. If a recording was pruned or interrupted, GPT-SoVITS recreates it from the saved Japanese reply, so it may sound different. Replies saved before Japanese voice text was stored cannot be replayed. Prerecorded touch reactions support replay and do not count toward the generated-recording limit.

Settings are saved in `backend/data/conversation_settings.json`, and recordings in `backend/generated/voices/`. The latest-recording copy at `generated/generated.wav` is retained separately.

Conversation settings and message controls were adapted from [cmh95209's feature branch](https://github.com/cmh95209/Amadeus-Project/tree/cmh95-local-llm-and-features).

## Launching Amadeus

After installation, use the launcher for your platform. It starts GPT-SoVITS, Flask, and the WebUI, waits for each service, and opens the browser.

### macOS

Make the launcher executable the first time:

```bash
chmod +x start_macos.command
```

Then double-click `start_macos.command` in Finder or run:

```bash
./start_macos.command
```

### Windows

Double-click `start_windows.bat` or run it from Command Prompt:

```bat
start_windows.bat
```

Press `Ctrl+C` in the launcher terminal to stop the stack. Runtime logs are saved in `.runtime/logs/`. The launcher also clears stale Amadeus listeners and runs `npm install` when frontend dependencies are missing.

| Service | Default address |
| --- | --- |
| GPT-SoVITS | http://127.0.0.1:9880 |
| Flask backend | http://127.0.0.1:5050 |
| WebUI | http://127.0.0.1:5173 |

<details>
<summary>Manual startup for development and debugging</summary>

Run each service in a separate terminal, starting from the repository root.

**GPT-SoVITS**

```bash
conda activate GPTSoVits
cd backend
python start_gptsovits.py
```

**Backend**

```bash
conda activate amadeus
cd backend
python main.py
```

**Frontend**

```bash
cd frontend
npm run dev
```

</details>

## Updating Amadeus

Pull the latest project changes:

```bash
git pull origin main
```

### Update Backend Environment

```bash
conda activate amadeus
cd backend
conda env update -f environment.yml --prune
cd ..
```

### Update Frontend

```bash
cd frontend
npm install
cd ..
```

### Update GPT-SoVITS

Only update GPT-SoVITS when Amadeus is known to support the newer version:

```bash
conda activate GPTSoVits
cd GPT-SoVITS
git pull origin main
python -m pip install -r requirements.txt
cd ..
```

## Troubleshooting

<details>
<summary>Windows: Microsoft Visual C++ is required or a dependency fails to compile</summary>

Follow the [C++ Build Tools setup](#windows-install-the-c-build-tools), including the **Desktop development with C++** workload. Complete the installation, reopen your terminal, and retry the dependency installation from the GPT-SoVITS folder:

```bash
conda activate GPTSoVits
python -m pip install -r extra-req.txt --no-deps
python -m pip install -r requirements.txt
```

Read the first compiler or package error if installation still fails; a failed wheel build can have causes other than missing Build Tools.

</details>

<details>
<summary>GPT-SoVITS reports a missing Python module</summary>

Make sure the dependencies were installed in `GPTSoVits`, rather than `base` or `amadeus`. From the Amadeus project root:

```bash
conda activate GPTSoVits
cd GPT-SoVITS
python -m pip install -r extra-req.txt --no-deps
python -m pip install -r requirements.txt
python -m pip check
```

Check the installation output for errors before relaunching. Creating a Conda environment alone does not install GPT-SoVITS dependencies.

</details>

<details>
<summary>Launcher says a port is already in use</summary>

The launcher attempts to clear stale Amadeus listeners from:

```text
9880
5050
5173
```

If a port cannot be cleared, inspect:

```text
.runtime/logs/
```

The backend intentionally uses port `5050` rather than `5000` to avoid conflicts with macOS services that commonly use port 5000.

</details>

<details>
<summary>macOS says start_macos.command cannot be executed</summary>

Run:

```bash
chmod +x start_macos.command
```

and try again.

</details>

<details>
<summary>Amadeus cannot connect to the backend</summary>

Check that the backend is available at:

```text
http://127.0.0.1:5050
```

When running the full launcher, inspect:

```text
.runtime/logs/backend.log
```

</details>

<details>
<summary>Amadeus has no voice</summary>

Check that GPT-SoVITS is available at:

```text
http://127.0.0.1:9880
```

Also verify that the required pretrained models exist under:

```text
GPT-SoVITS/GPT_SoVITS/pretrained_models/
```

</details>

<details>
<summary>Live2D character does not appear</summary>

Check the browser developer console and verify that the model reaches the expected loading stages:

```text
model3.json loaded
moc3 loaded
texture loaded
model loaded successfully
```

Also verify that the WebGL shader assets exist under:

```text
frontend/public/cubism-shaders/WebGL/
```

and that the model assets exist under:

```text
frontend/public/live2d/
```

</details>

<details>
<summary>Shader program is not initialized</summary>

The Cubism Web renderer loads shader files asynchronously. A warning during the initial frames can occur while the shaders are loading.

If the character eventually renders, this initial warning is not fatal.

Persistent shader compile errors usually indicate that the shader files are not being served from the expected public path.

</details>

<details>
<summary>Frontend dependencies are missing</summary>

Run:

```bash
cd frontend
npm install
```

The automatic launcher also performs this step if `node_modules/` does not exist.

</details>

<details>
<summary>Backend dependencies are missing or outdated</summary>

Run:

```bash
conda activate amadeus
cd backend
conda env update -f environment.yml --prune
```

</details>

<details>
<summary>Resetting conversation memory</summary>

Stop Amadeus first, then back up `backend/data/memory.db` if you want to preserve your conversation history. Run the following command from the project root to delete the stored history.

macOS/Linux:

```bash
rm backend/data/memory.db
```

Windows:

```bat
del backend\data\memory.db
```

Restart Amadeus afterward. A new database will be created automatically.

</details>

## Development

The frontend and backend are independent, allowing the interface to evolve without rewriting the conversational core.

| Component | Technology | Location |
| --- | --- | --- |
| Backend | Python, Flask, SQLite, OpenRouter | `backend/` |
| WebUI | React 19, TypeScript, Vite | `frontend/` |
| Character | Live2D Cubism SDK for Web, WebGL | `frontend/src/live2d/` |
| Voice synthesis | GPT-SoVITS native API v2 | `GPT-SoVITS/` (cloned separately) |
| Launcher | Shared Python startup script | `scripts/launcher.py` |

<details>
<summary>Live2D and audio implementation</summary>

`Live2DCharacter.tsx` connects the React interface to `KurisuController.ts` and `KurisuModel.ts`. The official Cubism Web runtime loads the model, textures, and shaders directly in the browser; Unity and Cubism Editor are not required.

- `MotionPlayer.ts` manages looping idle/talk states and higher-priority one-shot reactions.
- `SpeechPlayer.ts` plays streamed audio and measures its waveform with the Web Audio API. Smoothed amplitude drives `ParamMouthOpenY`.
- Touch reactions can interrupt the body animation while lip sync continues. After a reaction, the character returns to talk or idle according to playback state.

| Asset | Path |
| --- | --- |
| Character models | `frontend/public/live2d/` |
| WebGL shaders | `frontend/public/cubism-shaders/WebGL/` |
| Cubism Core | `frontend/public/live2dcubismcore.min.js` |
| Prerecorded reactions | `backend/assets/reaction_audio/` |

</details>

### Local data

Keep API keys, conversation history, generated audio, and runtime files out of source control:

- `backend/data/api_key.txt`
- `backend/data/memory.db`
- `backend/data/conversation_settings.json`
- `backend/generated/`
- `.runtime/`
- `frontend/node_modules/`
- `GPT-SoVITS/`

### Roadmap

- Improve prompting and character-state behavior (high priority).
- Add more hit-area interactions, including stomach pokes.
- Expand the prerecorded voice library and improve animations as resources allow.
- Explore expression control (low priority) and a future long-term memory redesign.

Longer-term ideas include activities such as chess and a hosted version with independent user sessions. APIs, dependencies, and project structure may change as development continues.

## Changelog

### 9/14/2026 -> Release Build - 091426

**Web access and conversation controls**

- Added a composer button for OpenRouter web search, with on/off, saving, and retry states.
- Connected the toggle to the active model and saved selection, preserving web access across restarts and handling duplicate `:online` suffixes.
- Added message editing, deletion, response regeneration, and switching between response versions.
- Added configurable conversation-history and saved-voice limits, plus replay of assistant responses.
- Improved the message toolbar and frontend/backend request handling, including CORS fixes.
- Incorporated conversation features adapted from [cmh95209](https://github.com/cmh95209/Amadeus-Project/tree/cmh95-local-llm-and-features).

<details>
<summary>Previous releases</summary>

### 9/8/2026 -> Release Build - 090826

**Japanese-first dialogue**

- Changed response generation to write Japanese dialogue first and then produce its English translation, improving naturalness for voice synthesis.

### 9/5/2026 -> Release Build - 090526

**Streaming speech and interactive Live2D**

- Moved to GPT-SoVITS native API v2 on port `9880` for incremental speech generation.
- Added browser-side streamed playback and audio-driven lip synchronization.
- Expanded idle and talking motions, head-pat and special-touch reactions, and motion priority with automatic return to idle/talk.
- Paired interaction text with prerecorded voice variants so replies, memory, and playback stay consistent.

### 9/4/2026 -> Release Build - 090426

**Official Cubism Web integration**

- Integrated the official Live2D Cubism SDK into the React frontend.
- Added browser model loading, character positioning, textures, and WebGL shaders.
- Replaced the earlier Pixi-based rendering approach.

### 9/3/2026 -> Release Build - 090326

**WebUI migration and automatic launchers**

- Replaced the Unity interface with a React + TypeScript WebUI.
- Added shared macOS/Windows startup, service readiness checks, browser opening, logs, and process cleanup.
- Reorganized the project into `backend/`, `frontend/`, and `scripts/`.
- Moved Flask to port `5050` to avoid common macOS port conflicts.

</details>

Older development history is available in the [commit history](https://github.com/reflectors02/Amadeus-Project/commits/main/).

## License

Original Amadeus project code is licensed under the [MIT License](LICENSE).

Third-party components and assets—including the Live2D Cubism SDK, character models, artwork, voice recordings, and model weights—are not covered by this MIT license and remain subject to their respective licenses and permissions.

