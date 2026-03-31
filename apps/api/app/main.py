import os
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.scenario_engine import ScenarioEngine
from app.services.config_git import ConfigGitService

_scenario_engine: ScenarioEngine | None = None
_config_git_service: ConfigGitService | None = None


def get_scenario_engine() -> ScenarioEngine:
    assert _scenario_engine is not None, "Scenario engine not initialized"
    return _scenario_engine


def get_config_git_service() -> ConfigGitService:
    assert _config_git_service is not None, "Config Git service not initialized"
    return _config_git_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scenario_engine, _config_git_service

    db_url_sync = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://blackboxnet:blackboxnet_dev@db:5432/blackboxnet",
    )
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
        print(f"Migration warning: {e.stderr}")
    except FileNotFoundError:
        print("Alembic not found, skipping migrations")

    git_repo_path = os.getenv("GIT_REPO_PATH", "/data/config-repo")
    _config_git_service = ConfigGitService(git_repo_path)
    print(f"Git repository initialized at {git_repo_path}")

    scenario_path = os.getenv(
        "SCENARIO_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "packages", "mock-scenarios", "acl-regression.json"),
    )
    _scenario_engine = ScenarioEngine()
    _scenario_engine.load_scenario(scenario_path)
    print(f"Scenario loaded: {_scenario_engine.get_scenario_info()['name']}")

    yield

    _scenario_engine = None
    _config_git_service = None


app = FastAPI(
    title="BlackBoxNet API",
    description="Network state replay platform API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import devices, incidents, configs, simulation  # noqa: E402

app.include_router(devices.router)
app.include_router(incidents.router)
app.include_router(configs.router)
app.include_router(simulation.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "blackboxnet-api"}
