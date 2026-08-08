import asyncio
import math

import discord

from discord import app_commands
from discord.ext import commands

from core.services.discord_service import (
    DiscordService,
)


# =============================================================
# DISPLAY HELPERS
# =============================================================

def money(value):

    try:
        value = float(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        value = 0.0


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


def signed_percent(value):

    try:
        value = float(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        value = 0.0


    return (
        f"{value:+.2f}%"
    )


# =============================================================
# TRENDING PAGINATOR
# =============================================================

class TrendingView(
    discord.ui.View
):

    def __init__(
        self,
        rows,
        duration,
        user_id,
        page_size=5,
    ):

        super().__init__(
            timeout=120
        )

        self.rows = list(
            rows or []
        )

        self.duration = (
            duration
        )

        self.user_id = (
            user_id
        )

        self.page_size = max(
            1,
            int(
                page_size
            )
        )

        self.page = 0

        self.total_pages = max(
            1,
            math.ceil(
                len(
                    self.rows
                )
                /
                self.page_size
            )
        )

        self._update_buttons()


    # =========================================================
    # USER SECURITY
    # =========================================================

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ):

        if (
            interaction.user.id
            !=
            self.user_id
        ):

            await interaction.response.send_message(
                (
                    "Only the person who opened "
                    "this page can use these buttons."
                ),
                ephemeral=True,
            )

            return False


        return True


    # =========================================================
    # BUILD PAGE
    # =========================================================

    def build_embed(self):

        embed = discord.Embed(
            title=(
                f"Trending Narratives - "
                f"{self.duration}"
            )
        )


        if not self.rows:

            embed.description = (
                "No narrative activity has been "
                "recorded for this period yet."
            )

            return embed


        start = (
            self.page
            *
            self.page_size
        )

        end = (
            start
            +
            self.page_size
        )


        page_rows = (
            self.rows[
                start:end
            ]
        )


        # Numbering intentionally resets to
        # 1-5 on every page as requested.

        for index, row in enumerate(
            page_rows,
            start=1,
        ):

            market_samples = int(
                row.get(
                    "market_samples",
                    0,
                )
                or 0
            )


            if market_samples > 0:

                mc_text = money(
                    row.get(
                        "avg_market_cap",
                        0,
                    )
                )

            else:

                mc_text = (
                    "Collecting"
                )


            embed.add_field(
                name=(
                    f"#{index} "
                    f"{row.get('name', 'Unknown')}"
                ),

                value=(
                    f"Score "
                    f"**{row.get('score', 0)}**\n"
                    f"Coins "
                    f"**{row.get('coin_count', 0)}**\n"
                    f"Confidence "
                    f"**{row.get('avg_confidence', 0)}%**\n"
                    f"Avg MC "
                    f"**{mc_text}**"
                ),

                inline=False,
            )


        embed.set_footer(
            text=(
                f"Page "
                f"{self.page + 1}"
                f"/"
                f"{self.total_pages}"
                " | Latest valid market data"
            )
        )


        return embed


    # =========================================================
    # BUTTON STATE
    # =========================================================

    def _update_buttons(self):

        self.previous_button.disabled = (
            self.page <= 0
        )

        self.next_button.disabled = (
            self.page
            >=
            self.total_pages - 1
        )


    # =========================================================
    # PREVIOUS
    # =========================================================

    @discord.ui.button(
        label="◀",
        style=discord.ButtonStyle.secondary,
    )
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if self.page > 0:

            self.page -= 1


        self._update_buttons()


        await interaction.response.edit_message(
            embed=(
                self.build_embed()
            ),
            view=self,
        )


    # =========================================================
    # NEXT
    # =========================================================

    @discord.ui.button(
        label="▶",
        style=discord.ButtonStyle.secondary,
    )
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if (
            self.page
            <
            self.total_pages - 1
        ):

            self.page += 1


        self._update_buttons()


        await interaction.response.edit_message(
            embed=(
                self.build_embed()
            ),
            view=self,
        )


    # =========================================================
    # TIMEOUT
    # =========================================================

    async def on_timeout(self):

        for child in self.children:

            if isinstance(
                child,
                discord.ui.Button,
            ):

                child.disabled = True


# =============================================================
# RADAR COG
# =============================================================

class RadarCog(
    commands.Cog
):

    def __init__(
        self,
        bot,
    ):

        self.bot = (
            bot
        )

        self.service = (
            DiscordService()
        )

        self.watchers = {}


    # =========================================================
    # HELP
    # =========================================================

    @app_commands.command(
        name="help",
        description="Show all NarrativeRadar commands.",
    )
    async def help_command(
        self,
        interaction: discord.Interaction,
    ):

        embed = discord.Embed(
            title=(
                "NarrativeRadar Commands"
            ),

            description=(
                "Real-time Solana narrative intelligence, "
                "manual token analysis, and outcome learning."
            ),
        )


        embed.add_field(
            name="Market Intelligence",

            value=(
                "`/trending` - What's gaining momentum\n"
                "`/topnarratives` - Strongest narratives now\n"
                "`/emerging` - Narratives starting early\n"
                "`/rotation` - Where attention is moving\n"
                "`/pulse` - Overall market condition\n"
                "`/radar` - Market control room"
            ),

            inline=False,
        )


        embed.add_field(
            name="Analysis",

            value=(
                "`/compare` - Compare two narratives\n"
                "`/timeline` - Narrative evolution\n"
                "`/discover` - Unusual emerging themes\n"
                "`/report` - Daily intelligence report\n"
                "`/scan` - Fresh live scan of a token"
            ),

            inline=False,
        )


        embed.add_field(
            name="Learning & Alerts",

            value=(
                "`/feed` - Track a token and learn from its outcome\n"
                "`/watch` - Watch a narrative for movement"
            ),

            inline=False,
        )


        embed.set_footer(
            text=(
                "Fluency + Accuracy + "
                "Consistency = Mastery"
            )
        )


        await interaction.response.send_message(
            embed=embed
        )


    # =========================================================
    # TRENDING
    # =========================================================

    @app_commands.command(
        name="trending",
        description="Show narratives gaining momentum.",
    )
    @app_commands.describe(
        duration=(
            "1h, 3h, 6h, 12h or 24h"
        )
    )
    async def trending(
        self,
        interaction: discord.Interaction,
        duration: str = "6h",
    ):

        await interaction.response.defer()


        duration = str(
            duration or "6h"
        ).lower().strip()


        if duration not in (
            "1h",
            "3h",
            "6h",
            "12h",
            "24h",
        ):

            duration = "6h"


        rows = (
            await asyncio.to_thread(
                self.service.trending,
                duration,
            )
        )


        view = TrendingView(
            rows=rows,
            duration=duration,
            user_id=(
                interaction.user.id
            ),
            page_size=5,
        )


        await interaction.followup.send(
            embed=(
                view.build_embed()
            ),
            view=view,
        )


    # =========================================================
    # TOP NARRATIVES
    # =========================================================

    @app_commands.command(
        name="topnarratives",
        description="Show the strongest narratives now.",
    )
    async def topnarratives(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.defer()


        rows = (
            await asyncio.to_thread(
                self.service.top_narratives
            )
        )


        embed = discord.Embed(
            title="Top Narratives"
        )


        if not rows:

            embed.description = (
                "No ranked narratives "
                "are available yet."
            )


        else:

            lines = []


            for index, row in enumerate(
                rows,
                start=1,
            ):

                lines.append(
                    (
                        f"**#{index} "
                        f"{row['name']}**\n"
                        f"Score "
                        f"`{row['score']}` - "
                        f"Confidence "
                        f"`{row['confidence']}%` - "
                        f"Coins "
                        f"`{row['coin_count']}`"
                    )
                )


            embed.description = (
                "\n\n".join(
                    lines
                )
            )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # EMERGING
    # =========================================================

    @app_commands.command(
        name="emerging",
        description="Find narratives that are just beginning.",
    )
    async def emerging(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.defer()


        rows = (
            await asyncio.to_thread(
                self.service.emerging
            )
        )


        embed = discord.Embed(
            title="Emerging Narratives"
        )


        if not rows:

            embed.description = (
                "No qualified emerging "
                "narratives detected yet."
            )


        else:

            for row in rows:

                avg_mc = float(
                    row.get(
                        "avg_market_cap",
                        0,
                    )
                    or 0
                )


                mc_text = (
                    money(
                        avg_mc
                    )
                    if avg_mc > 0
                    else
                    "Collecting"
                )


                embed.add_field(
                    name=(
                        row.get(
                            "name",
                            "Unknown",
                        )
                    ),

                    value=(
                        f"Confidence "
                        f"**{row.get('confidence', 0)}%**\n"
                        f"Launches "
                        f"**{row.get('launches', 0)}**\n"
                        f"Average MC "
                        f"**{mc_text}**\n"
                        f"Age "
                        f"**{row.get('age_minutes', 0)} min**"
                    ),

                    inline=False,
                )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # ROTATION
    # =========================================================

    @app_commands.command(
        name="rotation",
        description="Detect where market attention is moving.",
    )
    async def rotation(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.defer()


        rows = (
            await asyncio.to_thread(
                self.service.rotation
            )
        )


        embed = discord.Embed(
            title="Market Rotation"
        )


        if not rows:

            embed.description = (
                "Not enough historical narrative "
                "data exists to confirm a rotation yet."
            )


        else:

            strongest = (
                rows[
                    0
                ]
            )


            direction = (
                "into"
                if strongest[
                    "change"
                ] > 0
                else
                "out of"
            )


            embed.description = (
                "**Market rotation detected.**\n\n"
                f"Attention appears to be moving "
                f"**{direction} "
                f"{strongest['name']}**.\n\n"
                f"Momentum change "
                f"**{strongest['change']:+.2f}**"
            )


            for row in rows[
                :5
            ]:

                direction_text = (
                    "UP"
                    if row[
                        "change"
                    ] > 0
                    else
                    "DOWN"
                )


                embed.add_field(
                    name=(
                        f"{direction_text} - "
                        f"{row['name']}"
                    ),

                    value=(
                        f"{row['previous']} "
                        f"-> "
                        f"{row['current']} "
                        f"({row['change']:+.2f})"
                    ),

                    inline=False,
                )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # RADAR
    # =========================================================

    @app_commands.command(
        name="radar",
        description="Open the NarrativeRadar market control room.",
    )
    async def radar(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.defer()


        result = (
            await asyncio.to_thread(
                self.service.radar
            )
        )


        pulse = (
            result.get(
                "pulse",
                {},
            )
        )

        trending = (
            result.get(
                "trending",
                [],
            )
        )

        emerging = (
            result.get(
                "emerging",
                [],
            )
        )


        embed = discord.Embed(
            title="MARKET RADAR"
        )


        embed.add_field(
            name="Market State",

            value=(
                f"**{pulse.get('state', 'UNKNOWN')}**"
            ),

            inline=True,
        )


        embed.add_field(
            name="Market Strength",

            value=(
                f"**{pulse.get('average_score', 0)}%**"
            ),

            inline=True,
        )


        embed.add_field(
            name="Radar Samples",

            value=(
                f"**{pulse.get('total_results', 0)}**"
            ),

            inline=True,
        )


        hottest = (
            trending[
                0
            ].get(
                "name",
                "Insufficient data",
            )
            if trending
            else
            "Insufficient data"
        )


        newest = (
            emerging[
                0
            ].get(
                "name",
                "Insufficient data",
            )
            if emerging
            else
            "Insufficient data"
        )


        embed.add_field(
            name="Hottest Narrative",

            value=hottest,

            inline=False,
        )


        embed.add_field(
            name="Emerging Narrative",

            value=newest,

            inline=False,
        )


        embed.set_footer(
            text=(
                "Narratives are ranked from "
                "NarrativeRadar's observed dataset"
            )
        )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # PULSE
    # =========================================================

    @app_commands.command(
        name="pulse",
        description="Show overall market health.",
    )
    async def pulse(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.defer()


        result = (
            await asyncio.to_thread(
                self.service.pulse
            )
        )


        embed = discord.Embed(
            title="Market Pulse",

            description=(
                f"## "
                f"{result.get('state', 'UNKNOWN')}"
            ),
        )


        embed.add_field(
            name="Overall Strength",

            value=(
                f"{result.get('average_score', 0)}%"
            ),

            inline=True,
        )


        embed.add_field(
            name="Strong Results",

            value=str(
                result.get(
                    "bullish_results",
                    0,
                )
            ),

            inline=True,
        )


        embed.add_field(
            name="Weak Results",

            value=str(
                result.get(
                    "bearish_results",
                    0,
                )
            ),

            inline=True,
        )


        embed.add_field(
            name="Samples",

            value=str(
                result.get(
                    "total_results",
                    0,
                )
            ),

            inline=True,
        )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # REPORT
    # =========================================================

    @app_commands.command(
        name="report",
        description="Generate today's market and learning report.",
    )
    async def report(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.defer()


        result = (
            await asyncio.to_thread(
                self.service.report
            )
        )


        learning = (
            result.get(
                "learning",
                {},
            )
        )

        returns = (
            result.get(
                "returns",
                {},
            )
        )

        model_health = (
            result.get(
                "model_health",
                {},
            )
        )

        best_bucket = (
            result.get(
                "best_score_bucket"
            )
        )

        quality = (
            result.get(
                "quality_buckets",
                {},
            )
        )


        embed = discord.Embed(
            title="NarrativeRadar Report",

            description=(
                "24H market activity + "
                "verified learning performance"
            ),
        )


        embed.add_field(
            name="Market",

            value=(
                f"Coins Scanned "
                f"**{result.get('coins_scanned', 0)}**\n"
                f"Radar Runs "
                f"**{result.get('scans', 0)}**\n"
                f"Narratives "
                f"**{result.get('narratives', 0)}**\n"
                f"Average Radar "
                f"**{result.get('average_score', 0)}**"
            ),

            inline=True,
        )


        embed.add_field(
            name="Peak Signal",

            value=(
                f"Score "
                f"**{result.get('highest_score', 0)}**\n"
                f"Signal "
                f"**{result.get('highest_signal', 'NONE')}**\n"
                f"Alerts "
                f"**{result.get('alerts', 0)}**"
            ),

            inline=True,
        )


        embed.add_field(
            name="Learning",

            value=(
                f"Tracking "
                f"**{learning.get('tracking_cases', 0)}**\n"
                f"Completed "
                f"**{learning.get('completed_cases', 0)}**\n"
                f"Total Cases "
                f"**{learning.get('total_cases', 0)}**"
            ),

            inline=True,
        )


        completed_cases = int(
            learning.get(
                "completed_cases",
                0,
            )
            or 0
        )


        if completed_cases == 0:

            embed.add_field(
                name="Performance",

                value=(
                    "**CALIBRATING**\n"
                    "No verified 24H learning "
                    "outcomes have completed yet.\n\n"
                    "The bot is collecting "
                    "15m / 1h / 6h / 24h outcomes now."
                ),

                inline=False,
            )


            embed.set_footer(
                text=(
                    "Performance metrics activate "
                    "after completed 24H outcomes"
                )
            )


            await interaction.followup.send(
                embed=embed
            )

            return


        embed.add_field(
            name="Performance",

            value=(
                f"Win Rate "
                f"**{float(learning.get('win_rate', 0)):.2f}%**\n"
                f"Winners "
                f"**{learning.get('wins', 0)}**\n"
                f"Mixed / Failed "
                f"**{learning.get('losses_or_mixed', 0)}**"
            ),

            inline=True,
        )


        embed.add_field(
            name="Median Outcome",

            value=(
                f"15m "
                f"**{signed_percent(returns.get('15m', 0))}**\n"
                f"1h "
                f"**{signed_percent(returns.get('1h', 0))}**\n"
                f"6h "
                f"**{signed_percent(returns.get('6h', 0))}**\n"
                f"24h "
                f"**{signed_percent(returns.get('24h', 0))}**"
            ),

            inline=True,
        )


        embed.add_field(
            name="Risk / Reward",

            value=(
                f"Median Peak "
                f"**{signed_percent(returns.get('peak', 0))}**\n"
                f"Median Drawdown "
                f"**{signed_percent(returns.get('drawdown', 0))}**"
            ),

            inline=True,
        )


        embed.add_field(
            name="Model Health",

            value=(
                f"False Positives "
                f"**{model_health.get('false_positives', 0)}**\n"
                f"False Negatives "
                f"**{model_health.get('false_negatives', 0)}**"
            ),

            inline=True,
        )


        if best_bucket:

            embed.add_field(
                name="Best Score Range",

                value=(
                    f"Radar "
                    f"**{best_bucket.get('name', 'N/A')}**\n"
                    f"Win Rate "
                    f"**{float(best_bucket.get('win_rate', 0)):.2f}%**\n"
                    f"Samples "
                    f"**{best_bucket.get('count', 0)}**\n"
                    f"Median 24H "
                    f"**{signed_percent(best_bucket.get('median_24h', 0))}**"
                ),

                inline=True,
            )


        quality_lines = []


        for name in (
            "HIGH",
            "MEDIUM",
            "LOW",
        ):

            stats = (
                quality.get(
                    name
                )
            )


            if not stats:

                continue


            quality_lines.append(
                (
                    f"{name} "
                    f"**{float(stats.get('win_rate', 0)):.1f}%** "
                    f"({stats.get('count', 0)} cases)"
                )
            )


        if quality_lines:

            embed.add_field(
                name="Data Quality",

                value=(
                    "\n".join(
                        quality_lines
                    )
                ),

                inline=True,
            )


        embed.set_footer(
            text=(
                "More data does not equal better intelligence - "
                "verified performance does."
            )
        )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # WATCH
    # =========================================================

    @app_commands.command(
        name="watch",
        description="Watch a narrative for movement.",
    )
    @app_commands.describe(
        narrative="Narrative to watch"
    )
    async def watch(
        self,
        interaction: discord.Interaction,
        narrative: str,
    ):

        user_id = (
            interaction.user.id
        )


        name = (
            narrative
            .strip()
            .lower()
        )


        if user_id not in self.watchers:

            self.watchers[
                user_id
            ] = set()


        self.watchers[
            user_id
        ].add(
            name
        )


        embed = discord.Embed(
            title="Narrative Watch",

            description=(
                f"Watching "
                f"**{narrative}**.\n\n"
                "NarrativeRadar will track it "
                "during this bot session."
            ),
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


    # =========================================================
    # COMPARE
    # =========================================================

    @app_commands.command(
        name="compare",
        description="Compare two narratives.",
    )
    async def compare(
        self,
        interaction: discord.Interaction,
        first: str,
        second: str,
    ):

        await interaction.response.defer()


        result = (
            await asyncio.to_thread(
                self.service.compare,
                first,
                second,
            )
        )


        a = (
            result.get(
                "first"
            )
        )

        b = (
            result.get(
                "second"
            )
        )


        if not a or not b:

            await interaction.followup.send(
                (
                    "One or both narratives "
                    "could not be found."
                )
            )

            return


        embed = discord.Embed(
            title=(
                f"{a['name']} "
                f"vs "
                f"{b['name']}"
            )
        )


        embed.add_field(
            name=(
                a[
                    "name"
                ]
            ),

            value=(
                f"Score "
                f"**{a.get('score', 0)}**\n"
                f"Confidence "
                f"**{a.get('confidence', 0)}%**\n"
                f"Coins "
                f"**{a.get('coin_count', 0)}**\n"
                f"Average MC "
                f"**{money(a.get('avg_market_cap', 0))}**\n"
                f"Average Volume "
                f"**{money(a.get('avg_volume', 0))}**"
            ),

            inline=True,
        )


        embed.add_field(
            name=(
                b[
                    "name"
                ]
            ),

            value=(
                f"Score "
                f"**{b.get('score', 0)}**\n"
                f"Confidence "
                f"**{b.get('confidence', 0)}%**\n"
                f"Coins "
                f"**{b.get('coin_count', 0)}**\n"
                f"Average MC "
                f"**{money(b.get('avg_market_cap', 0))}**\n"
                f"Average Volume "
                f"**{money(b.get('avg_volume', 0))}**"
            ),

            inline=True,
        )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # TIMELINE
    # =========================================================

    @app_commands.command(
        name="timeline",
        description="Show how a narrative evolved.",
    )
    async def timeline(
        self,
        interaction: discord.Interaction,
        narrative: str,
    ):

        await interaction.response.defer()


        rows = (
            await asyncio.to_thread(
                self.service.timeline,
                narrative,
            )
        )


        embed = discord.Embed(
            title=(
                f"{narrative} Timeline"
            )
        )


        if not rows:

            embed.description = (
                "No historical timeline "
                "has been recorded yet."
            )


        else:

            lines = []


            for row in rows[
                -10:
            ]:

                time_object = (
                    row.get(
                        "time"
                    )
                )


                if time_object:

                    time_value = (
                        time_object.strftime(
                            "%H:%M"
                        )
                    )

                else:

                    time_value = "--:--"


                lines.append(
                    (
                        f"**{time_value}**\n"
                        f"Score "
                        f"`{row.get('score', 0)}` - "
                        f"{row.get('signal', 'UNKNOWN')} - "
                        f"{row.get('decision', 'UNKNOWN')}"
                    )
                )


            embed.description = (
                "\n\n|\nV\n\n".join(
                    lines
                )
            )


        await interaction.followup.send(
            embed=embed
        )


    # =========================================================
    # DISCOVER
    # =========================================================

    @app_commands.command(
        name="discover",
        description="Find unusual narratives starting to appear.",
    )
    async def discover(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.defer()


        rows = (
            await asyncio.to_thread(
                self.service.discover
            )
        )


        embed = discord.Embed(
            title="Unusual Activity"
        )


        if not rows:

            embed.description = (
                "Nothing unusual has crossed "
                "the discovery threshold yet."
            )


        else:

            for row in rows:

                embed.add_field(
                    name=(
                        row.get(
                            "name",
                            "Unknown",
                        )
                    ),

                    value=(
                        f"Launches "
                        f"**{row.get('launches', 0)}**\n"
                        f"Volume "
                        f"**{money(row.get('volume', 0))}**\n"
                        f"Confidence "
                        f"**{row.get('confidence', 0)}%**"
                    ),

                    inline=False,
                )


        await interaction.followup.send(
            embed=embed
        )


# =============================================================
# DISCORD EXTENSION ENTRY POINT
# =============================================================

async def setup(bot):

    await bot.add_cog(
        RadarCog(
            bot
        )
    )