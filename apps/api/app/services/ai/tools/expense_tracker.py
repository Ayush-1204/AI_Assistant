import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models.expense import Expense
from app.db.session import AsyncSessionLocal
from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class ExpenseTrackerTool(BaseTool):
    @property
    def name(self) -> str:
        return "expense_tracker"
        
    @property
    def description(self) -> str:
        return "Logs or queries financial expenses, purchases, and receipts. Use this to track user spending, budgeting, and OCR parsed receipt data."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action: 'get_summary', 'log_expense'.",
                    "enum": ["get_summary", "log_expense"]
                },
                "amount": {
                    "type": "number",
                    "description": "Cost amount of the expense."
                },
                "vendor": {
                    "type": "string",
                    "description": "Store or vendor name."
                },
                "category": {
                    "type": "string",
                    "description": "Expense category (e.g. food, tech, rent)."
                },
                "date_iso": {
                    "type": "string",
                    "description": "ISO format date of the expense. Defaults to now if not provided."
                }
            },
            "required": ["action"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> str:
        user_id = execution_context.get("user_id")
        action = kwargs.get("action")

        if not user_id:
            return "ERROR: user_id missing from context."

        async with AsyncSessionLocal() as session:
            if action == "get_summary":
                result = await session.execute(select(Expense).where(Expense.user_id == user_id).order_by(Expense.date_incurred.desc()).limit(20))
                expenses = result.scalars().all()
                if not expenses:
                    return "No expenses logged recently."
                
                total = sum(e.amount for e in expenses)
                lines = [f"- {e.date_incurred.strftime('%b %d')}: ${e.amount:.2f} at {e.vendor} ({e.category})" for e in expenses]
                return f"Total Recent Spending (up to 20 tracked items): ${total:.2f}\\n\\n" + "\\n".join(lines)
                
            elif action == "log_expense":
                amount = kwargs.get("amount")
                vendor = kwargs.get("vendor", "Unknown")
                
                if amount is None:
                    return "ERROR: amount is required to log an expense."
                    
                date_iso = kwargs.get("date_iso")
                date_obj = datetime.now(timezone.utc)
                if date_iso:
                    try:
                        date_obj = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
                    except:
                        pass
                        
                new_expense = Expense(
                    user_id=user_id,
                    amount=amount,
                    vendor=vendor,
                    category=kwargs.get("category", "Uncategorized"),
                    date_incurred=date_obj
                )
                session.add(new_expense)
                await session.commit()
                return f"Successfully logged expense: ${float(amount):.2f} at {vendor}."
                
            return "ERROR: Unknown action."
