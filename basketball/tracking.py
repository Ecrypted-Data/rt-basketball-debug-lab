from dataclasses import dataclass

from .detection import Ball


@dataclass(frozen=True)
class TrackingResult:
    frame_index: int
    time_seconds: float
    ball: Ball | None

    @property
    def status(self) -> str:
        return "visible" if self.ball is not None else "lost"


class Tracker:
    def update(self, frame_index: int, fps: float, detection: Ball | None) -> TrackingResult:
        return TrackingResult(frame_index, frame_index / fps, detection)
