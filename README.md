# TT1 – Route & ETA Chatbot (Telegram) using OpenStreetMap Services

This repository contains the implementation of **TT1 (Thực tập 1)** – a Python-based Telegram chatbot that helps users **find routes and estimate travel time (ETA)** between two locations through a guided conversation.

The chatbot integrates **OpenStreetMap-based services** and is designed with a **Finite State Machine (FSM)** to ensure a clear and robust interaction flow.

---

## Project Context

- **Course**: Thực tập 1 (TT1) – Master Program, HCMUT  
- **Major**: Computer Science  
- **Type**: Individual academic project  
- **Focus**: Python backend, API integration, conversation flow design

This project emphasizes **system implementation and API orchestration**, rather than machine learning.

---

## System Architecture

<p align="center">
  <img src="assets/system-architecture.png" width="800">
</p>

---

## Chatbot Demo

### 1. Start & command usage
<img src="assets/demo-01-start.png" width="480"/>

### 2. Location disambiguation (top-3 candidates)
<img src="assets/demo-03-candidates.png" width="480"/>

### 3. Route result & ETA
<img src="assets/demo-07-result.png" width="480"/>

### 4. OpenStreetMap route visualization
<img src="assets/demo-08-osm-map.png" width="90%"/>


---

## Key Features

- Step-by-step route collection using chat commands
- FSM-based conversation control
- Top-3 location candidates for ambiguous user input
- Distance and ETA calculation via OSRM
- OpenStreetMap direction link generation
- Graceful handling of invalid or cancelled requests

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create environment configuration

Create a file named `.env` in the project root with the following content:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

> **Note:** Do not commit the `.env` to GitHub. It is intentionally ignored.

### 3. Run the bot

```bash
python main.py
```

