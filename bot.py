import telebot
import os
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Your Telegram Bot API token
TOKEN = '7929715633:AAGTuiSgJ-VVkEtF-8SkDCAGt40vMIq5MDs'

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Allowed user (your Telegram username without '@')
ALLOWED_USER = 'xaltrix'

# Channel configuration - setting default channel ID
channel_config = {
    'enabled': True,  # Enable autoposting by default
    'channel_id': -1002491007435  # Your channel ID
}

def is_user_allowed(message):
    user = bot.get_chat(message.chat.id)
    if user.username != ALLOWED_USER:
        bot.send_message(message.chat.id, "This is a personal bot. If you want to make your own bot, please contact the developer @xaltrix.")
        return False
    return True

def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Cancel'))
    return keyboard

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("TeraBox Editor"),
        KeyboardButton("Channel Settings")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start_message(message):
    if not is_user_allowed(message):
        return
    bot.send_message(
        message.chat.id, 
        "Welcome! Choose an option:",
        reply_markup=get_main_keyboard()
    )

def post_to_channel(content_type, file_id, caption, keyboard):
    try:
        if content_type == 'text':
            bot.send_message(
                channel_config['channel_id'],
                caption,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        elif content_type == 'photo':
            bot.send_photo(
                channel_config['channel_id'],
                file_id,
                caption=caption,
                reply_markup=keyboard
            )
        elif content_type == 'video':
            bot.send_video(
                channel_config['channel_id'],
                file_id,
                caption=caption,
                reply_markup=keyboard
            )
        elif content_type == 'document':
            bot.send_document(
                channel_config['channel_id'],
                file_id,
                caption=caption,
                reply_markup=keyboard
            )
        return True, "Posted successfully"
    except Exception as e:
        return False, f"Error posting to channel: {str(e)}"

def process_single_post(message):
    user_id = message.chat.id
    
    text = message.text if message.content_type == 'text' else message.caption
    
    if not text:
        bot.send_message(user_id, "Please provide text or caption with TeraBox links.")
        return
    
    terabox_links = re.findall(r'https?://\S*terabox\S*', text, re.IGNORECASE)
    if not terabox_links:
        bot.send_message(user_id, "No valid TeraBox link found in the message.")
        return

    formatted_caption = (
        f"⚝─────⭒─⭑─⭒──────⚝\n"
        "  👉  ​🇼​​🇪​​🇱​​🇨​​🇴​​🇲​​🇪​❗ 👈\n"
        " ⚝─────⭒─⭑─⭒──────⚝\n\n"
        "≿━━━━━━━༺❀༻━━━━━━≾\n"
        f"📥  𝐉𝐎𝐈𝐍 𝐔𝐒 :– @NeonGhost_Network\n"
        "≿━━━━━━━༺❀༻━━━━━━≾\n\n"
    )

    if len(terabox_links) == 1:
        formatted_caption += f"➽───❥🔗𝐅𝐮𝐥𝐥 𝐕𝐢𝐝𝐞𝐨 𝐋𝐢𝐧𝐤:🔗 {terabox_links[0]}\n\n"
    else:
        for idx, link in enumerate(terabox_links, start=1):
            formatted_caption += f"➽───❥🔗𝐕𝐢𝐝𝐞𝐨 𝐋𝐢𝐧𝐤 {idx}:🔗 {link}\n\n"

    formatted_caption += "─❚█═𝑩𝒚 𝑵𝒆𝒐𝒏𝑮𝒉𝒐𝒔𝒕 𝑵𝒆𝒕𝒘𝒐𝒓𝒌𝒔═█❚─"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("How To Watch & Download 🔞", url="https://t.me/HTDTeraBox/5"))
    keyboard.add(InlineKeyboardButton("18+ Bot🔞", url="https://t.me/NightLifeRobot"))
    keyboard.add(InlineKeyboardButton("Movie Group", url="https://t.me/+Xs8osVK7iX81Yjc0"))

    try:
        # Send to user first
        if message.content_type == 'text':
            bot.send_message(user_id, formatted_caption, reply_markup=keyboard, disable_web_page_preview=True)
            file_id = None
            content_type = 'text'
        else:
            if message.content_type == 'photo':
                file_id = message.photo[-1].file_id
                bot.send_photo(user_id, file_id, caption=formatted_caption, reply_markup=keyboard)
                content_type = 'photo'
            elif message.content_type == 'video':
                file_id = message.video.file_id
                bot.send_video(user_id, file_id, caption=formatted_caption, reply_markup=keyboard)
                content_type = 'video'
            elif message.content_type == 'document' and message.document.mime_type == 'image/gif':
                file_id = message.document.file_id
                bot.send_document(user_id, file_id, caption=formatted_caption, reply_markup=keyboard)
                content_type = 'document'
        
        # Post to channel
        success, msg = post_to_channel(content_type, file_id, formatted_caption, keyboard)
        if not success:
            bot.send_message(user_id, f"Error posting to channel: {msg}")
        else:
            bot.send_message(user_id, "✅ Successfully posted to channel!")
                
    except Exception as e:
        bot.send_message(user_id, f"Error processing post: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_user_allowed(message):
        return
        
    if message.text == "TeraBox Editor":
        msg = bot.send_message(
            message.chat.id, 
            "Send your posts (text or media with TeraBox links). Type 'Cancel' to exit.",
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(message, handle_terabox_media)
    elif message.text == "Channel Settings":
        status = "Enabled" if channel_config['enabled'] else "Disabled"
        bot.send_message(
            message.chat.id,
            f"Channel Settings:\n\nAutoposting: {status}\nChannel ID: {channel_config['channel_id']}",
            reply_markup=get_main_keyboard()
        )
    elif message.text == "Cancel":
        start_message(message)

def handle_terabox_media(message):
    if not is_user_allowed(message):
        return
    if message.text == "Cancel":
        start_message(message)
        return
        
    if message.content_type in ['photo', 'video', 'document']:
        if message.caption:
            process_single_post(message)
    elif message.content_type == 'text':
        process_single_post(message)
    
    # Continue listening for more posts
    bot.register_next_step_handler(message, handle_terabox_media)

@bot.message_handler(content_types=['photo', 'video', 'document'])
def handle_media(message):
    if not is_user_allowed(message):
        return
    handle_terabox_media(message)

def main():
    try:
        print("Bot started...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Bot stopped due to error: {e}")
        main()

if __name__ == "__main__":
    main()
