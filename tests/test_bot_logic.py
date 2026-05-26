import unittest
import math
import tempfile
import os
from db.connection import ConnectionManager
from db.database import initialize_database
from db.repositories import (
    GroupSettingsRepository,
    SubscriptionRepository,
    UserBillingRepository
)
from utils.formatters import ListFormatter
from utils.validators import CommandValidator

class TestSubscriptionBotLogic(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.manager = ConnectionManager(self.db_path)
        initialize_database(self.manager)
        
        self.group_repo = GroupSettingsRepository(self.manager)
        self.sub_repo = SubscriptionRepository(self.manager)
        self.billing_repo = UserBillingRepository(self.manager)

    def tearDown(self):
        self.manager.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_database_initialization(self):
        settings = self.group_repo.get_or_create(111)
        self.assertEqual(settings["chat_id"], 111)
        self.assertEqual(settings["currency"], "USD")
        self.assertEqual(settings["billing_day"], 16)

    def test_cost_splitting_math_and_ceiling(self):
        cost = 100.0
        discount = 11.0
        member_count = 3
        
        individual_share = math.ceil((cost - discount) / member_count)
        self.assertEqual(individual_share, 30)

        cost = 24.75
        discount = 0.0
        member_count = 1
        individual_share = math.ceil((cost - discount) / member_count)
        self.assertEqual(individual_share, 25)

    def test_strict_multi_group_isolation(self):
        chat_a = 12345
        chat_b = 67890
        
        self.group_repo.get_or_create(chat_a)
        self.group_repo.get_or_create(chat_b)
        
        sub_id_a = self.sub_repo.add_subscription(chat_a, "Netflix", "NF", 100.0, 0.0)
        sub_id_b = self.sub_repo.add_subscription(chat_b, "Spotify", "SP", 50.0, 0.0)
        
        subs_a = self.sub_repo.get_subscriptions(chat_a)
        subs_b = self.sub_repo.get_subscriptions(chat_b)
        
        self.assertEqual(len(subs_a), 1)
        self.assertEqual(subs_a[0]["title"], "Netflix")
        
        self.assertEqual(len(subs_b), 1)
        self.assertEqual(subs_b[0]["title"], "Spotify")
        
        member_added = self.sub_repo.add_member(chat_a, sub_id_b, 999, "@user")
        self.assertFalse(member_added)
        
        members_a = self.sub_repo.get_members(chat_a, sub_id_b)
        self.assertEqual(len(members_a), 0)

    def test_command_parser_validation(self):
        title, cost, discount = CommandValidator.parse_add_sub(["Spotify", "120.5", "10"])
        self.assertEqual(title, "Spotify")
        self.assertEqual(cost, 120.5)
        self.assertEqual(discount, 10.0)
        
        with self.assertRaises(ValueError):
            CommandValidator.parse_add_sub(["Spotify"])
            
        with self.assertRaises(ValueError):
            CommandValidator.parse_add_sub(["Spotify", "-10"])

    def test_list_formatter_html_rendering(self):
        settings = {
            "chat_id": 123,
            "currency": "TRY",
            "iban": "TR1234",
            "iban_name": "John Doe"
        }
        
        billings = [
            {
                "id": 1,
                "username": "@alice",
                "amount": 25,
                "is_paid": 0,
                "subscriptions": [{"short_code": "SP"}]
            },
            {
                "id": 2,
                "username": "@bob",
                "amount": 50,
                "is_paid": 1,
                "subscriptions": [{"short_code": "SP"}, {"short_code": "NF"}]
            }
        ]
        
        subs = [
            {
                "title": "Spotify",
                "short_code": "SP",
                "cost": 50.0,
                "discount": 0.0,
                "members": [{"user_id": 1, "username": "@alice"}, {"user_id": 2, "username": "@bob"}]
            }
        ]
        
        formatted = ListFormatter.format_billing_list(billings, subs, settings, 2026, 5)
        
        self.assertIn("📅 May 2026 Billing List", formatted)
        self.assertIn("1. @alice - 25 TRY [SP] (Unpaid) (ID: 1)", formatted)
        self.assertIn("<s>2. @bob - 50 TRY [SP, NF] (Paid) (ID: 2)</s>", formatted)
        self.assertIn("IBAN: <code>TR1234</code>", formatted)
        self.assertIn("Name: John Doe", formatted)

if __name__ == "__main__":
    unittest.main()
