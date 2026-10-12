# cybersecurity-techstartup

SCU AIC × CrowdStrike hackathon, Track 2 (Detect). Working concept: NonprofitShield AI.

## 测试流程

主程序可以还没写。在仓库根目录运行：

```bash
python3 testing/run_workflow.py
```

退出码 0 表示测试流程跑通。`backend/detection.py` 还是空文件时，场景会计为 blocked，不会输出检测准确率。用法和合同见 [docs/testing/WORKFLOW.md](docs/testing/WORKFLOW.md)。执行记录见 [TESTING_REPORT.md](TESTING_REPORT.md)。