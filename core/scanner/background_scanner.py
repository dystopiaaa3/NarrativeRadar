import time
import threading

from datetime import (
    datetime,
    timedelta,
)

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from collectors.dexscreener_discovery import (
    DexScreenerDiscoveryCollector,
)

from collectors.pumpfun import (
    PumpFunCollector,
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

from core.scanner.candidate_queue import (
    CandidateQueue,
)

from core.learning.autonomous_sampler import (
    AutonomousLearningSampler,
)


class BackgroundScanner:

    def __init__(
        self,
        discovery_limit: int = 20,
        pumpfun_limit: int = 30,
        pumpfun_enrich_limit: int = 8,
        batch_size: int = 3,
        signature_limit: int = 20,
        max_workers: int = 3,
        cycle_seconds: int = 20,
        pump_pending_minutes: int = 15,
        pump_pending_max: int = 500,
    ):

        self.discovery_limit = max(
            5,
            min(
                int(
                    discovery_limit
                ),
                100,
            ),
        )

        self.pumpfun_limit = max(
            5,
            min(
                int(
                    pumpfun_limit
                ),
                100,
            ),
        )

        self.pumpfun_enrich_limit = max(
            1,
            min(
                int(
                    pumpfun_enrich_limit
                ),
                25,
            ),
        )

        self.batch_size = max(
            1,
            min(
                int(
                    batch_size
                ),
                5,
            ),
        )

        self.signature_limit = max(
            5,
            min(
                int(
                    signature_limit
                ),
                50,
            ),
        )

        self.max_workers = max(
            1,
            min(
                int(
                    max_workers
                ),
                5,
            ),
        )

        self.cycle_seconds = max(
            10,
            int(
                cycle_seconds
            ),
        )

        self.pump_pending_minutes = max(
            2,
            int(
                pump_pending_minutes
            ),
        )

        self.pump_pending_max = max(
            50,
            int(
                pump_pending_max
            ),
        )


        # =====================================================
        # DISCOVERY SOURCES
        # =====================================================

        self.dexscreener = (
            DexScreenerDiscoveryCollector()
        )

        self.pumpfun = (
            PumpFunCollector()
        )


        # =====================================================
        # QUEUE
        # =====================================================

        self.queue = (
            CandidateQueue(
                cooldown_minutes=10
            )
        )


        # =====================================================
        # PUMP PENDING POOL
        #
        # key:
        #     mint
        #
        # value:
        #     candidate + pending_since
        #
        # Pump.fun launches stay here until DexScreener has
        # enough data to make the token worth a deep scan.
        # =====================================================

        self._pump_pending = {}
        self._pump_pending_lock = (
            threading.Lock()
        )


        # =====================================================
        # SERVICES
        # =====================================================

        self.coin_storage = (
            CoinStorage()
        )

        self.narrative_engine = (
            NarrativeAssignmentEngine()
        )

        self.learning_sampler = (
            AutonomousLearningSampler(
                max_cases_per_hour=12,
                coin_cooldown_hours=24,
                minimum_data_quality=33.0,
                strong_score=55.0,
                control_sample_rate=4,
            )
        )


        self.stop_event = (
            threading.Event()
        )

        self._pump_started = False


    # =========================================================
    # SAFE HELPERS
    # =========================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
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


    @staticmethod
    def _safe_int(
        value,
        default=0,
    ):

        try:

            return int(
                float(
                    value
                    if value is not None
                    else default
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return default


    @staticmethod
    def _valid_address(
        value,
    ):

        if not isinstance(
            value,
            str,
        ):

            return False

        value = (
            value.strip()
        )

        return (
            32
            <= len(
                value
            )
            <= 44
        )


    @staticmethod
    def _has_usable_market_data(
        candidate,
    ):

        try:

            price = float(
                candidate.get(
                    "price",
                    0,
                )
                or 0
            )

            market_cap = float(
                candidate.get(
                    "market_cap",
                    0,
                )
                or 0
            )

            liquidity = float(
                candidate.get(
                    "liquidity",
                    0,
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            return False


        # For learning we eventually need a real T0 price.
        # Require all three core market fields.

        return (
            price > 0
            and
            market_cap > 0
            and
            liquidity > 0
        )


    # =========================================================
    # PUMP START
    # =========================================================

    def _ensure_pumpfun_started(
        self,
    ):

        if self._pump_started:

            return

        self.pumpfun.start()

        self._pump_started = True


    # =========================================================
    # SOCIAL TOPIC
    # =========================================================

    def _social_topic(
        self,
        candidate,
    ):

        symbol = str(
            candidate.get(
                "symbol",
                "",
            )
            or ""
        ).strip()

        name = str(
            candidate.get(
                "name",
                "",
            )
            or ""
        ).strip()


        if symbol:

            return (
                symbol
                .replace(
                    "$",
                    "",
                )
                .strip()
                .lower()
            )


        if name:

            return (
                name
                .strip()
                .lower()
            )


        return None


    # =========================================================
    # COIN
    # =========================================================

    def _get_coin(
        self,
        candidate,
    ):

        return (
            self.coin_storage
            .get_or_create_coin(
                candidate[
                    "coin_address"
                ]
            )
        )


    # =========================================================
    # DEEP SCAN
    # =========================================================

    def _scan_candidate(
        self,
        candidate,
    ):

        started = (
            time.time()
        )

        address = (
            candidate[
                "coin_address"
            ]
        )

        symbol = (
            candidate.get(
                "symbol"
            )
            or
            "UNKNOWN"
        )


        try:

            coin = (
                self._get_coin(
                    candidate
                )
            )

            topic = (
                self._social_topic(
                    candidate
                )
            )

            radar = (
                LiveRadar()
            )

            result = (
                radar.run(
                    coin_id=(
                        coin.id
                    ),

                    coin_address=(
                        address
                    ),

                    signature_limit=(
                        self.signature_limit
                    ),

                    social_topic=(
                        topic
                    ),
                )
            )


            narrative_result = (
                self.narrative_engine.assign(
                    coin_id=(
                        coin.id
                    ),

                    candidate=(
                        candidate
                    ),
                )
            )


            learning = (
                self.learning_sampler.record(
                    coin_id=(
                        coin.id
                    ),

                    candidate=(
                        candidate
                    ),

                    result=(
                        result
                    ),

                    narrative_result=(
                        narrative_result
                    ),
                )
            )


            analysis = (
                result[
                    "radar"
                ][
                    "analysis"
                ]
            )

            signal = (
                result[
                    "radar"
                ][
                    "radar"
                ][
                    "signal"
                ]
            )

            decision = (
                result[
                    "radar"
                ][
                    "radar"
                ][
                    "decision"
                ]
            )


            return {
                "success": True,

                "coin_id": (
                    coin.id
                ),

                "coin_address": (
                    address
                ),

                "symbol": (
                    symbol
                ),

                "priority_score": (
                    candidate.get(
                        "priority_score",
                        0,
                    )
                ),

                "discovery_sources": (
                    candidate.get(
                        "discovery_sources",
                        candidate.get(
                            "sources",
                            [],
                        ),
                    )
                ),

                "source_count": (
                    candidate.get(
                        "source_count",
                        1,
                    )
                ),

                "cross_source": (
                    candidate.get(
                        "cross_source",
                        False,
                    )
                ),

                "combined_score": (
                    analysis.get(
                        "combined_score",
                        0,
                    )
                ),

                "data_quality": (
                    analysis.get(
                        "data_quality",
                        0,
                    )
                ),

                "signal": (
                    signal.get(
                        "signal",
                        "UNKNOWN",
                    )
                ),

                "confidence": (
                    signal.get(
                        "confidence",
                        0,
                    )
                ),

                "decision": (
                    decision.get(
                        "decision",
                        "UNKNOWN",
                    )
                ),

                "risk": (
                    decision.get(
                        "risk",
                        "UNKNOWN",
                    )
                ),

                "saved_result_id": (
                    result.get(
                        "saved_result_id"
                    )
                ),

                "saved_market_observation_id": (
                    result.get(
                        "saved_market_observation_id"
                    )
                ),

                "narratives": (
                    narrative_result.get(
                        "assignments",
                        [],
                    )
                ),

                "narrative_count": (
                    narrative_result.get(
                        "count",
                        0,
                    )
                ),

                "learning_case_created": (
                    learning.get(
                        "created",
                        False,
                    )
                ),

                "learning_case_id": (
                    learning.get(
                        "feed_case_id"
                    )
                ),

                "learning_sample_type": (
                    learning.get(
                        "sample_type"
                    )
                ),

                "learning_reason": (
                    learning.get(
                        "reason"
                    )
                ),

                "seconds": round(
                    time.time()
                    - started,
                    2,
                ),

                "error": None,
            }


        except Exception as error:

            return {
                "success": False,

                "coin_address": (
                    address
                ),

                "symbol": (
                    symbol
                ),

                "priority_score": (
                    candidate.get(
                        "priority_score",
                        0,
                    )
                ),

                "discovery_sources": (
                    candidate.get(
                        "discovery_sources",
                        candidate.get(
                            "sources",
                            [],
                        ),
                    )
                ),

                "cross_source": (
                    candidate.get(
                        "cross_source",
                        False,
                    )
                ),

                "seconds": round(
                    time.time()
                    - started,
                    2,
                ),

                "error": str(
                    error
                ),
            }


    # =========================================================
    # DEXSCREENER NORMAL DISCOVERY
    # =========================================================

    def _discover_dexscreener(
        self,
    ):

        try:

            result = (
                self.dexscreener.discover(
                    self.discovery_limit
                )
            )

            candidates = (
                result.get(
                    "candidates",
                    [],
                )
            )


            for candidate in candidates:

                candidate[
                    "discovery_sources"
                ] = [
                    "dexscreener"
                ]

                candidate[
                    "source_count"
                ] = 1

                candidate[
                    "cross_source"
                ] = False

                candidate[
                    "discovery_confidence"
                ] = 60.0


            return {
                "success": bool(
                    result.get(
                        "success"
                    )
                ),

                "candidates": (
                    candidates
                ),

                "error": (
                    result.get(
                        "error"
                    )
                ),
            }


        except Exception as error:

            return {
                "success": False,
                "candidates": [],
                "error": str(
                    error
                ),
            }


    # =========================================================
    # PUMP REALTIME BUFFER
    # =========================================================

    def _discover_pumpfun(
        self,
    ):

        self._ensure_pumpfun_started()

        candidates = (
            self.pumpfun.drain(
                limit=(
                    self.pumpfun_limit
                )
            )
        )

        return {
            "success": True,

            "candidates": (
                candidates
            ),

            "status": (
                self.pumpfun.status()
            ),

            "error": None,
        }


    # =========================================================
    # PENDING PUMP TOKENS
    # =========================================================

    def _add_pending_pump(
        self,
        candidates,
    ):

        now = (
            datetime.utcnow()
        )


        with self._pump_pending_lock:

            for candidate in candidates:

                address = (
                    candidate.get(
                        "coin_address"
                    )
                )

                if not self._valid_address(
                    address
                ):

                    continue


                address = (
                    address.strip()
                )


                existing = (
                    self._pump_pending.get(
                        address
                    )
                )


                if existing:

                    existing.update(
                        candidate
                    )

                    existing[
                        "_pending_since"
                    ] = (
                        existing.get(
                            "_pending_since"
                        )
                        or
                        now
                    )

                else:

                    item = dict(
                        candidate
                    )

                    item[
                        "_pending_since"
                    ] = (
                        now
                    )

                    self._pump_pending[
                        address
                    ] = (
                        item
                    )


            # Hard memory ceiling.

            if (
                len(
                    self._pump_pending
                )
                >
                self.pump_pending_max
            ):

                ordered = sorted(
                    self._pump_pending.items(),

                    key=lambda pair: (
                        pair[1].get(
                            "_pending_since",
                            now,
                        )
                    ),
                )


                remove_count = (
                    len(
                        self._pump_pending
                    )
                    -
                    self.pump_pending_max
                )


                for (
                    address,
                    _
                ) in ordered[
                    :remove_count
                ]:

                    self._pump_pending.pop(
                        address,
                        None,
                    )


    def _expire_pending_pump(
        self,
    ):

        cutoff = (
            datetime.utcnow()
            - timedelta(
                minutes=(
                    self.pump_pending_minutes
                )
            )
        )

        expired = 0


        with self._pump_pending_lock:

            addresses = list(
                self._pump_pending.keys()
            )


            for address in addresses:

                candidate = (
                    self._pump_pending[
                        address
                    ]
                )

                pending_since = (
                    candidate.get(
                        "_pending_since"
                    )
                )


                if (
                    pending_since
                    and
                    pending_since
                    < cutoff
                ):

                    self._pump_pending.pop(
                        address,
                        None,
                    )

                    expired += 1


        return expired


    def _pending_pump_batch(
        self,
    ):

        with self._pump_pending_lock:

            values = list(
                self._pump_pending.values()
            )


        values.sort(
            key=lambda item: (
                item.get(
                    "_pending_since",
                    datetime.utcnow(),
                )
            )
        )


        # Retry oldest first so new events don't starve.

        return values[
            :self.pumpfun_enrich_limit
        ]


    def _remove_pending_pump(
        self,
        address,
    ):

        with self._pump_pending_lock:

            self._pump_pending.pop(
                address,
                None,
            )


    def _pending_pump_size(
        self,
    ):

        with self._pump_pending_lock:

            return len(
                self._pump_pending
            )


    # =========================================================
    # DEX ENRICH ONE PUMP TOKEN
    # =========================================================

    def _enrich_pump_candidate(
        self,
        candidate,
    ):

        address = (
            candidate[
                "coin_address"
            ]
        )


        try:

            pairs = (
                self.dexscreener
                .get_token_pairs(
                    address
                )
            )

        except Exception:

            return candidate


        if not pairs:

            return candidate


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
            ),
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


        token = (
            base
        )


        if (
            quote.get(
                "address"
            )
            == address
        ):

            token = (
                quote
            )


        liquidity_data = (
            best.get(
                "liquidity"
            )
            or {}
        )

        volume_data = (
            best.get(
                "volume"
            )
            or {}
        )

        change_data = (
            best.get(
                "priceChange"
            )
            or {}
        )

        txn_data = (
            best.get(
                "txns"
            )
            or {}
        )

        h1_txns = (
            txn_data.get(
                "h1"
            )
            or {}
        )


        enriched = dict(
            candidate
        )


        enriched.pop(
            "_pending_since",
            None,
        )


        if not enriched.get(
            "name"
        ):

            enriched[
                "name"
            ] = (
                token.get(
                    "name"
                )
                or ""
            )


        if not enriched.get(
            "symbol"
        ):

            enriched[
                "symbol"
            ] = (
                token.get(
                    "symbol"
                )
                or ""
            )


        enriched[
            "price"
        ] = (
            self._safe_float(
                best.get(
                    "priceUsd"
                )
            )
        )


        enriched[
            "market_cap"
        ] = (
            self._safe_float(
                best.get(
                    "marketCap",
                    best.get(
                        "fdv",
                        0,
                    )
                )
            )
        )


        enriched[
            "liquidity"
        ] = (
            self._safe_float(
                liquidity_data.get(
                    "usd"
                )
            )
        )


        enriched[
            "volume_24h"
        ] = (
            self._safe_float(
                volume_data.get(
                    "h24"
                )
            )
        )


        enriched[
            "price_change_1h"
        ] = (
            self._safe_float(
                change_data.get(
                    "h1"
                )
            )
        )


        enriched[
            "price_change_24h"
        ] = (
            self._safe_float(
                change_data.get(
                    "h24"
                )
            )
        )


        enriched[
            "buys_1h"
        ] = (
            self._safe_int(
                h1_txns.get(
                    "buys"
                )
            )
        )


        enriched[
            "sells_1h"
        ] = (
            self._safe_int(
                h1_txns.get(
                    "sells"
                )
            )
        )


        enriched[
            "pair_created_at"
        ] = (
            best.get(
                "pairCreatedAt"
            )
        )


        # Only mark cross-source after real market data exists.

        if self._has_usable_market_data(
            enriched
        ):

            enriched[
                "discovery_sources"
            ] = [
                "pumpfun",
                "dexscreener",
            ]

            enriched[
                "source_count"
            ] = 2

            enriched[
                "cross_source"
            ] = True

            enriched[
                "discovery_confidence"
            ] = 100.0

            enriched[
                "source_reasons"
            ] = [
                "new_token",
                "dex_validated",
            ]


        return enriched


    # =========================================================
    # RETRY PENDING PUMP
    # =========================================================

    def _retry_pending_pump(
        self,
    ):

        self._expire_pending_pump()

        selected = (
            self._pending_pump_batch()
        )


        if not selected:

            return {
                "ready": [],
                "retried": 0,
                "still_pending": (
                    self._pending_pump_size()
                ),
            }


        ready = []


        with ThreadPoolExecutor(
            max_workers=min(
                4,
                len(
                    selected
                ),
            )
        ) as executor:

            future_map = {
                executor.submit(
                    self._enrich_pump_candidate,
                    candidate,
                ): candidate

                for candidate
                in selected
            }


            for future in as_completed(
                future_map
            ):

                original = (
                    future_map[
                        future
                    ]
                )

                address = (
                    original[
                        "coin_address"
                    ]
                )


                try:

                    enriched = (
                        future.result()
                    )

                except Exception:

                    continue


                if self._has_usable_market_data(
                    enriched
                ):

                    ready.append(
                        enriched
                    )

                    self._remove_pending_pump(
                        address
                    )


        return {
            "ready": (
                ready
            ),

            "retried": len(
                selected
            ),

            "still_pending": (
                self._pending_pump_size()
            ),
        }


    # =========================================================
    # MERGE
    # =========================================================

    def _merge_candidates(
        self,
        candidates,
    ):

        merged = {}


        for candidate in candidates:

            address = (
                candidate.get(
                    "coin_address"
                )
            )


            if not self._valid_address(
                address
            ):

                continue


            address = (
                address.strip()
            )


            if address not in merged:

                merged[
                    address
                ] = dict(
                    candidate
                )

                continue


            existing = (
                merged[
                    address
                ]
            )


            if (
                not existing.get(
                    "name"
                )
                and
                candidate.get(
                    "name"
                )
            ):

                existing[
                    "name"
                ] = (
                    candidate[
                        "name"
                    ]
                )


            if (
                not existing.get(
                    "symbol"
                )
                and
                candidate.get(
                    "symbol"
                )
            ):

                existing[
                    "symbol"
                ] = (
                    candidate[
                        "symbol"
                    ]
                )


            for field in (
                "price",
                "market_cap",
                "liquidity",
                "volume_24h",
            ):

                incoming = (
                    self._safe_float(
                        candidate.get(
                            field
                        )
                    )
                )

                current = (
                    self._safe_float(
                        existing.get(
                            field
                        )
                    )
                )


                if incoming > current:

                    existing[
                        field
                    ] = (
                        incoming
                    )


            sources = set(
                existing.get(
                    "discovery_sources",
                    []
                )
            )

            sources.update(
                candidate.get(
                    "discovery_sources",
                    []
                )
            )


            existing[
                "discovery_sources"
            ] = sorted(
                sources
            )

            existing[
                "source_count"
            ] = len(
                sources
            )

            existing[
                "cross_source"
            ] = (
                len(
                    sources
                )
                >= 2
            )


            if existing[
                "cross_source"
            ]:

                existing[
                    "discovery_confidence"
                ] = 100.0


        return list(
            merged.values()
        )


    # =========================================================
    # DISCOVERY
    # =========================================================

    def discover(
        self,
    ):

        self._ensure_pumpfun_started()


        with ThreadPoolExecutor(
            max_workers=2
        ) as executor:

            dex_future = (
                executor.submit(
                    self._discover_dexscreener
                )
            )

            pump_future = (
                executor.submit(
                    self._discover_pumpfun
                )
            )


            dex_result = (
                dex_future.result()
            )

            pump_result = (
                pump_future.result()
            )


        dex_candidates = (
            dex_result.get(
                "candidates",
                [],
            )
        )

        new_pump_candidates = (
            pump_result.get(
                "candidates",
                [],
            )
        )


        # Fresh Pump.fun events go into pending storage.
        # They are NOT added to CandidateQueue yet.

        self._add_pending_pump(
            new_pump_candidates
        )


        retry = (
            self._retry_pending_pump()
        )

        ready_pump = (
            retry[
                "ready"
            ]
        )


        candidates = (
            self._merge_candidates(
                list(
                    dex_candidates
                )
                +
                list(
                    ready_pump
                )
            )
        )


        added = (
            self.queue.add_many(
                candidates
            )
        )


        cross_source_count = sum(
            1
            for candidate
            in candidates
            if candidate.get(
                "cross_source"
            )
        )


        pump_status = (
            self.pumpfun.status()
        )


        return {
            "success": (
                bool(
                    dex_result.get(
                        "success"
                    )
                )
                or
                bool(
                    ready_pump
                )
            ),

            "discovered": len(
                candidates
            ),

            "dexscreener_discovered": len(
                dex_candidates
            ),

            "pumpfun_discovered": len(
                new_pump_candidates
            ),

            "pumpfun_ready": len(
                ready_pump
            ),

            "pumpfun_retried": (
                retry[
                    "retried"
                ]
            ),

            "pumpfun_pending": (
                retry[
                    "still_pending"
                ]
            ),

            "cross_source": (
                cross_source_count
            ),

            "added": (
                added
            ),

            "queue_size": (
                self.queue.size()
            ),

            "sources": {
                "dexscreener": {
                    "success": (
                        dex_result.get(
                            "success",
                            False,
                        )
                    ),

                    "count": len(
                        dex_candidates
                    ),

                    "error": (
                        dex_result.get(
                            "error"
                        )
                    ),
                },

                "pumpfun": {
                    **pump_status,

                    "new": len(
                        new_pump_candidates
                    ),

                    "ready": len(
                        ready_pump
                    ),

                    "pending": (
                        retry[
                            "still_pending"
                        ]
                    ),
                },
            },

            "error": None,
        }


    # =========================================================
    # SCAN BATCH
    # =========================================================

    def scan_batch(
        self,
    ):

        candidates = (
            self.queue.pop_batch(
                self.batch_size
            )
        )


        if not candidates:

            return []


        results = []


        with ThreadPoolExecutor(
            max_workers=(
                self.max_workers
            )
        ) as executor:

            future_map = {
                executor.submit(
                    self._scan_candidate,
                    candidate,
                ): candidate

                for candidate
                in candidates
            }


            for future in as_completed(
                future_map
            ):

                candidate = (
                    future_map[
                        future
                    ]
                )


                try:

                    result = (
                        future.result()
                    )

                except Exception as error:

                    result = {
                        "success": False,

                        "coin_address": (
                            candidate[
                                "coin_address"
                            ]
                        ),

                        "symbol": (
                            candidate.get(
                                "symbol",
                                "UNKNOWN",
                            )
                        ),

                        "error": str(
                            error
                        ),
                    }


                results.append(
                    result
                )


        results.sort(
            key=lambda item: (
                item.get(
                    "combined_score",
                    0,
                )
            ),
            reverse=True,
        )


        return results


    # =========================================================
    # ONE CYCLE
    # =========================================================

    def run_once(
        self,
    ):

        started = (
            time.time()
        )

        discovery = (
            self.discover()
        )

        scans = (
            self.scan_batch()
            if discovery.get(
                "success"
            )
            else []
        )


        successful = sum(
            1
            for item
            in scans
            if item.get(
                "success"
            )
        )

        failed = (
            len(
                scans
            )
            -
            successful
        )

        narrative_assignments = sum(
            int(
                item.get(
                    "narrative_count",
                    0,
                )
                or 0
            )
            for item
            in scans
            if item.get(
                "success"
            )
        )

        learning_cases = sum(
            1
            for item
            in scans
            if item.get(
                "learning_case_created"
            )
        )


        return {
            "success": (
                discovery.get(
                    "success",
                    False,
                )
            ),

            "discovery": (
                discovery
            ),

            "scans": (
                scans
            ),

            "scanned": len(
                scans
            ),

            "successful": (
                successful
            ),

            "failed": (
                failed
            ),

            "narrative_assignments": (
                narrative_assignments
            ),

            "learning_cases_created": (
                learning_cases
            ),

            "queue_remaining": (
                self.queue.size()
            ),

            "cycle_seconds": round(
                time.time()
                - started,
                2,
            ),
        }


    # =========================================================
    # FOREVER
    # =========================================================

    def run_forever(
        self,
    ):

        self._ensure_pumpfun_started()


        print(
            "=" * 65
        )

        print(
            "NarrativeRadar Background Scanner ONLINE"
        )

        print(
            f"Cycle interval: "
            f"{self.cycle_seconds}s"
        )

        print(
            f"Dex discovery limit: "
            f"{self.discovery_limit}"
        )

        print(
            f"Pump.fun buffer/cycle: "
            f"{self.pumpfun_limit}"
        )

        print(
            f"Pump.fun retries/cycle: "
            f"{self.pumpfun_enrich_limit}"
        )

        print(
            f"Deep scans/cycle: "
            f"{self.batch_size}"
        )

        print(
            "Silent autonomous learning: ON"
        )

        print(
            "=" * 65
        )


        while not self.stop_event.is_set():

            try:

                result = (
                    self.run_once()
                )

                discovery = (
                    result[
                        "discovery"
                    ]
                )


                print(
                    "\n"
                    + "=" * 65
                )

                print(
                    "SCAN CYCLE COMPLETE"
                )

                print(
                    "=" * 65
                )


                print(
                    "DexScreener:",
                    discovery.get(
                        "dexscreener_discovered",
                        0,
                    )
                )

                print(
                    "Pump.fun new:",
                    discovery.get(
                        "pumpfun_discovered",
                        0,
                    )
                )

                print(
                    "Pump.fun ready:",
                    discovery.get(
                        "pumpfun_ready",
                        0,
                    )
                )

                print(
                    "Pump.fun pending:",
                    discovery.get(
                        "pumpfun_pending",
                        0,
                    )
                )

                print(
                    "Cross-source:",
                    discovery.get(
                        "cross_source",
                        0,
                    )
                )

                print(
                    "Added:",
                    discovery.get(
                        "added",
                        0,
                    )
                )

                print(
                    "Deep scanned:",
                    result[
                        "scanned"
                    ]
                )

                print(
                    "Learning cases:",
                    result[
                        "learning_cases_created"
                    ]
                )

                print(
                    "Queue remaining:",
                    result[
                        "queue_remaining"
                    ]
                )

                print(
                    "Cycle seconds:",
                    result[
                        "cycle_seconds"
                    ]
                )


                pump = (
                    discovery.get(
                        "sources",
                        {}
                    ).get(
                        "pumpfun",
                        {}
                    )
                )


                print(
                    (
                        "Pump stream: "
                        f"connected="
                        f"{pump.get('connected', False)} "
                        f"events="
                        f"{pump.get('events_received', 0)}"
                    )
                )


                for item in result[
                    "scans"
                ]:

                    if item.get(
                        "success"
                    ):

                        sources = (
                            "+"
                            .join(
                                item.get(
                                    "discovery_sources",
                                    [],
                                )
                            )
                            or
                            "unknown"
                        )


                        if item.get(
                            "learning_case_created"
                        ):

                            learning_text = (
                                f"LEARN#"
                                f"{item['learning_case_id']} "
                                f"{item['learning_sample_type']}"
                            )

                        else:

                            learning_text = (
                                "no-learn:"
                                f"{item.get('learning_reason')}"
                            )


                        print(
                            (
                                f"{item['symbol']} | "
                                f"{sources} | "
                                f"Radar "
                                f"{item['combined_score']} | "
                                f"{item['signal']} | "
                                f"{item['confidence']}% | "
                                f"{item['decision']} | "
                                f"{learning_text} | "
                                f"{item['seconds']}s"
                            )
                        )


                    else:

                        print(
                            (
                                f"{item.get('symbol', 'UNKNOWN')} | "
                                f"FAILED | "
                                f"{item.get('error')}"
                            )
                        )


            except Exception as error:

                print(
                    "Background scanner error:",
                    str(
                        error
                    )
                )


            self.stop_event.wait(
                self.cycle_seconds
            )


    # =========================================================
    # STOP
    # =========================================================

    def stop(
        self,
    ):

        self.stop_event.set()

        try:

            self.pumpfun.stop()

        except Exception:

            pass