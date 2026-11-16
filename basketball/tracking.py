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
        # 只把"当前帧"的检测结果当作当前位置：
        # 球出画时 detection 为 None，必须原样传递（ball=None → status=lost、坐标留空），
        # 不能缓存出画前的旧检测结果再当作当前位置返回，
        # 否则出画后会把旧位置误标成 visible 的当前位置（本练习的故障根因）。
        return TrackingResult(frame_index, frame_index / fps, detection)
