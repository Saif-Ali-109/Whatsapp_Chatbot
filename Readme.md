# WhatsApp Chatbot Backend (Flask + WhatsApp Cloud API)

## Overview
This project is a backend automation system for WhatsApp using **Python Flask** and the **WhatsApp Cloud API**. It allows your WhatsApp number to automatically receive messages and send automated replies.

This project is designed to be **shared publicly**, with sensitive credentials handled via environment variables so users can safely run their own instances.

---

## Features Implemented
- Flask server acting as a **webhook** for WhatsApp messages.
- Webhook **verification** with a custom verify token.
- Receiving messages from any sender who messages your **WhatsApp test number**.
- Printing incoming messages in the terminal.
- Sending automated responses back to the sender.
- Integration with **ngrok** for local development.
- Running via **uv** (Uvicorn wrapper) inside a **virtual environment**.

---

## Technologies Used
- Python 3.x
- Flask
- Requests library
- ngrok (for public URL during development)
- uv (Uvicorn wrapper for ASGI server)
- python-dotenv
- Python virtual environment (venv)

---

## Project Setup

### 1. Clone the repository
```bash
git clone https://github.com/Saif-Ali-109/Whatsapp_Chatbot.git
cd whatsapp_chatbot
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv || uv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your `.env` file
Create a file named `.env` in the root directory with the following content:
```
ACCESS_TOKEN=your_whatsapp_access_token_here
PHONE_NUMBER_ID=your_whatsapp_number_id_here
VERIFY_TOKEN=your_secret_verify_token_here
```
> **Important:** Do not share your `.env` file publicly.

### 5. Run Flask server using uv
```bash
uv run main.py
```
Server will run on: `http://127.0.0.1:5000`

### 6. Expose Flask locally using ngrok
```bash
ngrok http 5000
```
- Copy the generated **Forwarding URL** as your WhatsApp Webhook URL.

### 7. Set up WhatsApp Webhook in Meta Developer
1. Go to [Meta Developer Dashboard](https://developers.facebook.com/apps) → Your App → WhatsApp → Webhooks
2. Add your **ngrok forwarding URL** and your **verify token**
3. Subscribe to the **messages** field.
4. Verify the webhook.

---

## How it Works
1. WhatsApp sends incoming messages to the webhook URL.
2. Flask server receives the request and prints the message data in the terminal:
```python
From: <sender_number>
Message: <message_text>
```
3. The bot automatically replies to the sender with the received message.

---

## Notes for Users
- You must **create your own `.env` file** with your WhatsApp Cloud API credentials.  
- Users must set up their **own webhook URL** in Meta Developer.  
- Messages from any sender to your test number will trigger the webhook.  
- Use **uv** or **uvicorn** to run the server inside your virtual environment.  
- `.env` should never be published or uploaded to GitHub.  
- Add `.env` and `.venv` to `.gitignore` to keep them private:
```
# .gitignore
.venv
.env
```

---

## Next Steps / To-Do
- Implement more advanced **automated replies** using AI.
- Handle **multiple senders** dynamically.
- Add a **frontend interface** to view incoming messages and send replies.
- Deploy to **cloud hosting** (Heroku, AWS, etc.) for 24/7 operation.

---

## References
- [WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [ngrok Documentation](https://ngrok.com/docs)
- [Uvicorn Documentation](https://www.uvicorn.org/)

---

## Installing Dependencies
- Generate `requirements.txt` for all users to install dependencies:
```bash
pip freeze > requirements.txt
```
- Then users can install:
```bash
pip install -r requirements.txt
```
This ensures all necessary libraries (`Flask`, `requests`, `python-dotenv`, `uv`) are installed properly.

