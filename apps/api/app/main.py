import os
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db_urls import get_sync_database_url
from app.core.settings import get_settings
from app.core.scenario_manager import ScenarioManager
from app.services.config_git import ConfigGitService
from app.services.ssh_config_fetcher import RealDeviceSSHConfig, SSHConfigFetcher

_scenario_manager: ScenarioManager | None = None
_config_git_service: ConfigGitService | None = None
_ssh_config_fetcher: SSHConfigFetcher | None = None


def get_scenario_manager() -> ScenarioManager:
    assert _scenario_manager is not None, "Scenario manager not initialized"
    return _scenario_manager


def get_scenario_engine(scenario_id: str = "acl-regression"):
    """Backward-compatible accessor for a single scenario engine."""
    return get_scenario_manager().get_engine(scenario_id)


def get_config_git_service() -> ConfigGitService:
    assert _config_git_service is not None, "Config Git service not initialized"
    return _config_git_service


def get_ssh_config_fetcher() -> SSHConfigFetcher | None:
    return _ssh_config_fetcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scenario_manager, _config_git_service, _ssh_config_fetcher

    db_url_sync = get_sync_database_url()
    api_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=api_root,
            env={**os.environ, "DATABASE_URL_SYNC": db_url_sync, "PYTHONPATH": api_root},
            check=True,
            capture_output=True,
            text=True,
        )
        print("Database migrations completed successfully")
    except subprocess.CalledProcessError as e:
        msg = e.stderr or e.stdout or str(e)
        print(f"Migration failed: {msg}")
        if os.getenv("RENDER"):
            raise RuntimeError(f"Database migration failed on startup: {msg}") from e
    except FileNotFoundError:
        print("Alembic not found, skipping migrations")

    git_repo_path = os.getenv("GIT_REPO_PATH", "/data/config-repo")
    _config_git_service = ConfigGitService(git_repo_path)
    print(f"Git repository initialized at {git_repo_path}")

    scenarios_dir = os.getenv(
        "SCENARIOS_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "packages", "mock-scenarios"),
    )
    _scenario_manager = ScenarioManager(scenarios_dir)
    _scenario_manager.load_all()
    loaded = ", ".join(s["id"] for s in _scenario_manager.list_scenarios())
    print(f"Scenarios loaded ({len(_scenario_manager.list_scenarios())}): {loaded}")

    settings = get_settings()
    _ssh_config_fetcher = None
    if settings.real_device_enabled:
        missing = [
            name for name, value in {
                "REAL_DEVICE_HOST": settings.real_device_host,
                "REAL_DEVICE_USERNAME": settings.real_device_username,
                "REAL_DEVICE_SCENARIO_DEVICE_ID": settings.real_device_scenario_device_id,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"REAL_DEVICE_ENABLED is true but required settings are missing: {', '.join(missing)}"
            )
        if not settings.real_device_password and not settings.real_device_private_key_path:
            raise RuntimeError(
                "REAL_DEVICE_ENABLED is true but neither REAL_DEVICE_PASSWORD nor REAL_DEVICE_PRIVATE_KEY_PATH is set"
            )

        _ssh_config_fetcher = SSHConfigFetcher(
            RealDeviceSSHConfig(
                host=settings.real_device_host,
                port=settings.real_device_port,
                username=settings.real_device_username,
                password=settings.real_device_password,
                private_key_path=settings.real_device_private_key_path,
                private_key_passphrase=settings.real_device_private_key_passphrase,
                command=settings.real_device_command,
                timeout_seconds=settings.real_device_timeout_seconds,
                scenario_device_id=settings.real_device_scenario_device_id,
            )
        )
        print(
            "Real device config collection enabled for "
            f"{settings.real_device_scenario_device_id} via {settings.real_device_host}:{settings.real_device_port}"
        )

    yield

    _scenario_manager = None
    _config_git_service = None
    _ssh_config_fetcher = None


app = FastAPI(
    title="BlackBoxNet API",
    description="Network state replay platform API",
    version="1.0.0",
    lifespan=lifespan,
)

def _cors_origins() -> list[str]:
    defaults = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://blackboxnet-web.onrender.com",
    ]
    raw = os.getenv("CORS_ORIGINS", "")
    extra: list[str] = []
    for item in raw.split(","):
        origin = item.strip()
        if not origin:
            continue
        if not origin.startswith("http"):
            origin = f"https://{origin}"
        extra.append(origin.rstrip("/"))
    return list(dict.fromkeys(extra + defaults))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    # Allow any Render static-site preview/production URL (POST requires preflight).
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import devices, incidents, configs, simulation, scenarios  # noqa: E402

app.include_router(devices.router)
app.include_router(incidents.router)
app.include_router(configs.router)
app.include_router(simulation.router)
app.include_router(scenarios.router)


@app.get("/")
async def root():
    return {
        "service": "blackboxnet-api",
        "health": "/api/health",
        "scenarios": "/api/scenarios",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "blackboxnet-api"}
