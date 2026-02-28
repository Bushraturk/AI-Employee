"""Executors for local agent."""

from local_agent.src.executors.email_executor import EmailExecutor
from local_agent.src.executors.accounting_executor import AccountingExecutor
from local_agent.src.executors.whatsapp_executor import WhatsAppExecutor

__all__ = ["EmailExecutor", "AccountingExecutor", "WhatsAppExecutor"]
