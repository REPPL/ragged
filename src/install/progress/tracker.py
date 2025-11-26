"""
Progress Tracker.

WIZARD-003: Tracks installation progress through phases.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import logging
import time


logger = logging.getLogger(__name__)


class InstallationPhase(Enum):
    """Installation phases."""

    INITIALISING = "initialising"
    DETECTING = "detecting"
    VALIDATING = "validating"
    INSTALLING_DOCKER = "installing_docker"
    INSTALLING_PYTHON = "installing_python"
    INSTALLING_OLLAMA = "installing_ollama"
    CREATING_DIRECTORIES = "creating_directories"
    GENERATING_CONFIG = "generating_config"
    SETTING_UP_DOCKER = "setting_up_docker"
    PULLING_MODEL = "pulling_model"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    FAILED = "failed"


class PhaseStatus(Enum):
    """Phase status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class PhaseInfo:
    """Information about a phase."""

    phase: InstallationPhase
    status: PhaseStatus = PhaseStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float | None:
        """Get duration in seconds."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()


@dataclass
class ProgressTracker:
    """
    Tracks installation progress.

    Manages phases, progress updates, and callbacks.
    """

    phases: list[InstallationPhase] = field(default_factory=list)
    phase_info: dict[InstallationPhase, PhaseInfo] = field(default_factory=dict)
    current_phase: InstallationPhase | None = None
    callbacks: list[Callable[["ProgressTracker", PhaseInfo], None]] = field(
        default_factory=list
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialise default phases if not provided."""
        if not self.phases:
            self.phases = [
                InstallationPhase.INITIALISING,
                InstallationPhase.DETECTING,
                InstallationPhase.VALIDATING,
                InstallationPhase.INSTALLING_DOCKER,
                InstallationPhase.INSTALLING_OLLAMA,
                InstallationPhase.CREATING_DIRECTORIES,
                InstallationPhase.GENERATING_CONFIG,
                InstallationPhase.SETTING_UP_DOCKER,
                InstallationPhase.PULLING_MODEL,
                InstallationPhase.VERIFYING,
                InstallationPhase.COMPLETE,
            ]

        # Initialise phase info
        for phase in self.phases:
            if phase not in self.phase_info:
                self.phase_info[phase] = PhaseInfo(phase=phase)

    def add_callback(
        self,
        callback: Callable[["ProgressTracker", PhaseInfo], None],
    ) -> None:
        """Add a progress callback."""
        self.callbacks.append(callback)

    def remove_callback(
        self,
        callback: Callable[["ProgressTracker", PhaseInfo], None],
    ) -> None:
        """Remove a progress callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def start(self) -> None:
        """Start progress tracking."""
        self.started_at = datetime.now()
        logger.info("Installation started")

    def complete(self) -> None:
        """Mark installation as complete."""
        self.completed_at = datetime.now()
        self.set_phase(InstallationPhase.COMPLETE)
        logger.info(f"Installation completed in {self.total_duration:.1f}s")

    def fail(self, error: str) -> None:
        """Mark installation as failed."""
        self.completed_at = datetime.now()
        if self.current_phase:
            info = self.phase_info[self.current_phase]
            info.status = PhaseStatus.FAILED
            info.error = error
            info.completed_at = datetime.now()
            self._notify(info)

        self.current_phase = InstallationPhase.FAILED
        logger.error(f"Installation failed: {error}")

    def set_phase(
        self,
        phase: InstallationPhase,
        message: str = "",
    ) -> None:
        """Set current phase."""
        # Complete previous phase
        if self.current_phase and self.current_phase != phase:
            prev_info = self.phase_info.get(self.current_phase)
            if prev_info and prev_info.status == PhaseStatus.IN_PROGRESS:
                prev_info.status = PhaseStatus.COMPLETED
                prev_info.progress = 1.0
                prev_info.completed_at = datetime.now()
                self._notify(prev_info)

        # Start new phase
        self.current_phase = phase
        info = self.phase_info.get(phase)
        if info:
            info.status = PhaseStatus.IN_PROGRESS
            info.progress = 0.0
            info.message = message
            info.started_at = datetime.now()
            self._notify(info)

        logger.info(f"Phase: {phase.value} - {message}")

    def update_progress(
        self,
        progress: float,
        message: str = "",
    ) -> None:
        """Update progress of current phase."""
        if not self.current_phase:
            return

        info = self.phase_info.get(self.current_phase)
        if info:
            info.progress = max(0.0, min(1.0, progress))
            if message:
                info.message = message
            self._notify(info)

    def skip_phase(self, phase: InstallationPhase, reason: str = "") -> None:
        """Mark a phase as skipped."""
        info = self.phase_info.get(phase)
        if info:
            info.status = PhaseStatus.SKIPPED
            info.message = reason
            self._notify(info)

        logger.info(f"Skipped phase: {phase.value} - {reason}")

    def set_detail(self, key: str, value: Any) -> None:
        """Set a detail on the current phase."""
        if not self.current_phase:
            return

        info = self.phase_info.get(self.current_phase)
        if info:
            info.details[key] = value

    def _notify(self, info: PhaseInfo) -> None:
        """Notify callbacks of progress update."""
        for callback in self.callbacks:
            try:
                callback(self, info)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    @property
    def total_duration(self) -> float:
        """Get total duration in seconds."""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()

    @property
    def overall_progress(self) -> float:
        """Get overall installation progress (0.0 to 1.0)."""
        if not self.phases:
            return 0.0

        total_weight = len(self.phases)
        completed_weight = 0.0

        for phase in self.phases:
            info = self.phase_info.get(phase)
            if info:
                if info.status == PhaseStatus.COMPLETED:
                    completed_weight += 1.0
                elif info.status == PhaseStatus.SKIPPED:
                    completed_weight += 1.0
                elif info.status == PhaseStatus.IN_PROGRESS:
                    completed_weight += info.progress

        return completed_weight / total_weight

    @property
    def is_complete(self) -> bool:
        """Check if installation is complete."""
        return self.current_phase == InstallationPhase.COMPLETE

    @property
    def is_failed(self) -> bool:
        """Check if installation failed."""
        return self.current_phase == InstallationPhase.FAILED

    def get_summary(self) -> dict[str, Any]:
        """Get progress summary."""
        phases_summary = []
        for phase in self.phases:
            info = self.phase_info.get(phase)
            if info:
                phases_summary.append({
                    "phase": phase.value,
                    "status": info.status.value,
                    "progress": info.progress,
                    "message": info.message,
                    "duration": info.duration,
                    "error": info.error,
                })

        return {
            "overall_progress": self.overall_progress,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "total_duration": self.total_duration,
            "is_complete": self.is_complete,
            "is_failed": self.is_failed,
            "phases": phases_summary,
        }
