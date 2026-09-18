# Real-time-monitoring

台股盤中多空助手（偏做多）規則與本地執行骨架。可接 FinMind 行情；庫存請由本機康和 API 匯出後餵入。

## 文件

- 完整規則：[`docs/twse-intraday-bias-rules.md`](docs/twse-intraday-bias-rules.md)
- 康和接點說明：[`twse_bias/brokers/concord_stub.py`](twse_bias/brokers/concord_stub.py)
- 庫存範例：[`data/positions.example.json`](data/positions.example.json)

## 本地快速開始

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FINMIND_TOKEN=你的token

# 僅行情報告
python -m twse_bias.cli report

# 搭配庫存（從康和匯出或手動編輯）
cp data/positions.example.json data/positions.json
# 編輯 data/positions.json 成你的真實部位
python -m twse_bias.cli report --positions data/positions.json
```

## 倉位檔位（摘要）

依大盤現價相對「做多／保守／減碼／開盤」線：

1. **積極加倉**：≥做多線 + 綠燈 + 量能達黃以上  
2. **偏多持有**：做多～保守之間  
3. **保守觀望**：保守～減碼之間  
4. **減碼**：＜減碼線但仍＞開盤  
5. **清倉防守**：＜開盤或紅燈  

個股：破開不買；平開強勢可開；近高不追。

## 康和 API（本機）

雲端助手無法登入你的康和帳號。請在 Windows 本機：

1. 向營業員申請開通 API（[程式小幫手](https://stock.concords.com.tw/trade_071.html)）
2. 用官方元件或 [conrich](https://concords6016.github.io/conrich_docs/) 查庫存
3. 寫成 `data/positions.json`（格式同 example）
4. 再跑 `python -m twse_bias.cli report --positions data/positions.json`

## 免責

僅分析建議，不構成投資建議。下單與風險自負。
