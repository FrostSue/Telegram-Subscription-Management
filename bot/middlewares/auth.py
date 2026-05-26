import logging
from functools import wraps
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

def requires_admin(func):
    @wraps(func)
    async def decorator(client: Client, message: Message, *args, **kwargs):
        if not message.chat or not message.from_user:
            return
            
        if message.chat.type.name in ["PRIVATE", "BOT"]:
            return await func(client, message, *args, **kwargs)
            
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            logging.info(f"Admin check for user {message.from_user.id} in chat {message.chat.id}. Status: {member.status}")
            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                return await func(client, message, *args, **kwargs)
        except Exception as e:
            logging.error(f"Admin check failed with exception: {str(e)}")
            
        await message.reply_text("This command is restricted to group administrators.")
    return decorator
