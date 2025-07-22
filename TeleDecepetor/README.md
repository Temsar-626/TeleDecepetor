# TeleDeceptor

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Flask-2.0+-green.svg" alt="Flask 2.0+">
  <img src="https://img.shields.io/badge/Telethon-1.24+-red.svg" alt="Telethon 1.24+">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</div>

<div align="center">
  <h3>🚨 FOR EDUCATIONAL PURPOSES ONLY 🚨</h3>
  <p><b>Use responsibly. Unauthorized access to accounts is illegal and unethical.</b></p>
</div>

<p align="center">
  <a href="README_FA.md">🇮🇷 Persian Documentation (مستندات فارسی)</a>
</p>

## 🔍 Overview

TeleDeceptor is an advanced Telegram session harvester that demonstrates potential vulnerabilities in two-factor authentication flows. This project serves as an educational tool to understand social engineering techniques and improve security awareness.

The system uses a Flask web application to create a convincing Telegram login interface that collects and forwards authentication data to an administrator's bot.

## ✨ Key Features

- 🌐 Realistic Telegram login page simulation
- 📱 Phone number verification process
- 🔑 2FA password collection system
- 🔄 Session management and termination
- 👤 Admin notification system via Telegram bot
- 📊 IP address and user agent logging
- 🔐 2FA password setter (configurable)
- 🌍 Country code selection

## 🛡️ Advanced Capabilities

TeleDeceptor provides operators with powerful session manipulation tools:

- **Full Session Hijacking**: Capture and use valid Telegram sessions without detection
- **Message Interception**: Read incoming verification codes and messages in real-time
- **Silent Account Access**: Monitor target accounts without triggering notifications
- **Remote Session Management**: Control multiple hijacked sessions from a single admin interface
- **Automated 2FA Bypass**: Attempt to set custom 2FA passwords during login process
- **Session Persistence**: Maintain access even after target user logout attempts
- **Cross-Device Takeover**: Terminate other sessions to make yours the only valid one
- **Forensic Counter-Measures**: Leave minimal logs on target's device
- **Real-Time Alerts**: Instant notifications when new sessions are captured
- **User Profiling**: Collect device info, IP addresses, and user agents
- **Seamless Session Transfer**: Convert session strings for use in other tools or bots
- **Selective Termination**: End specific sessions while maintaining others

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Telegram API credentials (API_ID and API_HASH)
- Telegram Bot Token (for admin notifications)

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/teledeceptor.git
cd teledeceptor
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your credentials:
```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
```

## 🚀 Usage

1. Start the application:
```bash
python app.py
```

2. Access the web interface at `http://localhost:5000`

3. Admin commands will be available through your Telegram bot with these actions:
   - 🔑 Get Login Code
   - 📱 Get Phone Info
   - ❌ Terminate Session
   - 🔄 Reset Sessions

## 🔧 How It Works

1. **User Interaction**: Target enters phone number on fake login page
2. **Code Request**: System requests verification code from Telegram
3. **Code Collection**: Target enters the code they received
4. **2FA Handling**: If 2FA is enabled, password is requested
5. **Session Capture**: Valid session is captured and sent to admin
6. **Session Management**: Admin can interact with the captured session

## 📚 Project Structure

```
teledeceptor/
├── app.py              # Main application file
├── templates/          # HTML templates
│   ├── index.html      # Login page
│   ├── code.html       # Verification code page
│   ├── 2fa.html        # 2FA password page
│   └── success.html    # Success page
├── static/             # Static assets
│   ├── css/            # Stylesheets
│   └── img/            # Images
├── .env                # Environment variables
└── README.md           # Documentation
```

## ⚠️ Security Considerations & Legal Disclaimer

This project is provided STRICTLY FOR EDUCATIONAL PURPOSES to demonstrate how phishing attacks work. Using this software to gain unauthorized access to accounts is:

- 🚫 Illegal in most jurisdictions
- 🚫 A violation of Telegram's Terms of Service
- 🚫 Unethical and an invasion of privacy

The developers assume NO LIABILITY for misuse of this software. Use responsibly for educational purposes only.

## 🤝 Contributing

Contributions to enhance the educational value of this project are welcome. Please feel free to submit a pull request or open an issue.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 