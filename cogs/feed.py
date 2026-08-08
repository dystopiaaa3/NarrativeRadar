import asyncio

import discord

from discord import app_commands
from discord.ext import commands

from core.learning.feed_learning import (
    FeedLearningService,
)


class FeedCog(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot


    @app_commands.command(
        name="feed",
        description=(
            "Feed a token into NarrativeRadar's "
            "outcome-learning system."
        )
    )
    @app_commands.describe(
        coin_address=(
            "Solana token mint address"
        )
    )
    async def feed(
        self,
        interaction: discord.Interaction,
        coin_address: str
    ):

        address = (
            coin_address
            .strip()
        )


        if not (
            32
            <= len(address)
            <= 44
        ):

            await interaction.response.send_message(
                (
                    "That does not look like a valid "
                    "Solana token mint."
                ),
                ephemeral=True,
            )

            return


        await interaction.response.defer()


        service = (
            FeedLearningService()
        )


        result = await asyncio.to_thread(
            service.feed,
            address
        )


        if not result.get(
            "success"
        ):

            await interaction.followup.send(
                (
                    "Feed failed.\n\n"
                    f"`{result.get('error')}`"
                )
            )

            return


        embed = discord.Embed(
            title=(
                "Learning Case Created"
            ),
            description=(
                f"**{result['symbol']}**\n"
                f"`{result['coin_address']}`"
            ),
        )


        embed.add_field(
            name="Case ID",
            value=(
                f"**{result['feed_case_id']}**"
            ),
            inline=True,
        )


        embed.add_field(
            name="Narrative",
            value=(
                f"**{result['narrative']}**"
            ),
            inline=True,
        )


        embed.add_field(
            name="Status",
            value="**TRACKING**",
            inline=True,
        )


        embed.add_field(
            name="T0 Radar",
            value=(
                f"Score: **{result['combined_score']}**\n"
                f"Signal: **{result['signal']}**\n"
                f"Confidence: "
                f"**{result['confidence']}%**\n"
                f"Decision: "
                f"**{result['decision']}**\n"
                f"Risk: **{result['risk']}**"
            ),
            inline=False,
        )


        embed.add_field(
            name="T0 Market",
            value=(
                f"Price: **${result['price']:,.10g}**\n"
                f"Market Cap: "
                f"**{money(result['market_cap'])}**\n"
                f"Liquidity: "
                f"**{money(result['liquidity'])}**\n"
                f"24H Volume: "
                f"**{money(result['volume_24h'])}**"
            ),
            inline=False,
        )


        embed.add_field(
            name="What happens next?",
            value=(
                "NarrativeRadar will automatically "
                "measure this setup again at "
                "**15m, 1h, 6h and 24h**.\n\n"
                "The submitted token is **not** assumed "
                "to be a winner. Its real market outcome "
                "determines what the system learns."
            ),
            inline=False,
        )


        embed.set_footer(
            text=(
                "Fluency + Accuracy + "
                "Consistency = Mastery"
            )
        )


        await interaction.followup.send(
            embed=embed
        )


async def setup(bot):

    await bot.add_cog(
        FeedCog(bot)
    )


def money(value):

    value = float(
        value or 0
    )

    if value >= 1_000_000_000:

        return (
            f"${value / 1_000_000_000:.2f}B"
        )

    if value >= 1_000_000:

        return (
            f"${value / 1_000_000:.2f}M"
        )

    if value >= 1_000:

        return (
            f"${value / 1_000:.2f}K"
        )

    return (
        f"${value:,.2f}"
    )