from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from dvre.schemas.api import BuildConfig
from dvre.core.dependencies import get_project_manager
from dvre.server import create_app


@pytest.fixture
def app() -> FastAPI:
    app = create_app()
    app.state.build_lock = asyncio.Lock()
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestBuildEndpoint:
    async def test_build_success(self, app: FastAPI, client: AsyncClient, build_config: BuildConfig):
        mock_pm = MagicMock()

        app.dependency_overrides[get_project_manager] = lambda: mock_pm

        from dvre.core.builder.builder import OutputBuilder

        original_build = OutputBuilder.build

        def mock_build(self, config):
            return "job_001"

        OutputBuilder.build = mock_build

        try:
            payload = build_config.model_dump(mode="json")
            response = await client.post("/build", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job_001"
        finally:
            OutputBuilder.build = original_build
            app.dependency_overrides.clear()

    async def test_build_conflict_when_locked(self, app: FastAPI, client: AsyncClient, build_config: BuildConfig):
        app.dependency_overrides[get_project_manager] = lambda: MagicMock()
        lock = asyncio.Lock()
        await lock.acquire()
        app.state.build_lock = lock

        payload = build_config.model_dump(mode="json")
        response = await client.post("/build", json=payload)

        assert response.status_code == 409
        lock.release()
        app.dependency_overrides.clear()

    async def test_build_invalid_payload(self, client: AsyncClient):
        response = await client.post("/build", json={})
        assert response.status_code == 422


class TestProjectClose:
    async def test_close_success(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_project = MagicMock()
        mock_pm.GetCurrentProject.return_value = mock_project

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        response = await client.post("/project/close")

        assert response.status_code == 204
        app.dependency_overrides.clear()

    async def test_close_no_project(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_pm.GetCurrentProject.return_value = None

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        response = await client.post("/project/close")

        assert response.status_code == 404
        app.dependency_overrides.clear()


class TestRenderJobStatus:
    async def test_render_job_status_success(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_project = MagicMock()
        mock_pm.GetCurrentProject.return_value = mock_project
        mock_project.GetRenderJobStatus.return_value = {
            "JobStatus": "In Progress",
            "CompletionPercentage": 45,
        }

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        response = await client.get("/render-job/job_001/status")

        assert response.status_code == 200
        data = response.json()
        assert data["job_status"] == "In Progress"
        assert data["completion_percentage"] == 45
        app.dependency_overrides.clear()

    async def test_render_job_no_project(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_pm.GetCurrentProject.return_value = None

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        response = await client.get("/render-job/job_001/status")

        assert response.status_code == 404
        app.dependency_overrides.clear()
