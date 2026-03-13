"""
Telegram bot that polls messages and forwards to/from Galaxy Map.

Requires:
- TELEGRAM_BOT_TOKEN environment variable
- GALAXY_MAP_URL environment variable (default: http://localhost:8000)
"""

import asyncio
import os
import logging
from typing import Optional

import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GALAXY_MAP_URL = os.environ.get("GALAXY_MAP_URL", "http://localhost:8000")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages."""
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    text = update.message.text

    logger.info(f"Received message from {user_id}: {text}")

    # Post to Galaxy Map
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GALAXY_MAP_URL}/api/messages",
                json={"user_id": user_id, "text": text},
                timeout=10,
            )
            response.raise_for_status()
            msg_data = response.json()
            msg_id = msg_data["id"]

            await update.message.reply_text(
                "✓ Message received. Waiting for response..."
            )
            logger.info(f"Posted to Galaxy Map: {msg_id}")

            # Poll for response (max 2 minutes)
            for attempt in range(120):
                await asyncio.sleep(1)
                try:
                    response = await client.get(
                        f"{GALAXY_MAP_URL}/api/messages/{msg_id}",
                        timeout=10,
                    )
                    response.raise_for_status()
                    msg_data = response.json()

                    if msg_data["status"] == "answered" and msg_data.get("response"):
                        await update.message.reply_text(msg_data["response"])
                        logger.info(f"Sent response for {msg_id}")
                        return
                except Exception as e:
                    logger.warning(f"Error polling for response: {e}")

            # Timeout
            await update.message.reply_text(
                "⏱ No response received within 2 minutes."
            )

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(f"Error: {str(e)}")


async def main():
    """Start the bot."""
    logger.info(f"Starting Telegram bot (Galaxy Map: {GALAXY_MAP_URL})")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handle all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Run
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())
