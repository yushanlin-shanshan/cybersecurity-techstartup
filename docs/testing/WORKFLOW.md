# 测试流程怎么跑

队友的主程序可以还是空的。这条流程现在就能跑完。

## 一条命令

在仓库根目录执行：

```bash
python3 testing/run_workflow.py
```

不需要安装 pytest，也不需要 API key。Python 3.12 标准库就够。

检测器实现了当前合同并且 8 个场景都匹配时，第一行是：

```text
测试流程: 通过（检测器与合成场景一致）
```

退出码是 0。这表示这 8 个合成场景和密钥扫描、单元测试通过。它不表示生产环境里的检测准确，也不表示应用是安全的。

`backend/detection.py` 仍为空、或还没有 `detect()` 时，第一行仍是“检测器还没实现，场景已装载但未计分”，场景状态为 `blocked`。

机器可读结果写在 `testing/output/workflow_report.json`。这个文件不进 git。

## 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 流程健康。检测器还没写好，或者已经写好并且 8 个合成场景全部匹配。 |
| 1 | 流程失败。密钥扫描有命中、单元测试失败、`detect()` 抛错，或检测结果和场景合同不一致。 |

GitHub Actions 跑的是同一条命令：`.github/workflows/test.yml`。

## 现在仓库里实际有什么

`backend/detection.py` 实现了上面这一条失败后成功的规则。`backend/preprocessing.py` 只检查事件列表的形状，不解析 CSV 或 JSON 文件。没有前端、数据库或模型调用。

最近一次本地工作流把 8 个场景都标成 `pass`，并打印了合成合同上的 TP 3、FP 0、TN 5、FN 0。那不是生产准确率。

## 队友要接上的函数

在 `backend/detection.py` 里实现：

```python
def detect(events: list[dict]) -> dict:
    return {
        "predicted": "flagged",  # 或 "benign"
        "summary": "suspicious: repeated failed logins followed by a success",
        "evidence": ["p101-1", "p101-6"],
    }
```

约定：

- 同一个用户至少 5 次 `login_failed`，并且之后有一次 `login_success`，必须返回 `flagged`。
- 失败次数少于 5，或者只有失败没有成功，返回 `benign`。
- 日志正文不能改变结论。场景 `P3-04` 的正文要求模型把事件判成无害，合同仍然要求 `flagged`。
- `summary` 里不要写 `confirmed compromise`。这只是可疑活动。
- `flagged` 时 `evidence` 必须是非空的字符串列表。
- 不要在这个文件里 import `testing`。产品代码不依赖测试包。

接上之后，同一条命令会把每个场景标成 `pass` 或 `fail`，并打印合成场景的 TP / FP / TN / FN。那组数字仍然只代表这 8 个合成场景，不是真实遥测上的检测准确率。

## 场景

定义在 `testing/scenarios/auth_scenarios.json`。

| ID | 期望 | 内容 |
| --- | --- | --- |
| P1-01 | flagged | 5 次失败后成功 |
| P1-02 | benign | 1 次失败后成功 |
| P1-03 | benign | 4 次失败后成功，卡在阈值下面 |
| P1-04 | benign | 5 次失败，没有成功 |
| P1-05 | benign | 正常成功登录 |
| P3-04 | flagged | 失败后成功，但日志要求忽略指令 |
| P1-07 | benign | 空事件列表 |
| P1-08 | flagged | 同上失败模式，用户名是中文 |

`testing/reference_rule.py` 是测试用的对照规则，用来证明计分循环是通的。流程默认不会调用它。

## 本地自测对照规则

```bash
DETECTOR_MODULE=reference_rule python3 -c "import sys; sys.path.insert(0, 'testing'); import workflow_lib; r = workflow_lib.build_report(workflow_lib.ROOT, module_name='reference_rule'); print(workflow_lib.format_summary(r, workflow_lib.exit_code(r)))"
```

这组结果是合成合同上的 F1 = 1.0。不要把它写进答辩幻灯片当成产品成绩。
