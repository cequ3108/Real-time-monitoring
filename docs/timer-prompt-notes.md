# Cursor / 本地排程用的盤中刷新提示詞（精簡版）

完整規則見 `docs/twse-intraday-bias-rules.md`。

本地可用 cron／Task Scheduler 每 5 分鐘：

```bash
cd /path/to/Real-time-monitoring
source .venv/bin/activate
export FINMIND_TOKEN=...
python -m twse_bias.cli report --positions data/positions.json
```

雲端 Cursor timer 請沿用助手訂閱的完整 prompt（含 13:30 收盤流程與倉位建議區塊）。
