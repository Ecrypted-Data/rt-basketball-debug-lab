# 修复记录：篮球出画后仍报告陈旧位置

- 基线：`main` @ `06e6ea5`
- 修复分支：`fix/stale-position-after-exit`
- 复测视频：`samples/basketball.mp4`（302 帧，60.014 fps，sha256 `f244ae13c9472ebb047d0c09caaaf41b947cad22decb66333c97fb82aff171a2`）
- 目标仓库：`Ecrypted-Data/rt-basketball-debug-lab` 的 `main`

## 复现

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m basketball --output-dir runs/before
```

修复前（`06e6ea5`）：

- `tracking.csv` 302 行全部为 `visible`（预期 230 `visible` / 72 `lost`）。
- 帧 143–214 共 72 行的坐标完全相同 `(14, 315, 59)`，就是出画前最后一帧 142 的位置。
- 标注视频帧 178：空场地上仍画着绿圈，并标记 `Frame 178 | VISIBLE`。
- 同一视频逐帧直接调用 `detect_ball()`：返回 `None` 的帧同样是连续 143–214，共 72 帧。

## 定位依据

`basketball/tracking.py` 的 `Tracker` 缓存了 `self._last_detection`：检测为 `None` 时不更新，
却仍把缓存值当作当前帧结果返回。由此：

- `TrackingResult.status` 由 `ball` 推导，恒为 `visible`；
- `basketball/output.py` 写 CSV 坐标和 `annotate()` 画圈都读取 `result.ball`，于是两者都停留在出画前的位置。

对照实验说明问题不在检测：同一视频成功解码 302 帧，`detect_ball()` 在 143–214 正确返回 `None`；
问题只在 `Tracker.update()` 的状态处理（`tracking.py:17-24`，基线版本）。

## 修复

`basketball/tracking.py`：删除 `__init__` 与 `_last_detection`，`update()` 直接返回当帧检测结果。
`status`、CSV 空坐标、丢失时不画圈等既有逻辑无需改动。

## 复测（同一视频）

```bash
python -m basketball --output-dir runs/before   # 06e6ea5
python -m basketball --output-dir runs/after    # 修复分支
```

| 检查项 | 修复前 | 修复后 |
| --- | --- | --- |
| CSV 行数 | 302 | 302 |
| `visible` / `lost` | 302 / 0 | 230 / 72 |
| 帧 143–214 | 72 行 `visible`，坐标恒为 `(14, 315, 59)` | 72 行 `lost`，坐标为空 |
| 帧 178 标注帧 | 空场 + 绿圈 + `VISIBLE` | 空场 + `LOST`，无圈 |
| 帧 0（正常可见） | `(174, 286, 54)` | 相同 |
| 帧 142（出画前） | `(14, 315, 59)` | 相同 |
| 帧 215（重新出现） | `(15, 210, 54)` | 相同 |

- CSV：0–142 与 215–301 的坐标逐行相同；只有 143–214 由“陈旧 `visible`”变为“`lost` + 空坐标”。
- 视频逐帧解码比对：0–142、216–301 像素完全相同；143–214 按预期变化（无圈、`LOST`）；
  215 因有损编码的参考帧变化出现轻微像素差（最大 43/255、均值 0.31），坐标、状态与标注一致。
- 帧号仍从 0 开始、`time_s` 与 60.014 fps 对齐，重新出现阶段检测位置正常。

## PR

`WeiYiLx:fix/stale-position-after-exit` → `Ecrypted-Data/rt-basketball-debug-lab:main`。
