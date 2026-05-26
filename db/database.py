from db.connection import ConnectionManager

def initialize_database(manager: ConnectionManager) -> None:
    with manager.transaction() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                currency TEXT NOT NULL DEFAULT 'USD',
                iban TEXT,
                iban_name TEXT,
                billing_day INTEGER NOT NULL DEFAULT 16
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                member_id INTEGER NOT NULL,
                PRIMARY KEY (chat_id, user_id),
                FOREIGN KEY (chat_id) REFERENCES group_settings (chat_id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_group_members_unique ON group_members (chat_id, member_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                short_code TEXT NOT NULL,
                cost REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0.0,
                manual_individual_amount INTEGER DEFAULT NULL,
                FOREIGN KEY (chat_id) REFERENCES group_settings (chat_id) ON DELETE CASCADE,
                UNIQUE (chat_id, title),
                UNIQUE (chat_id, short_code)
            )
        """)

        try:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN manual_individual_amount INTEGER DEFAULT NULL")
        except Exception:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscription_members (
                subscription_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                PRIMARY KEY (subscription_id, user_id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS monthly_bills (
                chat_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                PRIMARY KEY (chat_id, year, month),
                FOREIGN KEY (chat_id) REFERENCES group_settings (chat_id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_billing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                amount INTEGER NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                is_paid INTEGER NOT NULL DEFAULT 0 CHECK (is_paid IN (0, 1)),
                FOREIGN KEY (chat_id) REFERENCES group_settings (chat_id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_billing_subscriptions (
                user_billing_id INTEGER NOT NULL,
                subscription_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                short_code TEXT NOT NULL,
                individual_amount INTEGER NOT NULL,
                PRIMARY KEY (user_billing_id, subscription_id),
                FOREIGN KEY (user_billing_id) REFERENCES user_billing (id) ON DELETE CASCADE,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_chat ON subscriptions (chat_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_billing_lookup ON user_billing (chat_id, year, month)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_billing_user ON user_billing (chat_id, user_id, is_paid)")
