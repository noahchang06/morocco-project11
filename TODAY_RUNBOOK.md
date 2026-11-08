# Xichen：当天完成运行与交付

代码起点：`bab49b1e80754f46b4f09bcaee1e39c3e95144d7`。
25 项离线测试通过；已完成真实模型访问验证和 1 条开发候选的有效 LLM 预测。首次响应因引文换行不匹配被拒绝，另存新 prompt 版本后通过。尚无正式研究成绩，详见 PROGRESS_2026-11-08.md。
工作分支：`txc701/fair-evaluation`。提交与合并状态以 GitHub PR 为准。

## 正式运行所需材料（人工标签仅评分阶段需要）

1. `data/curated/records.jsonl`：已确认 eligibility 的正式记录。
2. `data/processed/pages.jsonl`：与 quote/offset 对应的原始提取页，不要重新提取后混用旧 offsets。
3. `data/noah.jsonl`、`data/yuxin.jsonl`：讨论前的两份独立标签，保留原文件。
4. `data/gold-test.jsonl`：第三人仲裁后的 test 标签，不能由 LLM 代填。
5. `data/splits.json`：`{"record-id":"development", "another-id":"test"}`；正式测试须非空且按 organization 隔离。
6. `data/calibration-ids.json`：已讨论案例的 record_id JSON 数组；同一 organization 的所有记录都必须留在 development。
7. 团队确认的 cutoff 日期与 outdated 年数。修订 proposal 已指定 `gpt-4.1-mini-2025-04-14`、temperature 0；实际账号访问与开发调用已验证。当前代码按新指南暂用 2 年，不代表团队已批准。

每份人工标签最少包含 `record_id` 和 `label`，建议保留 reviewer_id、guide version、rationale、reason_code 和 notes。
Agreement 要求两人标签 ID 完全相同；gold-test 的 ID 必须与 test split 完全相同。
调用凭据只在运行电脑的环境变量 `OPENAI_API_KEY` 中配置，不发送到聊天或写入仓库。

## 第一步：安装检查与冻结

分类、评估和新增运行器只用 Python 标准库。已有提取页时不需要重新处理 PDF。

```bash
python3 -m unittest discover -s tests -v
```

先用 development records 验证模型访问和输出，再冻结正式试验。以下变量必须改成团队确认的实际值，不能原样执行占位符：

```bash
export MOROCCO_MODEL='gpt-4.1-mini-2025-04-14'
export MOROCCO_CUTOFF='YYYY-MM-DD'
python3 -m morocco.experiment freeze data/curated/records.jsonl \
  --pages data/processed/pages.jsonl \
  --output data/final-frozen \
  --model "$MOROCCO_MODEL" --as-of-date "$MOROCCO_CUTOFF" \
  --splits data/splits.json --calibration-ids data/calibration-ids.json \
  --outdated-years 2 --model-settings config/proposal-model-settings.json
```

`freeze` 不接受已存在的输出目录。已有冻结目录不可直接改文件；协议、prompt 或参数变更要另建版本并说明原因。开发试跑与正式试验用不同目录。上面的 settings 文件显式设 temperature=0 和 max_output_tokens=1500；前者来自修订 proposal，后者是本实现的输出上限。temperature 0 不保证完全确定性。若省略 settings 文件，通用 CLI 不会自动套用 proposal 的 temperature。

已明确标注为未确认纳入的候选不能进行 study freeze。诊断性开发运行需显式使用 `--purpose development_smoke_test`，全部记录只能属于 development，且禁止生成研究评估指标。

公平性改动：两套方法共享同一份 `inputs.jsonl`。每条 evidence 包括原 quote、核对后的 context、来源日期、类型、URL、语言等 metadata。传入的 context 文本不会被信任，context 从 preserved page 重新切片。

可在 evidence 中提供 `context_start` 和 `context_end`，使用标注前确定的完整相关段落；范围必须覆盖原 quote。不提供时使用完整原始页，`context_scope` 会记录这一点。完整页可能有其他应用或页眉，主实验前应检查。两种方法的上下文必须同时改变。不要把人工标注后挑出的决定性引文或理由回填输入。

## 第二步：执行模型

先检查，不调用 API，也不证明模型访问可用：

```bash
python3 -m morocco.run_model data/final-frozen \
  --split development --output data/model-dev --dry-run
```

在终端安全配置 `OPENAI_API_KEY` 后，development 试跑：

```bash
python3 -m morocco.run_model data/final-frozen \
  --split development --output data/model-dev
```

确认配置后执行 test，随后不按 test 错误继续调规则或 prompt：

```bash
python3 -m morocco.run_model data/final-frozen \
  --split test --output data/model-test
```

同一命令可恢复中断，已记录的响应不会再次请求。原始响应保存在 `raw/`，全部通过 schema、ID 和引用检查后才写 predictions.jsonl。API 异常、拒答、截断或非法输出不会被伪装成 insufficiently_supported，也不会悄悄丢弃；失败时停止，检查原始响应并记录处置。如果进程被强杀留下 `.running`，确认没有运行中的进程后才能删除该锁再恢复。每个目录只能有一个运行进程。

运行器使用 OpenAI Responses API；账户权限、模型 snapshot 可用性、支持的参数、费用和网络连接须以 development 实际调用为准。不要把模拟测试当作验证。实际返回 model 必须与冻结标识完全一致。

## 第三步：算 agreement 和最终比较

先对原始独立标签算 agreement，之后再仲裁：

```bash
python3 -m morocco.experiment agreement data/noah.jsonl data/yuxin.jsonl \
  --output data/agreement.json
```

使用单独保留的最终 test gold：

```bash
python3 -m morocco.experiment evaluate data/final-frozen \
  --predictions data/model-test/predictions.jsonl \
  --gold data/gold-test.jsonl --output data/final-results
```

提供给 Noah：

- `data/agreement.json`：N、raw agreement、Cohen's kappa。
- `data/final-results/report.md`：macro-F1、各类 precision/recall/F1/support、两张 confusion matrix。
- `data/final-results/results.json`：完整指标和按 organization 聚类的 bootstrap 区间；少于两个组织时不提供区间。
- `data/final-results/false_operational_audit.jsonl`：需要人工复核的误报。
- `data/final-frozen/config.json`、`manifest.json`、`data/model-test/run_metadata.json` 和 `APPENDIX_METHOD.md`：prompt、版本、参数、证据与流程说明。

保留原定义：false-operational rate = 非 operational gold 却预测 operational 的数量 / 全部 operational 预测数量。没有 operational 预测时为 null，不写 0。Macro-F1 固定四类，缺失类别贡献 0，要同时报告各类样本数。Cohen's kappa 在预期一致率为 1 时不定义，不伪造为 1。

## 停止条件与真实依赖

完成代码、development 访问验证、正式预测、agreement、评估和附录后，你的技术部分即可交接。不要为了补类别临时编记录，或拿 calibration cases 凑 test。

若今天人工标签没齐，能交付的是可运行代码、冻结输入、模型预测（若访问已就绪）及明确的未完成项；不能声称 4.3/4.4 的实证结果已经完成。请组员直接交原始文件，不用你重新手工录入表格。
