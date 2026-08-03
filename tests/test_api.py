from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

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


class TestTaskEndpoint:
    async def test_task_status_success(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_project = MagicMock()
        mock_pm.GetCurrentProject.return_value = mock_project
        mock_project.GetRenderJobStatus.return_value = {
            "JobStatus": "Complete",
            "CompletionPercentage": 100,
        }

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            response = await client.get("/tasks/task_001")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task_001"
        assert data["task_name"] == "dvre.render.status"
        assert data["status"] == "SUCCESS"
        assert data["result"] == {"ok": True}
        assert data["error"] == ""

    async def test_task_status_pending(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_project = MagicMock()
        mock_pm.GetCurrentProject.return_value = mock_project
        mock_project.GetRenderJobStatus.return_value = {
            "JobStatus": "Rendering",
            "CompletionPercentage": 45,
        }

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            response = await client.get("/tasks/task_001")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["result"] is None

    async def test_task_status_failure(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_project = MagicMock()
        mock_pm.GetCurrentProject.return_value = mock_project
        mock_project.GetRenderJobStatus.return_value = {
            "JobStatus": "Error",
            "CompletionPercentage": 10,
            "Error": "render failed",
        }

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            response = await client.get("/tasks/task_001")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILURE"
        assert data["result"] is None
        assert data["error"] == "render failed"

    async def test_task_status_no_project(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_pm.GetCurrentProject.return_value = None

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            response = await client.get("/tasks/task_001")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404


class TestProjectClose:
    async def test_close_success(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_project = MagicMock()
        mock_pm.GetCurrentProject.return_value = mock_project

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            response = await client.post("/project/close")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 204
        mock_pm.CloseProject.assert_called_once_with(mock_project)

    async def test_close_no_project(self, app: FastAPI, client: AsyncClient):
        mock_pm = MagicMock()
        mock_pm.GetCurrentProject.return_value = None

        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            response = await client.post("/project/close")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404
        mock_pm.CloseProject.assert_not_called()

    async def test_close_blocked_while_building(
        self, app: FastAPI, client: AsyncClient
    ):
        lock = asyncio.Lock()
        await lock.acquire()
        app.state.build_lock = lock

        mock_pm = MagicMock()
        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            response = await client.post("/project/close")
        finally:
            app.dependency_overrides.clear()
            lock.release()

        assert response.status_code == 403
        mock_pm.CloseProject.assert_not_called()
