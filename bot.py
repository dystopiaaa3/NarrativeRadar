import os
import asyncio

from dotenv import load_dotenv

from core.client import NarrativeRadarBot


load_dotenv()


async def main():

    token = os.getenv(
        "DISCORD_BOT_TOKEN"
    )

    if not token:

        raise RuntimeError(
            "DISCORD_BOT_TOKEN is missing from .env"
        )


    bot = NarrativeRadarBot()


    async with bot:

        await bot.start(
            token
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )