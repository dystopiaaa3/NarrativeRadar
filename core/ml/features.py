import math


FEATURE_NAMES = [
    "log_price",
    "log_market_cap",
    "log_liquidity",
    "log_volume_24h",
    "liquidity_mc_ratio",
    "volume_mc_ratio",
    "market_score",
    "social_score",
    "wallet_score",
    "data_quality",
    "confidence",
    "has_social",
    "has_wallet",
]


def _safe_float(value, default=0.0):
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return float(default)


def _clip(value, low, high):
    return max(low, min(high, value))


def build_features(
    *,
    price,
    market_cap,
    liquidity,
    volume_24h,
    market_score,
    social_score,
    wallet_score,
    data_quality,
    confidence,
):
    price = max(_safe_float(price), 0.0)
    market_cap = max(_safe_float(market_cap), 0.0)
    liquidity = max(_safe_float(liquidity), 0.0)
    volume_24h = max(_safe_float(volume_24h), 0.0)

    market_score = _clip(_safe_float(market_score), 0.0, 100.0)
    social_score = _clip(_safe_float(social_score), 0.0, 100.0)
    wallet_score = _clip(_safe_float(wallet_score), 0.0, 100.0)
    data_quality = _clip(_safe_float(data_quality), 0.0, 100.0)
    confidence = _clip(_safe_float(confidence), 0.0, 100.0)

    liquidity_mc_ratio = (
        liquidity / market_cap
        if market_cap > 0
        else 0.0
    )

    volume_mc_ratio = (
        volume_24h / market_cap
        if market_cap > 0
        else 0.0
    )

    row = {
        "log_price": math.log10(price + 1e-12),
        "log_market_cap": math.log10(market_cap + 1.0),
        "log_liquidity": math.log10(liquidity + 1.0),
        "log_volume_24h": math.log10(volume_24h + 1.0),

        # Clip wild microcap ratios so a single broken/extreme value
        # cannot dominate the tree splits.
        "liquidity_mc_ratio": _clip(
            liquidity_mc_ratio,
            0.0,
            10.0,
        ),

        "volume_mc_ratio": _clip(
            volume_mc_ratio,
            0.0,
            100.0,
        ),

        "market_score": market_score / 100.0,
        "social_score": social_score / 100.0,
        "wallet_score": wallet_score / 100.0,
        "data_quality": data_quality / 100.0,
        "confidence": confidence / 100.0,

        "has_social": 1.0 if social_score > 0 else 0.0,
        "has_wallet": 1.0 if wallet_score > 0 else 0.0,
    }

    return [
        float(row[name])
        for name in FEATURE_NAMES
    ]


def build_case_features(feed_case):
    return build_features(
        price=getattr(feed_case, "t0_price", 0.0),
        market_cap=getattr(feed_case, "t0_market_cap", 0.0),
        liquidity=getattr(feed_case, "t0_liquidity", 0.0),
        volume_24h=getattr(feed_case, "t0_volume_24h", 0.0),
        market_score=getattr(feed_case, "market_score", 0.0),
        social_score=getattr(feed_case, "social_score", 0.0),
        wallet_score=getattr(feed_case, "wallet_score", 0.0),
        data_quality=getattr(feed_case, "data_quality", 0.0),
        confidence=getattr(feed_case, "confidence", 0.0),
    )


def build_live_features(
    market_data,
    analysis,
    signal=None,
):
    signal = signal or {}

    return build_features(
        price=(market_data or {}).get("price", 0.0),
        market_cap=(market_data or {}).get("market_cap", 0.0),
        liquidity=(market_data or {}).get("liquidity", 0.0),
        volume_24h=(market_data or {}).get("volume_24h", 0.0),

        market_score=(analysis or {}).get(
            "market_score",
            0.0,
        ),

        social_score=(analysis or {}).get(
            "social_score",
            0.0,
        ),

        wallet_score=(analysis or {}).get(
            "wallet_score",
            0.0,
        ),

        data_quality=(analysis or {}).get(
            "data_quality",
            0.0,
        ),

        confidence=(signal or {}).get(
            "confidence",
            0.0,
        ),
    )
