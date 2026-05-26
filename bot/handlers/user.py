from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from utils.validators import CommandValidator
from utils.formatters import ListFormatter

@Client.on_message(filters.command("paid"))
async def paid_command(client: Client, message: Message):
    if not message.chat or not message.from_user:
        return
        
    args = message.command[1:]
    try:
        billing_id = CommandValidator.parse_paid_unpaid(args, "paid")
    except ValueError as e:
        await message.reply_text(str(e))
        return

    billing = client.user_billing_repo.get_billing_by_id(message.chat.id, billing_id)
    if not billing:
        await message.reply_text("Billing ID not found or does not belong to this group.")
        return

    is_admin = False
    if message.chat.type.name not in ["PRIVATE", "BOT"]:
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                is_admin = True
        except Exception:
            pass

    if not is_admin and billing["user_id"] != message.from_user.id:
        await message.reply_text("You can only mark your own bills as paid.")
        return

    success = client.user_billing_repo.update_payment_status(message.chat.id, billing_id, 1)
    if success:
        await message.reply_text(f"Billing ID {billing_id} marked as Paid.")
        
        year, month = billing["year"], billing["month"]
        billings = client.user_billing_repo.get_billings_for_month(message.chat.id, year, month)
        subs = client.subscription_repo.get_subscriptions_with_members(message.chat.id)
        settings = client.group_settings_repo.get_or_create(message.chat.id)
        
        formatted_text = ListFormatter.format_billing_list(billings, subs, settings, year, month)
        msg_id = client.bill_message_repo.get_message_id(message.chat.id, year, month)
        if msg_id:
            try:
                await client.edit_message_text(message.chat.id, msg_id, formatted_text)
            except Exception:
                pass
    else:
        await message.reply_text("Failed to update payment status.")
