from typing import Tuple, Optional
import datetime

class CommandValidator:
    @staticmethod
    def parse_add_sub(args: list) -> Tuple[str, float, float]:
        if len(args) < 2:
            raise ValueError("Usage: /add_sub <title> <cost> [discount]")
        
        title = args[0].strip()
        try:
            cost = float(args[1])
            if cost <= 0:
                raise ValueError("Cost must be greater than zero.")
        except ValueError:
            raise ValueError("Cost must be a valid number.")

        discount = 0.0
        if len(args) >= 3:
            try:
                discount = float(args[2])
                if discount < 0:
                    raise ValueError("Discount cannot be negative.")
                if discount >= cost:
                    raise ValueError("Discount must be less than cost.")
            except ValueError:
                raise ValueError("Discount must be a valid number.")

        return title, cost, discount

    @staticmethod
    def parse_add_member(args: list) -> Tuple[int, str]:
        if len(args) < 2:
            raise ValueError("Usage: /add_member <sub_id> <username>")
        
        try:
            sub_id = int(args[0])
        except ValueError:
            raise ValueError("Subscription ID must be an integer.")
        
        username = args[1].strip()
        if not username.startswith("@"):
            username = f"@{username}"
            
        return sub_id, username

    @staticmethod
    def parse_remove_member(args: list) -> Tuple[int, str]:
        if len(args) < 2:
            raise ValueError("Usage: /remove_member <sub_id> <username>")
        
        try:
            sub_id = int(args[0])
        except ValueError:
            raise ValueError("Subscription ID must be an integer.")
        
        username = args[1].strip()
        if not username.startswith("@"):
            username = f"@{username}"
            
        return sub_id, username

    @staticmethod
    def parse_set_iban(args: list) -> Tuple[str, str]:
        if len(args) < 2:
            raise ValueError("Usage: /set_iban <iban> <account_holder_name>")
        
        iban = args[0].strip().replace(" ", "").upper()
        name = " ".join(args[1:]).strip()
        
        if not iban.isalnum() or len(iban) < 15:
            raise ValueError("IBAN must be a valid alphanumeric code of at least 15 characters.")
            
        if not name:
            raise ValueError("Account holder name cannot be empty.")
            
        return iban, name

    @staticmethod
    def parse_set_currency(args: list) -> str:
        if len(args) < 1:
            raise ValueError("Usage: /set_currency <currency_symbol>")
        
        currency = args[0].strip()
        if len(currency) > 10:
            raise ValueError("Currency symbol is too long.")
            
        return currency

    @staticmethod
    def parse_set_debt(args: list) -> Tuple[int, int]:
        if len(args) < 2:
            raise ValueError("Usage: /set_debt <billing_id> <new_amount>")
        
        try:
            billing_id = int(args[0])
        except ValueError:
            raise ValueError("Billing ID must be an integer.")
            
        try:
            amount = int(args[1])
            if amount < 0:
                raise ValueError("Amount cannot be negative.")
        except ValueError:
            raise ValueError("Amount must be an integer.")
            
        return billing_id, amount

    @staticmethod
    def parse_paid_unpaid(args: list, command_name: str) -> int:
        if len(args) < 1:
            raise ValueError(f"Usage: /{command_name} <billing_id>")
        
        try:
            billing_id = int(args[0])
        except ValueError:
            raise ValueError("Billing ID must be an integer.")
            
        return billing_id

    @staticmethod
    def parse_billing(args: list) -> Tuple[int, int]:
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        
        if len(args) >= 1:
            try:
                month = int(args[0])
                if not (1 <= month <= 12):
                    raise ValueError("Month must be between 1 and 12.")
            except ValueError:
                raise ValueError("Month must be an integer.")
                
        if len(args) >= 2:
            try:
                year = int(args[1])
                if year < 2000:
                    raise ValueError("Year must be a valid four-digit year.")
            except ValueError:
                raise ValueError("Year must be an integer.")
                
        return year, month
