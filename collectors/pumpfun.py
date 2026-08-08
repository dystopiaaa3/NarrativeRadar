import json
import os
import threading
import time

from collections import deque
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

from websockets.sync.client import connect
from websockets.exceptions import (
    ConnectionClosed,
)


load_dotenv()


class PumpFunCollector:

    """
    Realtime Pump.fun discovery collector.

    Realtime events are supplied by PumpPortal.

    IMPORTANT:
        - Discovery only.
        - Never decides whether a token is good.
        - Never sends Discord notifications.
        - Uses ONE persistent WebSocket connection.
        - Automatically reconnects.
        - Tokens are later validated by DexScreener,
          Solana RPC and LiveRadar.
    """

    def __init__(
        self,
        timeout: float = 5.0,
        buffer_size: int = 5000,
        reconnect_seconds: int = 3,
    ):

        self.name = (
            "Pump.fun Realtime Discovery"
        )

        self.timeout = float(
            timeout
        )

        self.buffer_size = max(
            100,
            int(
                buffer_size
            ),
        )

        self.reconnect_seconds = max(
            1,
            int(
                reconnect_seconds
            ),
        )

        self.api_key = (
            os.getenv(
                "PUMPPORTAL_API_KEY"
            )
            or ""
        ).strip()

        self.websocket_url = (
            "wss://pumpportal.fun/api/data"
        )

        self._buffer = deque(
            maxlen=self.buffer_size
        )

        self._lock = (
            threading.Lock()
        )

        self._stop_event = (
            threading.Event()
        )

        self._thread = None

        self._connected = False

        self._last_error = None

        self._last_event_at = None

        self._events_received = 0

        self._reconnects = 0


    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

            if value is None:
                return default

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default


    @staticmethod
    def _valid_mint(
        value: Any,
    ) -> bool:

        if not isinstance(
            value,
            str,
        ):

            return False

        value = value.strip()

        return (
            32
            <= len(value)
            <= 44
        )


    # =========================================================
    # NORMALIZE REALTIME EVENT
    # =========================================================

    def _normalize_event(
        self,
        event: Dict[str, Any],
    ):

        if not isinstance(
            event,
            dict,
        ):

            return None

        mint = (
            event.get(
                "mint"
            )
            or
            event.get(
                "tokenAddress"
            )
            or
            event.get(
                "address"
            )
            or
            event.get(
                "coin_address"
            )
        )

        if not self._valid_mint(
            mint
        ):

            return None

        mint = mint.strip()

        tx_type = str(
            event.get(
                "txType",
                ""
            )
            or
            event.get(
                "type",
                ""
            )
            or
            ""
        ).lower()

        name = str(
            event.get(
                "name",
                ""
            )
            or ""
        )

        symbol = str(
            event.get(
                "symbol",
                ""
            )
            or ""
        )

        # PumpPortal may expose marketCapSol.
        #
        # DO NOT treat this as USD market cap.
        # Live USD data will come from DexScreener.

        market_cap_sol = (
            self._safe_float(
                event.get(
                    "marketCapSol"
                )
            )
        )

        initial_buy_sol = (
            self._safe_float(
                event.get(
                    "initialBuy"
                )
            )
        )

        return {
            "coin_address": (
                mint
            ),

            "name": (
                name
            ),

            "symbol": (
                symbol
            ),

            # USD fields intentionally unknown until
            # DexScreener enrichment succeeds.

            "price": 0.0,

            "market_cap": 0.0,

            "liquidity": 0.0,

            "volume": 0.0,

            "volume_24h": 0.0,

            "price_change_1h": 0.0,

            "price_change_24h": 0.0,

            "buys_1h": 0,

            "sells_1h": 0,

            "pair_created_at": None,

            # Discovery metadata

            "source": (
                "pumpfun"
            ),

            "discovery_sources": [
                "pumpfun"
            ],

            "source_count": 1,

            "cross_source": False,

            "discovery_confidence": 60.0,

            "source_reason": (
                "new_token"
            ),

            "source_reasons": [
                "new_token"
            ],

            "source_rank": 1,

            "discovered_at": (
                datetime.utcnow()
            ),

            # Pump-specific context

            "pumpfun_market_cap_sol": (
                market_cap_sol
            ),

            "pumpfun_initial_buy_sol": (
                initial_buy_sol
            ),

            "pumpfun_tx_type": (
                tx_type
            ),

            "creator": (
                event.get(
                    "traderPublicKey"
                )
                or
                event.get(
                    "creator"
                )
                or
                ""
            ),

            "bonding_curve": (
                event.get(
                    "bondingCurveKey"
                )
                or
                ""
            ),

            "raw": (
                event
            ),
        }


    # =========================================================
    # BUFFER
    # =========================================================

    def _push_event(
        self,
        event,
    ):

        candidate = (
            self._normalize_event(
                event
            )
        )

        if candidate is None:

            return False

        with self._lock:

            self._buffer.append(
                candidate
            )

            self._events_received += 1

            self._last_event_at = (
                datetime.utcnow()
            )

        return True


    def drain(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        """
        Drain events gathered since the previous scanner cycle.

        If more events arrived than we want to process, prefer
        the newest ones.
        """

        limit = max(
            1,
            int(
                limit
            ),
        )

        with self._lock:

            items = list(
                self._buffer
            )

            self._buffer.clear()

        if not items:

            return []

        # Keep latest events.

        items = items[
            -limit:
        ]

        # Deduplicate by mint while keeping newest event.

        unique = {}

        for candidate in items:

            address = (
                candidate[
                    "coin_address"
                ]
            )

            unique[
                address
            ] = candidate

        return list(
            unique.values()
        )


    # =========================================================
    # WEBSOCKET URL
    # =========================================================

    def _url(
        self,
    ):

        if not self.api_key:

            return None

        return (
            f"{self.websocket_url}"
            f"?api-key={self.api_key}"
        )


    # =========================================================
    # STREAM LOOP
    # =========================================================

    def _listen_forever(
        self,
    ):

        while not self._stop_event.is_set():

            uri = self._url()

            if not uri:

                self._connected = False

                self._last_error = (
                    "PUMPPORTAL_API_KEY "
                    "not configured"
                )

                self._stop_event.wait(
                    5
                )

                continue

            try:

                with connect(
                    uri,
                    open_timeout=(
                        self.timeout
                    ),
                    close_timeout=3,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=2_000_000,
                ) as websocket:

                    self._connected = True

                    self._last_error = None

                    subscription = {
                        "method": (
                            "subscribeNewToken"
                        )
                    }

                    websocket.send(
                        json.dumps(
                            subscription
                        )
                    )

                    while not self._stop_event.is_set():

                        try:

                            message = (
                                websocket.recv(
                                    timeout=1
                                )
                            )

                        except TimeoutError:

                            continue

                        if message is None:

                            continue

                        try:

                            event = (
                                json.loads(
                                    message
                                )
                            )

                        except (
                            json.JSONDecodeError,
                            TypeError,
                        ):

                            continue

                        # Some API responses may be
                        # subscription confirmations rather
                        # than actual token events.

                        self._push_event(
                            event
                        )

            except ConnectionClosed as error:

                self._connected = False

                self._last_error = str(
                    error
                )

            except Exception as error:

                self._connected = False

                self._last_error = str(
                    error
                )

            if self._stop_event.is_set():

                break

            self._reconnects += 1

            self._stop_event.wait(
                self.reconnect_seconds
            )

        self._connected = False


    # =========================================================
    # START / STOP
    # =========================================================

    def start(
        self,
    ):

        if (
            self._thread is not None
            and
            self._thread.is_alive()
        ):

            return False

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=(
                self._listen_forever
            ),
            name=(
                "PumpFunRealtime"
            ),
            daemon=True,
        )

        self._thread.start()

        return True


    def stop(
        self,
    ):

        self._stop_event.set()

        if (
            self._thread is not None
            and
            self._thread.is_alive()
        ):

            self._thread.join(
                timeout=5
            )


    # =========================================================
    # STATUS
    # =========================================================

    def status(
        self,
    ):

        with self._lock:

            buffered = len(
                self._buffer
            )

            events_received = (
                self._events_received
            )

            last_event = (
                self._last_event_at
            )

        return {
            "configured": bool(
                self.api_key
            ),

            "connected": (
                self._connected
            ),

            "buffered": (
                buffered
            ),

            "events_received": (
                events_received
            ),

            "reconnects": (
                self._reconnects
            ),

            "last_event_at": (
                last_event
            ),

            "last_error": (
                self._last_error
            ),
        }


    # =========================================================
    # LEGACY NORMALIZATION SUPPORT
    # =========================================================

    def normalize(
        self,
        payload: Any,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:

        """
        Retained so existing Pump.fun normalization tests
        continue to work.
        """

        if isinstance(
            payload,
            dict,
        ):

            possible = (
                payload.get(
                    "coins"
                )
                or
                payload.get(
                    "data"
                )
                or
                payload.get(
                    "results"
                )
                or
                payload.get(
                    "tokens"
                )
                or
                []
            )

        elif isinstance(
            payload,
            list,
        ):

            possible = payload

        else:

            possible = []

        if isinstance(
            possible,
            dict,
        ):

            possible = (
                possible.get(
                    "coins"
                )
                or
                possible.get(
                    "results"
                )
                or
                possible.get(
                    "tokens"
                )
                or
                []
            )

        if not isinstance(
            possible,
            list,
        ):

            return []

        results = []

        seen = set()

        for item in possible[
            :limit
        ]:

            if not isinstance(
                item,
                dict,
            ):

                continue

            candidate = (
                self._normalize_event(
                    item
                )
            )

            if candidate is None:

                continue

            address = (
                candidate[
                    "coin_address"
                ]
            )

            if address in seen:

                continue

            seen.add(
                address
            )

            results.append(
                candidate
            )

        return results