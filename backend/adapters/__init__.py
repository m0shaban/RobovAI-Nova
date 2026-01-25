"""RobovAI Nova - Platform Adapters Package"""
from .platforms import (
    BasePlatformAdapter,
    IncomingMessage,
    OutgoingMessage,
    TelegramAdapter,
    WhatsAppAdapter,
    MessengerAdapter,
    WebWidgetAdapter,
    DiscordAdapter,
    AdapterFactory
)

__all__ = [
    'BasePlatformAdapter',
    'IncomingMessage',
    'OutgoingMessage',
    'TelegramAdapter',
    'WhatsAppAdapter',
    'MessengerAdapter',
    'WebWidgetAdapter',
    'DiscordAdapter',
    'AdapterFactory'
]
