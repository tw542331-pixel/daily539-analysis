# 台灣今彩539分析系統

以 Python 從**台灣彩券官方資料**更新歷史開獎紀錄，產生多視窗統計、兩組受約束候選組合，並以無資料穿越的向前回測同時比較舊版模型與隨機選號。資料僅用於統計研究，不代表或保證中獎。

## 官方資料端點調查

官方網站目前以前端呼叫 `TLCAPIWeB/Lottery/Daily539Result`，按 `month`、`pageNum`、`pageSize` 查詢 JSON；本專案預設使用：

```text
GET https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result?month=YYYY-MM&pageNum=1&pageSize=50
```

回應通常包含期別、日期及五個號碼。官方服務曾調整主機、路徑及 JSON 包裝，因此解析器容許 `content/data/result/results` 包裝及常見欄位名稱。此執行環境對官方網站的連線代理回傳 403，故 repository 不放入未經官方驗證的第三方資料；首次在可連線環境執行即會下載近五年。程式**沒有**使用 500.com 或任何中國彩券來源。

資料來源透過 `DrawSource` 抽象介面隔離。官方端點若再次改版，可用 `--source-url` 指向格式相容端點，或新增一個 `DrawSource` 實作，而不需修改分析、回測邏輯。

## 功能

- 近 10、30、100 期及五年：單號頻率、冷熱門、尾數、遺漏期數、奇偶、小大、和值、連號、前期重號及二碼組合。
- 單號評分真正使用近 10、30、100 期與近 5 年的標準化頻率；遺漏只占小幅且有上限的權重，避免「久未開就該開」的謬誤。
- 組合評分納入近 100 期二碼、和值位置、尾數分散與前期重號；奇偶與大小限定 2:3 / 3:2，並排除過度集中及極端組合。
- 每次產生 2 組 5 碼，優先完全不重複，涵蓋 10 個不同號碼；模型不使用隨機亂數打破同分，因此同一份資料會得到相同結果。
- 最近 365 期向前回測的第 `t` 期只使用 `[:t]`，並同時呈現重作模型、舊版模型及每期兩組不重複隨機選號的最佳命中數。
- 報告明確標示下一期預測目標日，並公開上一期對獎、實戰累積投入、獎金、淨損益及 ROI，避免把「中 2 碼」誤認為獲利。
- 回測同時呈現每注命中數、獎金與 ROI；相對分數只用於排序，不是假裝成中獎機率或獲利率。
- 結果寫至 `reports/latest.md`；逐期回測明細寫至 `data/results.csv`，歷史資料快取於 `data/draws.csv`，實際發布過的候選組合保留於 `data/predictions.csv`。

## 安裝與執行

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src python -m daily539.cli
```

離線重做既有資料的報告：

```bash
PYTHONPATH=src python -m daily539.cli --no-fetch --seed 539
```

替換相容官方端點：

```bash
PYTHONPATH=src python -m daily539.cli --source-url 'https://example.invalid/Daily539Result'
```

## 測試

```bash
pytest
```

## 自動更新

GitHub Actions 可在 Actions 頁手動觸發，亦於台灣開獎日週一至週六晚上 21:30、22:00、22:30、23:00、23:30 自動嘗試更新。流程先測試、抓取資料並產生報告；若台彩官方 API 尚未提供當天資料，該次執行會明確標示失敗並等待下一次排程重試，不再把舊資料顯示為更新成功。內容有變更才提交，不會重複寫入；單次工作最長 15 分鐘。

`--seed` 只控制舊版與隨機回測基準，重作模型本身是確定性的。彩券開獎為隨機事件，歷史回測較佳不代表未來仍有優勢，也不應用於追損。
