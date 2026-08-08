import asyncio

import discord

from discord import app_commands
from discord.ext import commands

from collectors.dexscreener_discovery import (
    DexScreenerDiscoveryCollector,
)

from collectors.storage.coin_storage import (
    CoinStorage,
)

from core.intelligence.live_radar import (
    LiveRadar,
)

from core.intelligence.narrative_assignment import (
    NarrativeAssignmentEngine,
)

from core.learning.historical_calibration import (
    HistoricalCalibration,
)

from core.learning.pattern_similarity import (
    PatternSimilarityEngine,
)


class ManualIntelligenceCog(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        self.coin_storage = CoinStorage()

        self.dex = (
            DexScreenerDiscoveryCollector()
        )

        self.narrative_engine = (
            NarrativeAssignmentEngine()
        )

        self.calibration = (
            HistoricalCalibration()
        )

        self.similarity_engine = (
            PatternSimilarityEngine()
        )


    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _valid_address(
        address
    ):

        if not isinstance(
            address,
            str
        ):
            return False

        address = (
            address.strip()
        )

        return (
            32
            <= len(address)
            <= 44
        )


    @staticmethod
    def _safe_float(
        value,
        default=0.0
    ):

        try:

            return float(
                value
                if value is not None
                else default
            )

        except (
            TypeError,
            ValueError,
        ):

            return default


    # =========================================================
    # TOKEN METADATA
    # =========================================================

    def _token_metadata(
        self,
        address
    ):

        pairs = (
            self.dex.get_token_pairs(
                address
            )
        )


        if not pairs:

            return {
                "name": "Unknown",
                "symbol": "UNKNOWN",
                "topic": None,
                "pair": None,
            }


        best = max(
            pairs,
            key=lambda pair: (
                self._safe_float(
                    (
                        pair.get(
                            "liquidity"
                        )
                        or {}
                    ).get(
                        "usd"
                    )
                )
            )
        )


        base = (
            best.get(
                "baseToken"
            )
            or {}
        )

        quote = (
            best.get(
                "quoteToken"
            )
            or {}
        )


        if (
            base.get(
                "address"
            )
            == address
        ):

            token = base

        elif (
            quote.get(
                "address"
            )
            == address
        ):

            token = quote

        else:

            token = base


        name = (
            token.get(
                "name"
            )
            or "Unknown"
        )

        symbol = (
            token.get(
                "symbol"
            )
            or "UNKNOWN"
        )


        topic = (
            symbol
            .replace(
                "$",
                ""
            )
            .strip()
            .lower()
        )


        if topic in (
            "",
            "unknown",
        ):

            topic = (
                name
                .strip()
                .lower()
            )


        if topic in (
            "",
            "unknown",
        ):

            topic = None


        return {
            "name": name,
            "symbol": symbol,
            "topic": topic,
            "pair": best,
        }


    # =========================================================
    # THEME
    # =========================================================

    def _detected_theme(
        self,
        address,
        metadata
    ):

        candidate = {
            "coin_address": address,

            "name": (
                metadata.get(
                    "name",
                    ""
                )
            ),

            "symbol": (
                metadata.get(
                    "symbol",
                    ""
                )
            ),

            "source": (
                "manual_scan"
            ),

            "source_reasons": [
                "manual_scan"
            ],
        }


        matches = (
            self.narrative_engine
            .detect(
                candidate
            )
        )


        if not matches:

            return "UNKNOWN"


        return (
            matches[0][0]
        )


    # =========================================================
    # RUN SCAN
    # =========================================================

    def _run_scan(
        self,
        address
    ):

        metadata = (
            self._token_metadata(
                address
            )
        )


        coin = (
            self.coin_storage
            .get_or_create_coin(
                address
            )
        )


        radar = LiveRadar()


        result = radar.run(
            coin_id=coin.id,

            coin_address=address,

            signature_limit=20,

            social_topic=(
                metadata[
                    "topic"
                ]
            ),
        )


        theme = (
            self._detected_theme(
                address,
                metadata
            )
        )


        radar_data = (
            result[
                "radar"
            ]
        )


        analysis = (
            radar_data[
                "analysis"
            ]
        )


        signal = (
            radar_data[
                "radar"
            ][
                "signal"
            ]
        )


        decision = (
            radar_data[
                "radar"
            ][
                "decision"
            ]
        )


        market = (
            result[
                "collected"
            ].get(
                "market",
                {}
            )
        )


        calibration = (
            self.calibration.calibrate(
                narrative=theme,

                combined_score=(
                    analysis.get(
                        "combined_score",
                        0
                    )
                ),

                data_quality=(
                    analysis.get(
                        "data_quality",
                        0
                    )
                ),

                signal=(
                    signal.get(
                        "signal",
                        "UNKNOWN"
                    )
                ),

                risk=(
                    decision.get(
                        "risk",
                        "UNKNOWN"
                    )
                ),

                base_confidence=(
                    signal.get(
                        "confidence",
                        0
                    )
                ),
            )
        )


        current_features = (
            self.similarity_engine
            .build_current_features(
                narrative=theme,
                analysis=analysis,
                market=market,
                signal=signal,
                decision=decision,
            )
        )


        similarity = (
            self.similarity_engine
            .match(
                current_features
            )
        )


        return {
            "metadata": metadata,
            "result": result,
            "theme": theme,
            "calibration": calibration,
            "similarity": similarity,
        }


    # =========================================================
    # DEX VOLUME DATA
    # =========================================================

    def _volume_data(
        self,
        metadata
    ):

        pair = (
            metadata.get(
                "pair"
            )
            or {}
        )

        volumes = (
            pair.get(
                "volume"
            )
            or {}
        )


        return {
            "h1": self._safe_float(
                volumes.get(
                    "h1"
                )
            ),

            "h6": self._safe_float(
                volumes.get(
                    "h6"
                )
            ),

            "h24": self._safe_float(
                volumes.get(
                    "h24"
                )
            ),
        }


    # =========================================================
    # SHORT HISTORY TEXT
    # =========================================================

    def _history_text(
        self,
        calibration,
        similarity
    ):

        calibrated_count = int(
            calibration.get(
                "occurrences",
                0
            )
            or 0
        )

        similar_count = int(
            similarity.get(
                "match_count",
                0
            )
            or 0
        )


        if (
            calibrated_count < 10
            and
            similar_count < 10
        ):

            completed = max(
                calibrated_count,
                similar_count
            )

            return (
                f"Learning - "
                f"**{completed} completed matches**"
            )


        parts = []


        if calibrated_count >= 10:

            parts.append(
                (
                    f"Pattern: "
                    f"**{calibration.get('success_rate', 0):.1f}%** "
                    f"success across "
                    f"**{calibrated_count}** cases"
                )
            )


        if similar_count >= 10:

            parts.append(
                (
                    f"Similar setups: "
                    f"**{similarity.get('weighted_success_rate', 0):.1f}%** "
                    f"success across "
                    f"**{similar_count}** matches"
                )
            )


        return (
            "\n".join(
                parts
            )
        )


    # =========================================================
    # CLEAN RADAR TAKE
    # =========================================================

    def _radar_take(
        self,
        analysis,
        signal,
        decision,
        calibration,
        similarity
    ):

        market = (
            self._safe_float(
                analysis.get(
                    "market_score"
                )
            )
        )

        social = (
            self._safe_float(
                analysis.get(
                    "social_score"
                )
            )
        )

        wallet = (
            self._safe_float(
                analysis.get(
                    "wallet_score"
                )
            )
        )

        combined = (
            self._safe_float(
                analysis.get(
                    "combined_score"
                )
            )
        )

        quality = (
            self._safe_float(
                analysis.get(
                    "data_quality"
                )
            )
        )


        strong = []
        weak = []


        if market >= 60:

            strong.append(
                "market"
            )

        elif market < 35:

            weak.append(
                "market"
            )


        if social >= 60:

            strong.append(
                "social"
            )

        elif social < 30:

            weak.append(
                "social"
            )


        if wallet >= 60:

            strong.append(
                "wallet"
            )

        elif wallet < 30:

            weak.append(
                "wallet"
            )


        decision_name = (
            decision.get(
                "decision",
                "IGNORE"
            )
        )


        if (
            decision_name
            in (
                "ENTER",
                "ENTER_WATCH",
            )
            and
            combined >= 70
        ):

            opening = (
                "Strong setup with "
                "multi-source confirmation."
            )


        elif decision_name == "MONITOR":

            opening = (
                "Worth watching, but "
                "confirmation is incomplete."
            )


        else:

            opening = (
                "Not enough evidence "
                "for a strong setup yet."
            )


        details = []


        if strong:

            details.append(
                (
                    "Strength: "
                    + ", ".join(
                        strong
                    )
                    + "."
                )
            )


        if weak:

            details.append(
                (
                    "Missing: "
                    + ", ".join(
                        weak
                    )
                    + "."
                )
            )


        if quality < 67:

            details.append(
                "Data coverage is still limited."
            )


        similar_count = int(
            similarity.get(
                "match_count",
                0
            )
            or 0
        )


        if similar_count >= 10:

            historical_rate = (
                self._safe_float(
                    similarity.get(
                        "weighted_success_rate"
                    )
                )
            )


            if historical_rate >= 65:

                details.append(
                    "History supports the setup."
                )


            elif historical_rate <= 40:

                details.append(
                    "History warns against the setup."
                )


        return (
            opening
            + " "
            + " ".join(
                details
            )
        )


    # =========================================================
    # /SCAN
    # =========================================================

    @app_commands.command(
        name="scan",
        description=(
            "Run a fresh live intelligence "
            "scan on a Solana token."
        )
    )
    @app_commands.describe(
        coin_address=(
            "Solana token mint address"
        )
    )
    async def scan(
        self,
        interaction: discord.Interaction,
        coin_address: str
    ):

        address = (
            coin_address.strip()
        )


        if not self._valid_address(
            address
        ):

            await interaction.response.send_message(
                (
                    "That does not look like "
                    "a valid Solana token address."
                ),
                ephemeral=True,
            )

            return


        await interaction.response.defer()


        try:

            package = await asyncio.to_thread(
                self._run_scan,
                address
            )


        except Exception as error:

            await interaction.followup.send(
                (
                    "The live scan failed.\n\n"
                    f"`{error}`"
                )
            )

            return


        metadata = (
            package[
                "metadata"
            ]
        )

        result = (
            package[
                "result"
            ]
        )

        theme = (
            package[
                "theme"
            ]
        )

        calibration = (
            package[
                "calibration"
            ]
        )

        similarity = (
            package[
                "similarity"
            ]
        )


        collected = (
            result[
                "collected"
            ]
        )

        radar = (
            result[
                "radar"
            ]
        )

        analysis = (
            radar[
                "analysis"
            ]
        )

        signal = (
            radar[
                "radar"
            ][
                "signal"
            ]
        )

        decision = (
            radar[
                "radar"
            ][
                "decision"
            ]
        )

        live_narrative = (
            radar[
                "narrative"
            ][
                "narrative"
            ][
                "narrative"
            ]
        )

        market = (
            collected.get(
                "market",
                {}
            )
        )


        volumes = (
            self._volume_data(
                metadata
            )
        )


        price = (
            self._safe_float(
                market.get(
                    "price"
                )
            )
        )

        market_cap = (
            self._safe_float(
                market.get(
                    "market_cap"
                )
            )
        )

        liquidity = (
            self._safe_float(
                market.get(
                    "liquidity"
                )
            )
        )


        symbol = (
            metadata.get(
                "symbol"
            )
            or "UNKNOWN"
        )

        name = (
            metadata.get(
                "name"
            )
            or symbol
        )


        embed = discord.Embed(
            title=(
                f"{name} - {symbol}"
            ),

            description=(
                f"`{address}`\n"
                f"**{theme}** | "
                f"**{format_state(live_narrative)}**"
            ),
        )


        embed.add_field(
            name="Market",
            value=(
                f"Price **${price:,.10g}**\n"
                f"MC **{money(market_cap)}**\n"
                f"Liq **{money(liquidity)}**"
            ),
            inline=True,
        )


        embed.add_field(
            name="Volume",
            value=(
                f"1H **{money(volumes['h1'])}**\n"
                f"6H **{money(volumes['h6'])}**\n"
                f"24H **{money(volumes['h24'])}**"
            ),
            inline=True,
        )


        embed.add_field(
            name="Radar",
            value=(
                f"**{analysis['combined_score']}/100**\n"
                f"Confidence "
                f"**{signal['confidence']}%**\n"
                f"Risk **{decision['risk']}**"
            ),
            inline=True,
        )


        embed.add_field(
            name="Signals",
            value=(
                f"Market **{analysis['market_score']}** | "
                f"Social **{analysis['social_score']}** | "
                f"Wallet **{analysis['wallet_score']}**"
            ),
            inline=False,
        )


        embed.add_field(
            name="Status",
            value=(
                f"**{radar_status(analysis, signal, decision)}**"
            ),
            inline=False,
        )


        embed.add_field(
            name="History",
            value=(
                self._history_text(
                    calibration,
                    similarity
                )
            ),
            inline=False,
        )


        embed.add_field(
            name="Radar Take",
            value=(
                self._radar_take(
                    analysis,
                    signal,
                    decision,
                    calibration,
                    similarity
                )
            ),
            inline=False,
        )


        embed.set_footer(
            text=(
                f"Data Quality "
                f"{analysis['data_quality']}% "
                f"| Live evidence + verified history"
            )
        )


        await interaction.followup.send(
            embed=embed
        )


async def setup(
    bot
):

    await bot.add_cog(
        ManualIntelligenceCog(
            bot
        )
    )


# =============================================================
# FORMAT HELPERS
# =============================================================

def money(
    value
):

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


def format_state(
    value
):

    value = str(
        value
        or "UNKNOWN"
    )


    return (
        value
        .replace(
            "_",
            " "
        )
        .title()
    )


def radar_status(
    analysis,
    signal,
    decision
):

    score = float(
        analysis.get(
            "combined_score",
            0
        )
        or 0
    )

    confidence = int(
        signal.get(
            "confidence",
            0
        )
        or 0
    )

    quality = float(
        analysis.get(
            "data_quality",
            0
        )
        or 0
    )

    decision_name = str(
        decision.get(
            "decision",
            "IGNORE"
        )
    ).upper()


    # =========================================================
    # GREEN
    #
    # Rare. Strong live evidence + strong confidence +
    # sufficient data quality + positive engine decision.
    # =========================================================

    if (
        score >= 80
        and
        confidence >= 70
        and
        quality >= 66
        and
        decision_name
        in (
            "ENTER",
            "ENTER_WATCH",
        )
    ):

        return (
            "🟢 WATCH IT LIKE UR LIFE DEPENDS ON IT"
        )


    # =========================================================
    # PURPLE
    #
    # Interesting setup worth monitoring.
    # =========================================================

    if (
        score >= 55
        and
        decision_name
        in (
            "MONITOR",
            "ENTER_WATCH",
            "ENTER",
        )
    ):

        return (
            "🟣 WATCH"
        )


    # =========================================================
    # RED
    #
    # Insufficient setup quality / confirmation.
    # =========================================================

    return (
        "🔴 AVOID"
    )