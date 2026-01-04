# Telegram Intelligence Agent 🧠

A local AI-powered agent that monitors your Telegram messages, learns your habits, and organizes actionable items into a premium local dashboard, synced directly to **Notion**.

## ✨ Features

### 🧠 Intelligent Analysis
- **Smart Monitoring**: Listens to "Saved Messages", DMs, **Mentions**, **Replies**, and **Keyword Triggers**.
- **Gemini 3.0 Powered**: Analyzes context, importance, and deadlines.
- **Context Aware**: Checks your Notion database to avoid duplicates.

### 📚 Notion Integration (SSOT)
- **Single Source of Truth**: All tasks are stored directly in a Notion Database.
- **Two-Way Sync**:
  - **Telegram -> Notion**: New tasks appear instantly.
  - **Dashboard -> Notion**: Updates (Done, Reject, Reopen) reflect instantly.
- **Robust API**: Uses efficient Search and UUID handling for reliability.

### 📊 Premium Dashboard 2.0
- **Modern UI**: Dark mode, glassmorphism, and smooth animations.
- **Real-Time**: Fetches live data from Notion.
- **Visual Cues**: Priority badges, deadlines, and sender info.
- **Daily Briefing**: Sends a summary of Top Tasks to your **Saved Messages** every morning.

## 🚀 Installation

## 🛠️ Comprehensive Setup Guide

### 1. Notion Setup (Crucial) 📚
The agent needs a specific Notion database to store tasks.

1.  **Create a New Database**:
    - In Notion, create a new page named **"Telegram Tasks"**.
    - Select **Table View** -> **New Database**.
2.  **Add Required Columns**:
    - Rename/Create these exact properties:
        | Name | Type | Options |
        | :--- | :--- | :--- |
        | **Name** | Title | |
        | **Status** | Status (or Select) | `Active`, `Done`, `Rejected` |
        | **Priority** | Number | |
        | **Sender** | Text | |
        | **Link** | URL | |
    - *Note: Property names are case-sensitive.*
3.  **Create Integration Token**:
    - Go to [Notion My Integrations](https://www.notion.so/my-integrations).
    - Click **New integration**, name it "Telegram Agent", and submit.
    - Copy the **Internal Integration Secret** (starts with `secret_...`).
4.  **Connect Integration**:
    - Go back to your Notion Database page.
    - Click the **`...`** menu (top right) -> **Connect to** -> Select **"Telegram Agent"**.
5.  **Get Database ID**:
    - Click **Share** -> **Copy link**.
    - The ID is the 32-char string between `/` and `?`.
    - Example: `https://notion.so/user/`**`a8aec4...2e089`**`?v=...`

### 2. Environment Configuration
Create a `.env` file in the root folder with the following:

```ini
# Telegram Credentials (my.telegram.org)
API_ID=123456
API_HASH=abcdef123456

# Google AI (aistudio.google.com)
GENAI_KEY=AIzaSy...

# Notion Credentials
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=a8aec4...2e089

# Session String (Generated via python generate_session.py)
SESSION_STRING=...
```

### 3. Telegram Session Login
To allow the agent to run on your behalf without constant logins (and to support 2FA), you must generate a **Session String**.

1.  **Run the Generator**:
    ```bash
    python generate_session.py
    ```
2.  **Authenticate**:
    - Enter your phone number (international format, e.g., `+1234567890`).
    - Enter the **OTP code** sent to your Telegram account.
    - (If enabled) Enter your 2FA Password.
3.  **Update Config**:
    - The script will output a long string. Copy it **entirely**.
    - Paste it into your `.env` file as the value for `SESSION_STRING`.

---

## 🧠 How it Works: Monitoring logic

The agent does not read every message you receive. It filters for **signal**.

### 1. Data Sources (Where it listens)
- **Saved Messages**: Your personal note-taking space. Any message sent here is analyzed.
- **Mentions**: If someone tags you (`@yourname`) in a group.
- **Replies**: If someone replies to your message.
- **Direct Messages (DMs)**: Only if they contain specific triggers or tasks (configurable).
- **Keywords**: Messages containing your name or custom keywords.

### 2. The AI Filter (What it looks for)
Once a message is captured, the **Gemini 3.0** model analyzes it against a strict set of criteria:

- **Is it Actionable?** (e.g., "Buy milk" -> Yes. "Hello" -> No.)
- **Is it for ME?** (e.g., "Can you fix this?" -> Yes. "I fixed this" -> No.)
- **Is it new?** (Checks Notion history to avoid duplicates.)
- **Is it wanted?** (Checks "Rejected" history to filter spammy requests.)

If the message passes, a Task is created in Notion with a **Priority Score (1-10)**.

### 3. The Dashboard
Runs locally at **http://localhost:8000**.
- **Real-time Sync**: Changes in the dashboard (Done/Reopen) update Notion instantly.
- **Toast Notifications**: Get feedback on every action.

---

## 🏃‍♂️ Daily Usage

1.  **Start the Agent**: `python main.py`
2.  **Send a Task**: Open Telegram -> Saved Messages -> Type "Buy coffee".
3.  **Check Notion**: The task appears in seconds.
4.  **Complete it**: Click **Done** on the Dashboard.

## 🍏 Auto-Start (Mac Only)

To make the agent start automatically when you login:

1.  **Copy the plist file**:
    ```bash
    cp org.jzbnb.telegram-agent.plist ~/Library/LaunchAgents/
    ```
2.  **Load the service**:
    ```bash
    launchctl load ~/Library/LaunchAgents/org.jzbnb.telegram-agent.plist
    ```
3.  **Check status**:
    The agent will now run in the background. Logs are available at `agent.log` and `agent.err` in the project folder.

## 🏗️ Architecture

- **`main.py`**: Orchestrator running concurrent Listener and Server.
- **`listener.py`**: Telegram Client (Pyrogram). Handles message events, filters, and passes memory context.
- **`agent.py`**: Intelligence Engine. Uses `system_prompt.txt` (Jinja2) to prompt Gemini.
- **`notion_sync.py`**: Handling all Notion API interactions (Search, Create, Update).
- **`server.py`**: FastAPI backend for the Dashboard.

## 🛡️ Security
- **Local Only**: No data is sent to us.
- **Open Source**: Verify the code yourself.
- **Secure Storage**: Credentials in `.env`, Session in memory.

## 📄 License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
