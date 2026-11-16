# 任务三：故障定位与实际验收

日期：2026-11-16。基线提交 06e6ea5b219dc10bf993fdefff84a79bfc36d858。依赖按 requirements.txt：Python 3.12.15、NumPy 2.2.6、OpenCV 4.11.0.86。

## 复现

`python -m basketball --output-dir runs/before`，302帧，输入 samples/basketball.mp4（SHA-256 f244ae13c9472ebb047d0c09caaaf41b947cad22decb66333c97fb82aff171a2）。帧号从0开始。

第175帧（2.916秒）画面已完全没有篮球，但 CSV 仍输出 `175,2.916,visible,14,315,59`；标注视频还绘制旧球位置。预期是 lost、坐标和半径为空、图像不画旧位置。

## 定位证据

在同一帧独立调用 detection.detect_ball 得到 None，而原 Tracker.update 返回 Ball(x=14,y=315,radius=59)。首次分歧位于第143帧，证明视频已经成功读出且检测器给了缺测值，错误在追踪结果整理环节。代码中 `_last_detection` 只在非空检测时更新，却在每帧无条件返回，因此把历史位置当作当前位置。

先新增回归测试再改程序，4个测试中3个失败，第一处断言为 `Ball(x=14,y=315,radius=59) != None : frame 143`。原始失败输出见 evidence/before-regression-tests.txt。

## 修复与同输入复测

仅修改 tracking.py，让每帧返回当前 detection，并去掉造成错误的历史位置缓存。未改视频读取、检测阈值或输出格式。

`python -m basketball --output-dir runs/after`：仍输出302帧。
`python -m unittest discover -s tests -v`：4个测试全部通过。

| 阶段 | 帧号 | 修复前 | 修复后 |
|---|---:|---|---|
| 正常可见 | 0 | visible,174,286,54 | 一致 |
| 完全出画 | 175 | visible,14,315,59 | lost，三个坐标字段为空 |
| 重新检出 | 215 | visible,15,210,54 | 一致 |
| 回画后可见 | 240 | visible,153,232,51 | 一致 |

- 143–214共72帧全部清除旧位置；其余230帧 CSV 每条记录与基线完全一致。
- 对真实视频的全部302帧逐一核对 TrackingResult.ball 与当前帧原始 detect_ball，一致。
- 前后标注视频均能完整解码302帧；229帧像素完全相同，73帧发生像素变化。视频采用有损帧间压缩，变化可能传播到相邻帧，因此不将压缩后像素差异直接当作额外追踪行为变化，正常/重新出现阶段以原始检测与CSV逐帧对照为准。
- evidence/comparison.json 保留阶段数据，before/after-tracking.csv 保留原始CSV；第0、175、240帧前后图供目视核对。

限制：沿用课程原检测器。球部分出画时也可能被判为缺测；本次只修复缺测仍输出旧位置，不宣称改进检测准确率。
