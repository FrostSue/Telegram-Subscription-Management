import datetime
import math
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import idle
from bot.client import SubscriptionBot
from utils.formatters import ListFormatter

logging.basicConfig(level=logging.INFO)

async def auto_billing_job(bot: SubscriptionBot):
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    
    try:
        with bot.manager.cursor() as cursor:
            cursor.execute("SELECT chat_id FROM group_settings")
            chats = [row["chat_id"] for row in cursor.fetchall()]
    except Exception:
        return
        
    for chat_id in chats:
        try:
            subs = bot.subscription_repo.get_subscriptions_with_members(chat_id)
            if not subs:
                continue
                
            bot.user_billing_repo.delete_billings_for_month(chat_id, year, month)
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
                continue
                
            for uid, data in user_shares.items():
                billing_id = bot.user_billing_repo.create_billing(
                    chat_id=chat_id,
                    user_id=uid,
                    username=data["username"],
                    amount=data["total"],
                    year=year,
                    month=month
                )
                for item in data["subscriptions"]:
                    bot.user_billing_repo.link_billing_subscription(
                        user_billing_id=billing_id,
                        subscription_id=item["id"],
                        title=item["title"],
                        short_code=item["short_code"],
                        individual_amount=item["amount"]
                    )
            
            billings = bot.user_billing_repo.get_billings_for_month(chat_id, year, month)
            settings = bot.group_settings_repo.get_or_create(chat_id)
            formatted_text = ListFormatter.format_billing_list(billings, subs, settings, year, month)
            
            sent_msg = await bot.send_message(chat_id, formatted_text)
            bot.bill_message_repo.save_message_id(chat_id, year, month, sent_msg.id)
        except Exception:
            pass

async def main():
    bot = SubscriptionBot()
    await bot.start()
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        auto_billing_job,
        "cron",
        day=16,
        hour=0,
        minute=0,
        args=[bot]
    )
    scheduler.start()
    
    logging.info("Subscription Bot is running and scheduler is active.")
    await idle()
    
    scheduler.shutdown()
    await bot.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
