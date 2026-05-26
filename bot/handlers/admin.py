import math
from pyrogram import Client, filters
from pyrogram.types import Message
from bot.middlewares.auth import requires_admin
from utils.validators import CommandValidator
from utils.formatters import ListFormatter

@Client.on_message(filters.command("add_sub"))
@requires_admin
async def add_sub_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        title, cost, discount = CommandValidator.parse_add_sub(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    short_code = "".join([word[0] for word in title.split() if word])[:3].upper()
    if not short_code:
        short_code = title[:2].upper()

    try:
        sub_id = client.subscription_repo.add_subscription(
            chat_id=message.chat.id,
            title=title,
            short_code=short_code,
            cost=cost,
            discount=discount
        )
        await message.reply_text(
            f"Subscription added successfully!\n"
            f"ID: {sub_id}\n"
            f"Title: {title}\n"
            f"Short Code: [{short_code}]\n"
            f"Cost: {cost}\n"
            f"Discount: {discount}"
        )
    except Exception:
        await message.reply_text("Failed to add subscription. Title or short code might already exist.")

@Client.on_message(filters.command("add_member"))
@requires_admin
async def add_member_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        sub_id, username = CommandValidator.parse_add_member(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    try:
        user = await client.get_users(username)
        user_id = user.id
    except Exception:
        await message.reply_text("Could not resolve username to a valid Telegram user.")
        return

    success = client.subscription_repo.add_member(
        chat_id=message.chat.id,
        subscription_id=sub_id,
        user_id=user_id,
        username=username
    )
    
    if success:
        member_id = client.group_members_repo.get_or_create_member_id(
            chat_id=message.chat.id,
            user_id=user_id,
            username=username
        )
        await message.reply_text(f"User {username} added to subscription {sub_id} successfully!\nStable Member ID: {member_id}")
    else:
        await message.reply_text("Failed to add member. Check if subscription ID exists and belongs to this group.")

@Client.on_message(filters.command("remove_member"))
@requires_admin
async def remove_member_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        sub_id, username = CommandValidator.parse_remove_member(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    try:
        user = await client.get_users(username)
        user_id = user.id
    except Exception:
        await message.reply_text("Could not resolve username to a valid Telegram user.")
        return

    success = client.subscription_repo.remove_member(
        chat_id=message.chat.id,
        subscription_id=sub_id,
        user_id=user_id
    )
    
    if success:
        await message.reply_text(f"User {username} removed from subscription {sub_id} successfully.")
    else:
        await message.reply_text("Failed to remove member. Check if subscription ID exists and member is assigned.")

@Client.on_message(filters.command("set_iban"))
@requires_admin
async def set_iban_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        iban, name = CommandValidator.parse_set_iban(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    client.group_settings_repo.update_iban(message.chat.id, iban, name)
    await message.reply_text(
        f"IBAN settings updated successfully!\n"
        f"IBAN: <code>{iban}</code>\n"
        f"Name: {name}"
    )

@Client.on_message(filters.command("set_currency"))
@requires_admin
async def set_currency_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        currency = CommandValidator.parse_set_currency(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    client.group_settings_repo.update_currency(message.chat.id, currency)
    await message.reply_text(f"Currency updated to {currency} successfully.")

async def get_active_billing_by_member(client: Client, chat_id: int, member_id: int):
    user_id = client.group_members_repo.get_user_id_by_member_id(chat_id, member_id)
    if not user_id:
        return None, None
    with client.manager.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM user_billing WHERE chat_id = ? AND user_id = ? ORDER BY year DESC, month DESC LIMIT 1",
            (chat_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            return None, None
        billing_id = row["id"]
    return client.user_billing_repo.get_billing_by_id(chat_id, billing_id), billing_id

@Client.on_message(filters.command("set_debt"))
@requires_admin
async def set_debt_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        member_id, amount = CommandValidator.parse_set_debt(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    billing, billing_id = await get_active_billing_by_member(client, message.chat.id, member_id)
    if not billing:
        await message.reply_text("Member ID not found or has no active bills.")
        return

    success = client.user_billing_repo.update_billing_amount(message.chat.id, billing_id, amount)
    if success:
        await message.reply_text(f"Member ID {member_id} amount updated to {amount} successfully.")
        
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
        await message.reply_text("Failed to update debt.")

@Client.on_message(filters.command("unpaid"))
@requires_admin
async def unpaid_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        member_id = CommandValidator.parse_paid_unpaid(args, "unpaid")
    except ValueError as e:
        await message.reply_text(str(e))
        return

    billing, billing_id = await get_active_billing_by_member(client, message.chat.id, member_id)
    if not billing:
        await message.reply_text("Member ID not found or has no active bills.")
        return

    success = client.user_billing_repo.update_payment_status(message.chat.id, billing_id, 0)
    if success:
        await message.reply_text(f"Member ID {member_id} status updated to Unpaid.")
        
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
        await message.reply_text("Failed to revert payment status.")

@Client.on_message(filters.command("billing"))
@requires_admin
async def billing_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        year, month = CommandValidator.parse_billing(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    settings = client.group_settings_repo.get_or_create(message.chat.id)
    subs = client.subscription_repo.get_subscriptions_with_members(message.chat.id)

    if not subs:
        await message.reply_text("No subscriptions configured in this group.")
        return

    client.user_billing_repo.delete_billings_for_month(message.chat.id, year, month)
    user_shares = {}

    for sub in subs:
        members = sub["members"]
        members_count = len(members)
        if members_count == 0:
            continue
            
        if sub.get("manual_individual_amount") is not None:
            individual_amount = sub["manual_individual_amount"]
        else:
            individual_amount = math.ceil((sub["cost"] - sub["discount"]) / members_count)
        for member in members:
            uid = member["user_id"]
            uname = member["username"]
            
            if uid not in user_shares:
                user_shares[uid] = {
                    "username": uname,
                    "total": 0,
                    "subscriptions": []
                }
            
            user_shares[uid]["total"] += individual_amount
            user_shares[uid]["subscriptions"].append({
                "id": sub["id"],
                "title": sub["title"],
                "short_code": sub["short_code"],
                "amount": individual_amount
            })

    if not user_shares:
        await message.reply_text("No active members found in any subscription.")
        return

    for uid, data in user_shares.items():
        if data["username"].lower().lstrip('@') == "frostsue":
            continue

        client.group_members_repo.get_or_create_member_id(
            chat_id=message.chat.id,
            user_id=uid,
            username=data["username"]
        )

        billing_id = client.user_billing_repo.create_billing(
            chat_id=message.chat.id,
            user_id=uid,
            username=data["username"],
            amount=data["total"],
            year=year,
            month=month
        )
        
        for item in data["subscriptions"]:
            client.user_billing_repo.link_billing_subscription(
                user_billing_id=billing_id,
                subscription_id=item["id"],
                title=item["title"],
                short_code=item["short_code"],
                individual_amount=item["amount"]
            )

    billings = client.user_billing_repo.get_billings_for_month(message.chat.id, year, month)
    formatted_text = ListFormatter.format_billing_list(billings, subs, settings, year, month)
    
    sent_msg = await message.reply_text(formatted_text)
    client.bill_message_repo.save_message_id(message.chat.id, year, month, sent_msg.id)

@Client.on_message(filters.command("set_cost"))
@requires_admin
async def set_cost_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        sub_id, cost, discount = CommandValidator.parse_set_cost(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    success = client.subscription_repo.update_subscription_cost(
        chat_id=message.chat.id,
        subscription_id=sub_id,
        cost=cost,
        discount=discount
    )

    if success:
        await message.reply_text(
            f"Subscription ID {sub_id} cost updated successfully!\n"
            f"New Cost: {cost}\n"
            f"New Discount: {discount}\n\n"
            f"💡 Run /billing to regenerate the monthly bills under the new pricing."
        )
    else:
        await message.reply_text("Failed to update subscription cost. Check if Subscription ID exists.")

@Client.on_message(filters.command("set_individual_price"))
@requires_admin
async def set_individual_price_command(client: Client, message: Message):
    args = message.command[1:]
    try:
        sub_id, amount = CommandValidator.parse_set_individual_price(args)
    except ValueError as e:
        await message.reply_text(str(e))
        return

    success = client.subscription_repo.update_subscription_manual_individual_amount(
        chat_id=message.chat.id,
        subscription_id=sub_id,
        amount=amount
    )

    if success:
        if amount is not None:
            await message.reply_text(
                f"Subscription ID {sub_id} individual share price updated to {amount} successfully!\n\n"
                f"💡 Run /billing to regenerate the monthly bills under the new pricing."
            )
        else:
            await message.reply_text(
                f"Subscription ID {sub_id} individual share price has been reset to automatic calculation!\n\n"
                f"💡 Run /billing to regenerate the monthly bills under the new pricing."
            )
    else:
        await message.reply_text("Failed to update subscription individual price. Check if Subscription ID exists.")
