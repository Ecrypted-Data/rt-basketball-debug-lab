# 篮球追踪故障排查练习

对应《技术选型与原型》任务三。项目读取视频，生成带标记的视频和逐帧 CSV。篮球完全不可见后，程序仍把最后一次检测到的位置标成当前位置。请复现、定位并修复，再检查正常可见和重新出现阶段。

## 复现

在 Ubuntu 或 WSL 的仓库根目录执行以下命令。使用 Python 3.10–3.13。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m basketball --output-dir runs/before
```

仓库自带实拍验收视频 `samples/basketball.mp4`，覆盖篮球正常可见、完全出画和重新进入画面三个阶段。上述命令会直接读取它。试跑其他视频时，可以加 `--input 视频路径`。

`tracking.csv` 记录帧号（从 0 开始）、视频时间（秒）、追踪状态、中心坐标和半径。`annotated.mp4` 便于核对画面。可见时应标出当前球的位置，丢失时应让使用者分辨当前位置不可用。

## 提交

先在 GitHub 上 Fork 本仓库，在自己的 Fork 里创建工作分支。完成后从该分支向原仓库的 `main` 发起 PR，并将 PR 链接填入飞书问卷。组长在 PR 中验收和反馈，验收后关闭 PR。

用同一段视频复测，把修复后输出写到 `runs/after`，保留两个目录用于对照。复现证据、定位依据和复测结果按飞书问卷中的题目提交。

## 本次修复与复测

```bash
python -m basketball --output-dir runs/after
python -m unittest discover -s tests -v
```

定位到 tracking.py 的 Tracker.update：原实现只在当前帧检测非空时更新历史位置，随后无条件把历史值作为当前结果返回。现在每帧直接使用当前检测（包括 None）；检测器与输出模块保持不变，缺测状态自然为 lost、CSV 坐标为空且不再绘制旧球位置。没有加入预测状态或新的检测算法。

同一实拍视频 302 帧：第 143–214 帧共 72 帧由错误的 visible/旧坐标变为 lost/空坐标；其余 230 帧的 CSV 记录逐字段与原基线一致。第175帧（2.916秒）完全出画，修复前仍为 visible,(14,315),r=59；修复后为 lost 且坐标空。第0帧正常可见，第215帧重新检出，第240帧完整可见，坐标均与基线一致。

修复前新回归测试 4 项中 3 项失败；修复后 4 项全部通过，覆盖可见→连续丢失→重新检出、开头无目标、真实视频全部302帧与当前检测对应、CSV 缺测输出。详见 [故障证据与复测](docs/verification.md)，前后 CSV、代表性帧与失败日志位于 docs/evidence/。
