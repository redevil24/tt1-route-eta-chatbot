# TT1 – Route & ETA Chatbot

Chatbot Telegram hỗ trợ tìm đường và ước tính thời gian di chuyển (ETA),
sử dụng FSM và các dịch vụ bản đồ OpenStreetMap.

## Features
- Multi-turn conversation (FSM)
- Geocoding: Nominatim
- Routing: OSRM (public)
- Telegram Bot interface

## Tech Stack
- Python
- python-telegram-bot
- OpenStreetMap APIs

## Run
```bash
pip install -r requirements.txt
python main.py
