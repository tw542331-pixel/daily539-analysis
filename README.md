# 台灣今彩539分析系統

以 Python 從**台灣彩券官方資料**更新歷史開獎紀錄，產生多視窗統計、兩組受約束選號，並以無資料穿越的滾動回測與隨機選號比較。資料僅用於統計研究，不代表或保證中獎。

## 官方資料端點調查

官方網站目前以前端呼叫 `TLCAPIWeB/Lottery/Daily539Result`，按 `month`、`pageNum`、`pageSize` 查詢 JSON；本專案預設使用：

```text
GET https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result?month=YYYY-MM&pageNum=1&pageSize=50
```

回應通常包含期別、日期及五個號碼。官方服務曾調整主機、路徑及 JSON 包裝，因此解析器容許 `content/data/result/results` 包裝及常見欄位名稱。此執行環境對官方網站的連線代理回傳 403，故 repository 不放入未經官方驗證的第三方資料；首次在可連線環境執行即會下載近五年。程式**沒有**使用 500.com 或任何中國彩券來源。

資料來源透過 `DrawSource` 抽象介面隔離。官方端點若再次改版，可用 `--source-url` 指向格式相容端點，或新增一個 `DrawSource` 實作，而不需修改分析、回測邏輯。

## 功能

- 近 10、30、100 期及五年：單號頻率、冷熱門、尾數、遺漏期數、奇偶、小大、和值、連號、前期重號及二碼組合。
- 每次產生 2 組 5 碼：奇偶與大小皆限定 2:3 / 3:2，和值採歷史四分位主要區間；排除五連號、全奇偶、全大小、單一十位區超過 3 碼等極端組合，兩組重疊最多 2 碼。
- 滾動回測的第 `t` 期僅將 `[:t]` 傳給策略，並比較每期兩組隨機選號的最佳命中數分布。
- 結果寫至 `reports/latest.md`；逐期回測明細寫至 `data/results.csv`，歷史資料快取於 `data/draws.csv`。

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

GitHub Actions 可在 Actions 頁手動觸發，亦於台灣開獎日週一至週六開獎後（UTC 13:30，即台灣 21:30）執行。流程先測試、更新資料和報告，再提交變更。若台灣彩券封鎖 GitHub runner，工作會明確失敗而不會靜默改用非官方來源。
