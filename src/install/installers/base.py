"""
Base Installer Abstract Class.

Provides the foundation for all dependency installers with common
functionality for downloads, progress tracking, and error handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable
import logging

from ragged.install.detection.base import Platform, BaseDetector


logger = logging.getLogger(__name__)


class InstallationStatus(Enum):
    """Status of dependency installation."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    REQUIRES_REBOOT = "requires_reboot"
    PARTIAL = "partial"


@dataclass
class InstallationResult:
    """
    Result of dependency installation.

    Attributes:
        status: Overall installation status.
        success: Whether installation succeeded.
        message: Human-readable status message.
        version: Installed version if successful.
        requires_logout: Whether user needs to log out.
        requires_reboot: Whether system reboot is required.
        manual_steps: List of manual steps user must complete.
        rollback_performed: Whether rollback was performed on failure.
        logs: Installation log messages.
    """

    status: InstallationStatus
    success: bool
    message: str
    version: str | None = None
    requires_logout: bool = False
    requires_reboot: bool = False
    manual_steps: list[str] = field(default_factory=list)
    rollback_performed: bool = False
    logs: list[str] = field(default_factory=list)

    def add_log(self, message: str) -> None:
        """Add a log message."""
        self.logs.append(message)
        logger.info(message)


class InstallationStep:
    """A single step in the installation process."""

    def __init__(
        self,
        name: str,
        description: str,
        action: Callable[[], bool],
        rollback: Callable[[], None] | None = None,
    ) -> None:
        """
        Initialise installation step.

        Args:
            name: Short name for the step.
            description: Human-readable description.
            action: Callable that performs the step, returns success bool.
            rollback: Optional callable to undo the step on failure.
        """
        self.name = name
        self.description = description
        self.action = action
        self.rollback = rollback
        self.completed = False


class BaseInstaller(ABC):
    """
    Abstract base class for dependency installers.

    Provides common functionality for downloads, progress tracking,
    step management, and rollback on failure.
    """

    def __init__(self) -> None:
        """Initialise installer."""
        self._detector = self._create_detector()
        self._steps: list[InstallationStep] = []
        self._completed_steps: list[InstallationStep] = []
        self._progress_callback: Callable[[str, float], None] | None = None

    @abstractmethod
    def _create_detector(self) -> BaseDetector:
        """
        Create the detector for this dependency.

        Returns:
            Detector instance for the dependency.
        """
        ...

    @abstractmethod
    def _setup_steps(self) -> list[InstallationStep]:
        """
        Set up installation steps.

        Returns:
            List of installation steps in order.
        """
        ...

    @property
    def platform(self) -> Platform:
        """Get the current platform."""
        return self._detector.platform

    def set_progress_callback(
        self,
        callback: Callable[[str, float], None],
    ) -> None:
        """
        Set callback for progress updates.

        Args:
            callback: Function taking (message, progress_percent).
        """
        self._progress_callback = callback

    def _report_progress(self, message: str, percent: float) -> None:
        """Report progress to callback if set."""
        if self._progress_callback:
            self._progress_callback(message, percent)
        logger.info(f"[{percent:.0f}%] {message}")

    def install(self) -> InstallationResult:
        """
        Perform installation.

        Returns:
            InstallationResult with outcome.
        """
        # Check if already installed
        detection = self._detector.detect(force_refresh=True)
        if detection.is_ready():
            return InstallationResult(
                status=InstallationStatus.SKIPPED,
                success=True,
                message="Already installed",
                version=detection.version,
            )

        # Set up steps
        self._steps = self._setup_steps()
        total_steps = len(self._steps)

        result = InstallationResult(
            status=InstallationStatus.SUCCESS,
            success=True,
            message="Installation started",
        )

        try:
            for i, step in enumerate(self._steps):
                progress = (i / total_steps) * 100
                self._report_progress(step.description, progress)
                result.add_log(f"Starting: {step.description}")

                try:
                    success = step.action()
                    if not success:
                        result.add_log(f"Failed: {step.description}")
                        raise InstallationError(f"Step failed: {step.name}")

                    step.completed = True
                    self._completed_steps.append(step)
                    result.add_log(f"Completed: {step.description}")

                except Exception as e:
                    result.add_log(f"Error in {step.name}: {e!s}")
                    raise

            # Verify installation
            self._report_progress("Verifying installation", 95)
            detection = self._detector.detect(force_refresh=True)

            if detection.is_ready():
                result.status = InstallationStatus.SUCCESS
                result.success = True
                result.message = "Installation completed successfully"
                result.version = detection.version
                self._report_progress("Installation complete", 100)
            else:
                result.status = InstallationStatus.PARTIAL
                result.success = False
                result.message = "Installation completed but verification failed"
                if detection.issues:
                    result.manual_steps.extend(detection.issues)

        except Exception as e:
            result.status = InstallationStatus.FAILED
            result.success = False
            result.message = f"Installation failed: {e!s}"

            # Perform rollback
            self._rollback()
            result.rollback_performed = True
            result.add_log("Rollback performed")

        return result

    def _rollback(self) -> None:
        """Roll back completed steps in reverse order."""
        for step in reversed(self._completed_steps):
            if step.rollback:
                try:
                    logger.info(f"Rolling back: {step.name}")
                    step.rollback()
                except Exception as e:
                    logger.warning(f"Rollback failed for {step.name}: {e}")

    def requires_sudo(self) -> bool:
        """Check if installation requires elevated privileges."""
        return self.platform == Platform.LINUX

    def requires_admin(self) -> bool:
        """Check if installation requires admin on Windows."""
        return self.platform == Platform.WINDOWS


class InstallationError(Exception):
    """Exception raised during installation."""

    pass
