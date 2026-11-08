# Xichen：当前交接与下一步

首轮已经完成：5 条记录（1 development、4 test），rules 生成 5 条预测；LLM 的 1 条 development 和 3 条 test 通过验证，另 1 条 test 的异常响应原样保留。已按相同配置完整复跑一次：再次得到 4 条有效输出和同一条失败，有效分类均一致。两轮分别保存，没有第三次重试。API 访问、输入公平性、cutoff 和 splits 已确定，不需要重新安装或配置。

当前材料：

- `Morocco_blind_review_2026-11-08.zip`：只给 Noah、Yuxin 的独立核验/标注包，无模型预测。
- `Morocco_execution_2026-11-08.zip`：给 Xichen 保存的实验审计包，含预测、失败、原始响应、冻结配置和来源记录。两人提交独立标签前不要给他们看其中预测。
- [执行协议](docs/EXECUTION_PROTOCOL_2026-11-08.md)：范围、纳入排除、日期、来源和限制。
- [方法附录](APPENDIX_METHOD.md)：相同输入、模型设置、prompt 位置和流程图。
- [实际进展](PROGRESS_2026-11-08.md)：准确的运行数量和未完成项。

## Noah、Yuxin 需要做的事

各自解压盲标包，用桌面浏览器打开 `reviewer-packet.html`，独立完成四条记录：先核对组织/AI任务/摩洛哥范围，再选阶段、复制原文依据、写 rationale。字段有误就选 Needs correction 并说明，不能用 insufficiently_supported 掩盖字段问题。

每条 Save 后经常 Export。关闭页面前必须导出；页面不自动保存。各自返回 `noah.jsonl` 和 `yuxin.jsonl`，先保留原始独立结果，再讨论和仲裁。包内有指南、来源文字及银行原始 PDF。任何法语翻译辅助都要记录。没有自动发送任何消息。

## 收到标签后的处理

1. 检查两份文件覆盖相同四条 test IDs，reviewer IDs 不同，字段核验状态完整。
2. 若有字段/context 实质修正，保留旧版本，说明修正原因，并决定新的冻结/运行；不要在旧输入上改字后复用原预测。
3. 对未讨论的原始独立标签计算 agreement；需要修正或空标签时停止，不能把它们当成第五个部署阶段。
4. 保存独立仲裁后的 gold，与模型输出隔离。确认输入未变后，建立新的、带人工核验记录的 study 快照，逐项比对旧冻结 inputs/splits/rules/prompt。当前 `prediction_pending_human_review` 目录不能评分。
5. 主分析使用首轮的 4 条 test 尝试：3 条 accepted 加 1 条 failures。失败计入其 gold 类的 false negative，保留四类 macro-F1；矩阵额外一列 invalid_output 仅审计，不是第五种阶段。报告 3/4 输出覆盖率。完整复跑作为独立可靠性检查，不拼接两轮结果。
6. 只有以上条件满足后，输出 macro-F1、per-class scores、confusion matrices 和 false-operational rate。四条 test 只支持描述性结果，不支持泛化优势或语言比较。

Agreement 命令（只在两份完整且独立的标签就绪后）：

```bash
python3 -m morocco.experiment agreement data/noah.jsonl data/yuxin.jsonl \
  --output data/agreement.json
```

False-operational rate 保留原定义：错误 operational 预测数 / 全部 operational 预测数。分母 0 时为 null。Macro-F1 固定四类，缺失类贡献 0，并同时报告 support。kappa 在预期一致率为 1 时未定义。

评分命令（仅在人工核验后的 study 快照和 gold 就绪后，以下为待满足条件，不会自动执行）：

```bash
python3 -m morocco.experiment evaluate data/human-reviewed-frozen \
  --predictions data/execution-20261108-v1/llm-test/accepted_predictions.jsonl \
  --failures data/execution-20261108-v1/llm-test/failures.jsonl \
  --gold data/gold-test.jsonl --output data/final-results
```

`--failures` 要求成功与失败 IDs 不重叠且完整覆盖所选 split；缺失、重复、额外 ID 会报错。当前 pending-human-review 冻结版本即使传此参数也禁止评分。

## 故障与复现

`morocco.run_model` 保存每条原始响应并严格验证。`morocco.complete_batch` 可在同一冻结配置下继续尚未请求的记录，已有失败或成功响应都不会被再次请求；它分别写 accepted_predictions.jsonl、failures.jsonl 和 batch_metadata.json。只有全批通过才生成完整 predictions.jsonl。

本次首轮 test 完成器已请求完所有四条，重复运行只会复用缓存。此前审批阻塞后，用户授权继续。完整复跑现已完成，同一条失败重现，另四条有效输出的分类一致。两轮的输入和请求 hashes 一致；没有第三次重试。

验证代码：

```bash
python3 -m unittest discover -s tests -v
```

API key 仅存在本地忽略文件/环境变量，不在交付包或仓库中。代码更新在 PR #2，未合并 main。
