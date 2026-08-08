import asyncio

import discord

from discord.ext import commands

from database.database import (
    create_database,
)

from core.scanner.background_scanner import (
    BackgroundScanner,
)

from core.learning.feed_learning import (
    FeedLearningService,
)


class NarrativeRadarBot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )


        self.market_scanner = (
            BackgroundScanner(
                discovery_limit=20,
                batch_size=3,
                signature_limit=20,
                max_workers=3,
                cycle_seconds=20,
            )
        )


        self.feed_learning = (
            FeedLearningService(
                check_interval=60
            )
        )


        self.scanner_task = None

        self.learning_task = None


    async def setup_hook(self):

        # Ensure any newly added tables exist.

        create_database()


        await self.load_extension(
            "cogs.radar"
        )


        await self.load_extension(
            "cogs.manual"
        )


        await self.load_extension(
            "cogs.feed"
        )


        synced = (
            await self.tree.sync()
        )


        print(
            f"Synced {len(synced)} "
            f"Discord commands."
        )


        if self.scanner_task is None:

            self.scanner_task = (
                asyncio.create_task(
                    asyncio.to_thread(
                        self.market_scanner.run_forever
                    )
                )
            )


            print(
                "Background market scanner started."
            )


        if self.learning_task is None:

            self.learning_task = (
                asyncio.create_task(
                    asyncio.to_thread(
                        self.feed_learning.run_forever
                    )
                )
            )


            print(
                "Feed learning tracker started."
            )


    async def on_ready(self):

        print(
            f"NarrativeRadar online as "
            f"{self.user}"
        )

        print(
            f"Bot ID: {self.user.id}"
        )

        print(
            "Discord + Scanner + Learning ONLINE"
        )


    async def close(self):

        print(
            "Stopping NarrativeRadar..."
        )


        try:

            self.market_scanner.stop()

        except Exception as error:

            print(
                "Scanner stop error:",
                str(error)
            )


        try:

            self.feed_learning.stop()

        except Exception as error:

            print(
                "Learning stop error:",
                str(error)
            )


        tasks = [
            task
            for task in (
                self.scanner_task,
                self.learning_task,
            )
            if task is not None
        ]


        if tasks:

            try:

                await asyncio.wait_for(
                    asyncio.gather(
                        *tasks,
                        return_exceptions=True,
                    ),
                    timeout=10,
                )

            except asyncio.TimeoutError:

                print(
                    "Background shutdown timeout."
                )


        await super().close()