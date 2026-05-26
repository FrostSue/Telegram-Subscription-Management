from typing import List, Dict, Any, Optional
import math

MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

class ListFormatter:
    @staticmethod
    def format_billing_list(
        billings: List[Dict[str, Any]],
        subscriptions_with_shares: List[Dict[str, Any]],
        settings: Dict[str, Any],
        year: int,
        month: int
    ) -> str:
        month_name = MONTHS.get(month, str(month))
        currency = settings.get("currency", "USD")
        
        lines = []
        lines.append(f"<b>📅 {month_name} {year} Billing List</b>")
        lines.append("---------------------------------")
        
        if not billings:
            lines.append("No active bills for this month.")
        else:
            for idx, bill in enumerate(billings, 1):
                display_id = bill.get("member_id", bill["id"])
                username = bill["username"]
                amount = bill["amount"]
                is_paid = bill["is_paid"]
                
                codes = [sub["short_code"] for sub in bill.get("subscriptions", [])]
                codes_str = f" [{', '.join(codes)}]" if codes else ""
                
                status_text = "Paid" if is_paid else "Unpaid"
                line_content = f"{idx}. {username} - {amount} {currency}{codes_str} ({status_text}) (ID: {display_id})"
                
                if is_paid:
                    lines.append(f"<s>{line_content}</s>")
                else:
                    lines.append(line_content)
                    
        lines.append("---------------------------------")
        lines.append("<b>Individual Subscription Prices:</b>")
        
        if not subscriptions_with_shares:
            lines.append("No subscriptions configured.")
        else:
            for sub in subscriptions_with_shares:
                title = sub["title"]
                code = sub["short_code"]
                cost = sub["cost"]
                discount = sub["discount"]
                members_count = len(sub.get("members", []))
                
                if sub.get("manual_individual_amount") is not None:
                    share = sub["manual_individual_amount"]
                elif members_count > 0:
                    share = math.ceil((cost - discount) / members_count)
                else:
                    share = math.ceil(cost - discount)
                    
                lines.append(f"- [{code}] {title}: {share} {currency}")
                
        lines.append("---------------------------------")
        lines.append("<b>🏦 Payment Details</b>")
        
        iban = settings.get("iban")
        iban_name = settings.get("iban_name")
        
        if iban and iban_name:
            lines.append(f"IBAN: <code>{iban}</code>")
            lines.append(f"Name: {iban_name}")
        else:
            lines.append("IBAN details are not configured by admin.")
            
        return "\n".join(lines)
