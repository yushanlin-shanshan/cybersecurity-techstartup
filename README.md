# cybersecurity-techstartup

SCU AIC × CrowdStrike hackathon, Track 2 (Detect). Working concept: NonprofitShield AI.

## 测试流程

主程序可以还没写。在仓库根目录运行：

```bash
python3 testing/run_workflow.py
```

退出码 0 表示这次跑通的是当前合同，不是生产检测准确率。`backend/detection.py` 只实现“同一用户至少 5 次失败后出现成功登录”这一条规则。用法见 [docs/testing/WORKFLOW.md](docs/testing/WORKFLOW.md)。勘察记录见 [TESTING_BASELINE.md](TESTING_BASELINE.md)。