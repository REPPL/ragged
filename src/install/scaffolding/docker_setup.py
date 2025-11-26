"""
Docker Services Setup.

PREREQ-005: Sets up Docker services including ChromaDB container,
Docker networks, and volumes.
"""

import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Docker Compose configuration
DOCKER_COMPOSE_TEMPLATE = """version: '3.8'

services:
  chromadb:
    image: chromadb/chroma:latest
    container_name: ragged_chromadb
    ports:
      - "{chromadb_port}:8000"
    volumes:
      - {chromadb_data}:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped
    networks:
      - ragged_network

networks:
  ragged_network:
    name: ragged_network
    driver: bridge

volumes:
  chromadb_data:
    name: ragged_chromadb_data
"""


@dataclass
class DockerServiceConfig:
    """Configuration for Docker services."""

    chromadb_port: int = 8001
    chromadb_data_path: str = "~/.ragged/chromadb"
    compose_file_path: str = "~/.ragged/docker-compose.yml"


class DockerServiceManager:
    """
    Manager for ragged Docker services.

    Handles creating, starting, stopping, and managing Docker containers.
    """

    def __init__(self, config: DockerServiceConfig | None = None) -> None:
        """
        Initialise Docker service manager.

        Args:
            config: Docker service configuration.
        """
        self._config = config or DockerServiceConfig()
        self._compose_path = Path(self._config.compose_file_path).expanduser()

    def generate_compose_file(self) -> str:
        """
        Generate docker-compose.yml content.

        Returns:
            Docker Compose file content.
        """
        data_path = Path(self._config.chromadb_data_path).expanduser()

        content = DOCKER_COMPOSE_TEMPLATE.format(
            chromadb_port=self._config.chromadb_port,
            chromadb_data=str(data_path),
        )

        return content

    def save_compose_file(self) -> Path:
        """
        Save docker-compose.yml file.

        Returns:
            Path to saved file.
        """
        content = self.generate_compose_file()

        # Ensure directory exists
        self._compose_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self._compose_path, "w") as f:
            f.write(content)

        logger.info(f"Saved docker-compose.yml: {self._compose_path}")

        return self._compose_path

    def pull_images(self) -> bool:
        """
        Pull required Docker images.

        Returns:
            True if successful.
        """
        logger.info("Pulling Docker images...")

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self._compose_path), "pull"],
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )

            if result.returncode != 0:
                # Try docker-compose v1
                result = subprocess.run(
                    ["docker-compose", "-f", str(self._compose_path), "pull"],
                    capture_output=True,
                    text=True,
                    timeout=600,
                    check=False,
                )

            if result.returncode != 0:
                logger.error(f"Failed to pull images: {result.stderr}")
                return False

            logger.info("Docker images pulled successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Image pull timed out")
            return False
        except FileNotFoundError:
            logger.error("Docker/docker-compose not found")
            return False

    def start_services(self) -> bool:
        """
        Start Docker services.

        Returns:
            True if successful.
        """
        logger.info("Starting Docker services...")

        try:
            # Try docker compose v2 first
            result = subprocess.run(
                ["docker", "compose", "-f", str(self._compose_path), "up", "-d"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )

            if result.returncode != 0:
                # Try docker-compose v1
                result = subprocess.run(
                    ["docker-compose", "-f", str(self._compose_path), "up", "-d"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )

            if result.returncode != 0:
                logger.error(f"Failed to start services: {result.stderr}")
                return False

            logger.info("Docker services started")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Service start timed out")
            return False
        except FileNotFoundError:
            logger.error("Docker/docker-compose not found")
            return False

    def stop_services(self) -> bool:
        """
        Stop Docker services.

        Returns:
            True if successful.
        """
        logger.info("Stopping Docker services...")

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self._compose_path), "down"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode != 0:
                result = subprocess.run(
                    ["docker-compose", "-f", str(self._compose_path), "down"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )

            if result.returncode != 0:
                logger.warning(f"Failed to stop services cleanly: {result.stderr}")

            logger.info("Docker services stopped")
            return True

        except subprocess.TimeoutExpired:
            logger.warning("Service stop timed out")
            return False
        except FileNotFoundError:
            return True  # Docker not found, nothing to stop

    def remove_services(self, remove_volumes: bool = False) -> bool:
        """
        Remove Docker services and optionally volumes.

        Args:
            remove_volumes: Whether to remove data volumes.

        Returns:
            True if successful.
        """
        logger.info("Removing Docker services...")

        cmd = ["docker", "compose", "-f", str(self._compose_path), "down"]
        if remove_volumes:
            cmd.append("-v")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode != 0:
                # Try v1
                cmd = ["docker-compose", "-f", str(self._compose_path), "down"]
                if remove_volumes:
                    cmd.append("-v")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )

            logger.info("Docker services removed")
            return True

        except subprocess.TimeoutExpired:
            logger.warning("Service removal timed out")
            return False
        except FileNotFoundError:
            return True

    def get_service_status(self) -> dict[str, Any]:
        """
        Get status of Docker services.

        Returns:
            Dictionary with service status information.
        """
        status: dict[str, Any] = {
            "running": False,
            "containers": [],
            "health": {},
        }

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self._compose_path), "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                import json

                # Handle both single object and array output
                output = result.stdout.strip()
                if output.startswith("["):
                    containers = json.loads(output)
                else:
                    # Multiple JSON objects, one per line
                    containers = [json.loads(line) for line in output.split("\n") if line.strip()]

                status["containers"] = containers
                status["running"] = any(
                    c.get("State") == "running" for c in containers
                )

                for container in containers:
                    name = container.get("Service", container.get("Name", "unknown"))
                    state = container.get("State", "unknown")
                    health = container.get("Health", "unknown")
                    status["health"][name] = {"state": state, "health": health}

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"Could not get service status: {e}")

        return status

    def wait_for_healthy(self, timeout: float = 60.0) -> bool:
        """
        Wait for all services to become healthy.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if all services are healthy.
        """
        logger.info("Waiting for services to become healthy...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_service_status()

            if status["running"]:
                all_healthy = True
                for name, info in status["health"].items():
                    if info.get("health") not in ("healthy", None):
                        all_healthy = False
                        break

                if all_healthy:
                    logger.info("All services are healthy")
                    return True

            time.sleep(2)

        logger.warning("Timeout waiting for services to become healthy")
        return False


def setup_docker_services(
    config: DockerServiceConfig | None = None,
    pull_images: bool = True,
    start: bool = True,
    wait_healthy: bool = True,
) -> dict[str, Any]:
    """
    Set up Docker services.

    Args:
        config: Docker service configuration.
        pull_images: Whether to pull images.
        start: Whether to start services.
        wait_healthy: Whether to wait for healthy status.

    Returns:
        Dictionary with setup results.
    """
    result: dict[str, Any] = {
        "success": True,
        "compose_file": None,
        "images_pulled": False,
        "services_started": False,
        "healthy": False,
        "errors": [],
    }

    manager = DockerServiceManager(config)

    # Save compose file
    try:
        compose_path = manager.save_compose_file()
        result["compose_file"] = str(compose_path)
    except OSError as e:
        result["success"] = False
        result["errors"].append(f"Failed to save compose file: {e}")
        return result

    # Pull images
    if pull_images:
        if manager.pull_images():
            result["images_pulled"] = True
        else:
            result["success"] = False
            result["errors"].append("Failed to pull Docker images")
            return result

    # Start services
    if start:
        if manager.start_services():
            result["services_started"] = True
        else:
            result["success"] = False
            result["errors"].append("Failed to start Docker services")
            return result

        # Wait for healthy
        if wait_healthy:
            if manager.wait_for_healthy():
                result["healthy"] = True
            else:
                result["errors"].append("Services started but not all healthy")

    return result
