import logging
from pyrogram import Client, filters
from pyrogram.types import Message

@Client.on_message(filters.all, group=-1)
async def log_incoming_message(client: Client, message: Message):
    logging.info(f"Full message object: {str(message)}")

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    welcome_text = (
        "<b>Welcome to the Subscription Management Bot!</b>\n\n"
        "This bot helps groups split subscription costs, track monthly payments, and coordinate bank transfers easily.\n\n"
        "Use /help to see all available commands."
    )
    await message.reply_text(welcome_text)

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    help_text = (
        "<b>💡 Available Commands:</b>\n\n"
        "<b>User Commands:</b>\n"
        "/paid &lt;billing_id&gt; - Mark your monthly bill as paid.\n\n"
        "<b>Admin Commands:</b>\n"
        "/add_sub &lt;title&gt; &lt;cost&gt; [discount] - Register a new subscription.\n"
        "/add_member &lt;sub_id&gt; &lt;username&gt; - Assign a member to a subscription.\n"
        "/remove_member &lt;sub_id&gt; &lt;username&gt; - Unassign a member from a subscription.\n"
        "/set_iban &lt;iban&gt; &lt;account_holder_name&gt; - Update group bank transfer details.\n"
        "/set_currency &lt;currency_symbol&gt; - Set group's display currency.\n"
        "/set_debt &lt;billing_id&gt; &lt;new_amount&gt; - Manually adjust a member's bill.\n"
        "/unpaid &lt;billing_id&gt; - Revert a payment status to unpaid.\n"
        "/billing [month] [year] - Generate consolidated billing list for the month.\n"
        "/help - Display this help manual."
    )
    await message.reply_text(help_text)
