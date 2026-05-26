import math
from typing import List, Dict, Any, Optional
from db.connection import ConnectionManager

class GroupSettingsRepository:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    def get_or_create(self, chat_id: int) -> Dict[str, Any]:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM group_settings WHERE chat_id = ?",
                (chat_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            conn.execute(
                "INSERT INTO group_settings (chat_id) VALUES (?)",
                (chat_id,)
            )
            cursor = conn.execute(
                "SELECT * FROM group_settings WHERE chat_id = ?",
                (chat_id,)
            )
            return dict(cursor.fetchone())

    def update_iban(self, chat_id: int, iban: str, iban_name: str) -> None:
        with self.manager.transaction() as conn:
            self.get_or_create(chat_id)
            conn.execute(
                "UPDATE group_settings SET iban = ?, iban_name = ? WHERE chat_id = ?",
                (iban, iban_name, chat_id)
            )

    def update_currency(self, chat_id: int, currency: str) -> None:
        with self.manager.transaction() as conn:
            self.get_or_create(chat_id)
            conn.execute(
                "UPDATE group_settings SET currency = ? WHERE chat_id = ?",
                (currency, chat_id)
            )

    def update_billing_day(self, chat_id: int, billing_day: int) -> None:
        with self.manager.transaction() as conn:
            self.get_or_create(chat_id)
            conn.execute(
                "UPDATE group_settings SET billing_day = ? WHERE chat_id = ?",
                (billing_day, chat_id)
            )


class GroupMembersRepository:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    def get_or_create_member_id(self, chat_id: int, user_id: int, username: str) -> int:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT member_id, username FROM group_members WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id)
            )
            row = cursor.fetchone()
            if row:
                if row["username"] != username:
                    conn.execute(
                        "UPDATE group_members SET username = ? WHERE chat_id = ? AND user_id = ?",
                        (username, chat_id, user_id)
                    )
                return row["member_id"]

            cursor = conn.execute(
                "SELECT COALESCE(MAX(member_id), 0) as max_id FROM group_members WHERE chat_id = ?",
                (chat_id,)
            )
            max_id = cursor.fetchone()["max_id"]
            new_member_id = max_id + 1

            conn.execute(
                """
                INSERT INTO group_members (chat_id, user_id, username, member_id)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, user_id, username, new_member_id)
            )
            return new_member_id

    def get_user_id_by_member_id(self, chat_id: int, member_id: int) -> Optional[int]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM group_members WHERE chat_id = ? AND member_id = ?",
                (chat_id, member_id)
            )
            row = cursor.fetchone()
            return row["user_id"] if row else None

    def get_member_id_by_user_id(self, chat_id: int, user_id: int) -> Optional[int]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT member_id FROM group_members WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id)
            )
            row = cursor.fetchone()
            return row["member_id"] if row else None


class SubscriptionRepository:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    def add_subscription(
        self,
        chat_id: int,
        title: str,
        short_code: str,
        cost: float,
        discount: float = 0.0
    ) -> int:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO subscriptions (chat_id, title, short_code, cost, discount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, title, short_code.upper(), cost, discount)
            )
            return cursor.lastrowid

    def remove_subscription(self, chat_id: int, subscription_id: int) -> bool:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM subscriptions WHERE id = ? AND chat_id = ?",
                (subscription_id, chat_id)
            )
            return cursor.rowcount > 0

    def update_subscription_cost(
        self,
        chat_id: int,
        subscription_id: int,
        cost: float,
        discount: float = 0.0
    ) -> bool:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE subscriptions 
                SET cost = ?, discount = ? 
                WHERE id = ? AND chat_id = ?
                """,
                (cost, discount, subscription_id, chat_id)
            )
            return cursor.rowcount > 0

    def update_subscription_manual_individual_amount(
        self,
        chat_id: int,
        subscription_id: int,
        amount: Optional[int]
    ) -> bool:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE subscriptions 
                SET manual_individual_amount = ? 
                WHERE id = ? AND chat_id = ?
                """,
                (amount, subscription_id, chat_id)
            )
            return cursor.rowcount > 0

    def get_subscriptions(self, chat_id: int) -> List[Dict[str, Any]]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM subscriptions WHERE chat_id = ?",
                (chat_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_subscription_by_short_code(
        self,
        chat_id: int,
        short_code: str
    ) -> Optional[Dict[str, Any]]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM subscriptions WHERE chat_id = ? AND short_code = ?",
                (chat_id, short_code.upper())
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_subscription_by_id(
        self,
        chat_id: int,
        subscription_id: int
    ) -> Optional[Dict[str, Any]]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM subscriptions WHERE id = ? AND chat_id = ?",
                (subscription_id, chat_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_member(
        self,
        chat_id: int,
        subscription_id: int,
        user_id: int,
        username: str
    ) -> bool:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM subscriptions WHERE id = ? AND chat_id = ?",
                (subscription_id, chat_id)
            )
            if not cursor.fetchone():
                return False

            conn.execute(
                """
                INSERT OR REPLACE INTO subscription_members (subscription_id, user_id, username)
                VALUES (?, ?, ?)
                """,
                (subscription_id, user_id, username)
            )
            return True

    def remove_member(
        self,
        chat_id: int,
        subscription_id: int,
        user_id: int
    ) -> bool:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM subscriptions WHERE id = ? AND chat_id = ?",
                (subscription_id, chat_id)
            )
            if not cursor.fetchone():
                return False

            cursor = conn.execute(
                "DELETE FROM subscription_members WHERE subscription_id = ? AND user_id = ?",
                (subscription_id, user_id)
            )
            return cursor.rowcount > 0

    def get_members(self, chat_id: int, subscription_id: int) -> List[Dict[str, Any]]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                """
                SELECT m.* FROM subscription_members m
                JOIN subscriptions s ON m.subscription_id = s.id
                WHERE s.id = ? AND s.chat_id = ?
                """,
                (subscription_id, chat_id)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_subscriptions_with_members(self, chat_id: int) -> List[Dict[str, Any]]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM subscriptions WHERE chat_id = ?",
                (chat_id,)
            )
            subs = [dict(row) for row in cursor.fetchall()]
            for sub in subs:
                cursor.execute(
                    "SELECT user_id, username FROM subscription_members WHERE subscription_id = ?",
                    (sub["id"],)
                )
                sub["members"] = [dict(row) for row in cursor.fetchall()]
            return subs


class UserBillingRepository:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    def create_billing(
        self,
        chat_id: int,
        user_id: int,
        username: str,
        amount: int,
        year: int,
        month: int
    ) -> int:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO user_billing (chat_id, user_id, username, amount, year, month, is_paid)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                (chat_id, user_id, username, amount, year, month)
            )
            return cursor.lastrowid

    def link_billing_subscription(
        self,
        user_billing_id: int,
        subscription_id: int,
        title: str,
        short_code: str,
        individual_amount: int
    ) -> None:
        with self.manager.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_billing_subscriptions 
                (user_billing_id, subscription_id, title, short_code, individual_amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_billing_id, subscription_id, title, short_code.upper(), individual_amount)
            )

    def get_billings_for_month(
        self,
        chat_id: int,
        year: int,
        month: int
    ) -> List[Dict[str, Any]]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                """
                SELECT b.*, m.member_id FROM user_billing b
                LEFT JOIN group_members m ON b.chat_id = m.chat_id AND b.user_id = m.user_id
                WHERE b.chat_id = ? AND b.year = ? AND b.month = ?
                """,
                (chat_id, year, month)
            )
            billings = [dict(row) for row in cursor.fetchall()]
            for billing in billings:
                cursor.execute(
                    "SELECT * FROM user_billing_subscriptions WHERE user_billing_id = ?",
                    (billing["id"],)
                )
                billing["subscriptions"] = [dict(row) for row in cursor.fetchall()]
            return billings

    def get_billing_by_id(self, chat_id: int, billing_id: int) -> Optional[Dict[str, Any]]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_billing WHERE id = ? AND chat_id = ?",
                (billing_id, chat_id)
            )
            row = cursor.fetchone()
            if not row:
                return None
            billing = dict(row)
            cursor.execute(
                "SELECT * FROM user_billing_subscriptions WHERE user_billing_id = ?",
                (billing["id"],)
            )
            billing["subscriptions"] = [dict(row) for row in cursor.fetchall()]
            return billing

    def update_payment_status(self, chat_id: int, billing_id: int, is_paid: int) -> bool:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                "UPDATE user_billing SET is_paid = ? WHERE id = ? AND chat_id = ?",
                (is_paid, billing_id, chat_id)
            )
            return cursor.rowcount > 0

    def update_billing_amount(self, chat_id: int, billing_id: int, amount: int) -> bool:
        with self.manager.transaction() as conn:
            cursor = conn.execute(
                "UPDATE user_billing SET amount = ? WHERE id = ? AND chat_id = ?",
                (amount, billing_id, chat_id)
            )
            return cursor.rowcount > 0

    def delete_billings_for_month(self, chat_id: int, year: int, month: int) -> None:
        with self.manager.transaction() as conn:
            conn.execute(
                "DELETE FROM user_billing WHERE chat_id = ? AND year = ? AND month = ?",
                (chat_id, year, month)
            )


class MonthlyBillMessageRepository:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    def get_message_id(self, chat_id: int, year: int, month: int) -> Optional[int]:
        with self.manager.cursor() as cursor:
            cursor.execute(
                "SELECT message_id FROM monthly_bills WHERE chat_id = ? AND year = ? AND month = ?",
                (chat_id, year, month)
            )
            row = cursor.fetchone()
            return row["message_id"] if row else None

    def save_message_id(self, chat_id: int, year: int, month: int, message_id: int) -> None:
        with self.manager.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO monthly_bills (chat_id, year, month, message_id)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, year, month, message_id)
            )
