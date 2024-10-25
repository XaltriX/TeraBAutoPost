import logging
import asyncio
import time
import re
from pyrogram import Client, errors
from pyrogram.raw import functions, types
from pyrogram.enums import ChatType

# Disable default logging
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Your API ID and API HASH
API_ID = "24955235"
API_HASH = "f317b3f7bbe390346d8b46868cff0de8"

class Stats:
    def __init__(self):
        self.total_requests = 0
        self.approved = 0
        self.failed = 0
        self.dismissed = 0
        self.start_time = time.time()

    def print_stats(self):
        elapsed_time = time.time() - self.start_time
        stats_str = (
            f"\r📊 Stats: ✅ {self.approved} | ❌ {self.failed} | 🚫 {self.dismissed} | "
            f"⏱️ {elapsed_time:.2f}s | 💯 {self.total_requests}"
        )
        print(stats_str, end='', flush=True)

async def handle_request(app, chat_id, user_id, stats):
    try:
        await app.approve_chat_join_request(chat_id, user_id)
        stats.approved += 1
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        return False
    except errors.UserAlreadyParticipant:
        pass
    except errors.UserChannelsTooMuch:
        await dismiss_request(app, chat_id, user_id, stats)
    except Exception:
        stats.failed += 1
    finally:
        stats.total_requests += 1
    return True

async def dismiss_request(app, chat_id, user_id, stats):
    try:
        await app.decline_chat_join_request(chat_id, user_id)
        stats.dismissed += 1
    except Exception:
        stats.failed += 1

async def get_channel_info(app, identifier, max_retries=3):
    for attempt in range(max_retries):
        try:
            if re.match(r'https?://t\.me/(\+|joinchat/)\w+', identifier) or identifier.startswith('+') or identifier.startswith('joinchat/'):
                chat = await app.join_chat(identifier)
            else:
                chat = await app.get_chat(identifier)
            return chat
        except errors.FloodWait as e:
            await asyncio.sleep(e.value)
        except (errors.InviteHashExpired, errors.InviteHashInvalid, errors.ChannelPrivate):
            return None
        except errors.UserAlreadyParticipant:
            return await app.get_chat(identifier)
        except Exception:
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(2 ** attempt)
    return None

async def auto_approve(app, chat, stats):
    print(f"🚀 Auto-approving for: {chat.title} (ID: {chat.id})")
    last_update = 0
    request_queue = asyncio.Queue()
    
    async def process_requests():
        while True:
            request = await request_queue.get()
            await handle_request(app, chat.id, request.user.id, stats)
            await asyncio.sleep(0.2)  # 5 requests per second
            request_queue.task_done()

    # Start 5 worker tasks
    workers = [asyncio.create_task(process_requests()) for _ in range(5)]

    try:
        while True:
            try:
                async for request in app.get_chat_join_requests(chat.id):
                    await request_queue.put(request)
                    if time.time() - last_update >= 2:
                        stats.print_stats()
                        last_update = time.time()
            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
            except errors.ChatAdminRequired:
                print("\n❌ Error: Admin rights required.")
                break
            except Exception as e:
                print(f"\n⚠️ Error: {str(e)}")
                await asyncio.sleep(5)
    finally:
        # Cancel worker tasks
        for worker in workers:
            worker.cancel()
        # Wait for all workers to complete
        await asyncio.gather(*workers, return_exceptions=True)

async def main():
    app = Client("my_account", api_id=API_ID, api_hash=API_HASH)
    
    try:
        async with app:
            # Synchronize time with Telegram servers
            for _ in range(5):  # Try up to 5 times
                try:
                    await app.invoke(functions.Ping(ping_id=0))
                    break
                except errors.BadMsgNotification as e:
                    if e.error_code != 17:
                        raise
                    # Get the server time
                    result = await app.invoke(functions.help.GetConfig())
                    server_time = result.date
                    # Calculate the time difference
                    time_diff = server_time - int(time.time())
                    # Apply the time difference
                    app.set_parse_mode("html", time_offset=time_diff)
                    print(f"Applied time offset of {time_diff} seconds")
            
            me = await app.get_me()
            print(f"🔓 Logged in as {me.first_name} ({me.id})")
            
            while True:
                identifier = input("Enter channel username/invite link (or 'q' to quit): ")
                if identifier.lower() == 'q':
                    break
                
                chat = await get_channel_info(app, identifier)
                if chat:
                    if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                        print("❌ Error: Not a channel or supergroup.")
                        continue
                    stats = Stats()
                    await auto_approve(app, chat, stats)
                    print("\n✅ Auto-approve completed.")
                else:
                    print("❌ Channel access failed. Check the link and try again.")
    except errors.AuthKeyUnregistered:
        print("🔑 Session expired. Delete 'my_account.session' and rerun.")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
