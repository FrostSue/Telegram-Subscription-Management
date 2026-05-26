from pyrogram import Client
from config import settings
from db.connection import ConnectionManager
from db.database import initialize_database
from db.repositories import (
    GroupSettingsRepository,
    SubscriptionRepository,
    UserBillingRepository,
    MonthlyBillMessageRepository
)

class SubscriptionBot(Client):
    def __init__(self):
        super().__init__(
            name="tgsubsbot",
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            bot_token=settings.BOT_TOKEN,
            plugins=dict(root="bot/handlers")
        )
        self.manager = ConnectionManager(settings.DATABASE_PATH)
        self.group_settings_repo = GroupSettingsRepository(self.manager)
        self.subscription_repo = SubscriptionRepository(self.manager)
        self.user_billing_repo = UserBillingRepository(self.manager)
        self.bill_message_repo = MonthlyBillMessageRepository(self.manager)

    async def start(self):
        initialize_database(self.manager)
        await super().start()

    async def stop(self, *args, **kwargs):
        await super().stop(*args, **kwargs)
