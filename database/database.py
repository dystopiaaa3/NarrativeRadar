import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base import Base


# ============================================================
# LOAD ALL MODELS BEFORE CREATE_ALL
# ============================================================

from .models.coin import Coin
from .models.market import MarketObservation
from .models.narrative import Narrative
from .models.coin_narrative import CoinNarrative
from .models.attribute import Attribute
from .models.coin_attribute import CoinAttribute
from .models.wallet import Wallet
from .models.wallet_activity import WalletActivity
from .models.social import SocialObservation
from .models.similarity import CoinSimilarity
from .models.case import CaseStudy
from .models.pattern import Pattern
from .models.alert import Alert
from .models.analysis import Analysis
from .models.radar_result import RadarResult

from .models.feed_case import FeedCase
from .models.feed_outcome import FeedOutcome


# ============================================================
# DATABASE LOCATION
# ============================================================

def build_database_url():

    # --------------------------------------------------------
    # Explicit override
    #
    # If DATABASE_URL is provided, always use it.
    # This also makes a future PostgreSQL migration easy.
    # --------------------------------------------------------

    explicit_url = os.getenv(
        "DATABASE_URL"
    )

    if explicit_url:

        return explicit_url


    # --------------------------------------------------------
    # RAILWAY VOLUME
    #
    # Railway provides this automatically when a volume
    # is attached to the service.
    #
    # Example:
    # /data
    #
    # SQLite absolute paths require:
    #
    # sqlite:////data/narrativeradar.db
    # --------------------------------------------------------

    railway_volume = os.getenv(
        "RAILWAY_VOLUME_MOUNT_PATH"
    )

    if railway_volume:

        database_path = os.path.join(
            railway_volume,
            "narrativeradar.db"
        )

        return (
            "sqlite:///"
            + database_path
        )


    # --------------------------------------------------------
    # LOCAL WINDOWS FALLBACK
    #
    # Keeps using:
    #
    # NarrativeRadar\narrativeradar.db
    # --------------------------------------------------------

    return (
        "sqlite:///narrativeradar.db"
    )


DATABASE_URL = (
    build_database_url()
)


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,

    echo=False,

    # SQLite runs across the Discord thread,
    # scanner workers and learning tracker.
    connect_args=(
        {
            "check_same_thread": False
        }
        if DATABASE_URL.startswith(
            "sqlite"
        )
        else {}
    ),
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


# ============================================================
# DATABASE CREATION
# ============================================================

def create_database():

    Base.metadata.create_all(
        bind=engine
    )


# ============================================================
# SESSION HELPER
# ============================================================

def get_session():

    return SessionLocal()