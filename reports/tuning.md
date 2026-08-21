# 今彩539 中 3+ 直接優化驗證

- 模型：three_hit_optimizer
- 搜尋結構數：8
- 訓練期數：730
- 保留驗證期數：365
- 升級門檻：至少 13/365 次中 3+

## 訓練區排名

### 第 1 名

- 結構：`window=60, pool_size=14, triple_weight=1.0, number_weight=0.35, max_overlap=0`
- 訓練中 3+：18/730
- 訓練中 4+：1/730
- 訓練中 2+：176/730
- 訓練 ROI：-54.5%

### 第 2 名

- 結構：`window=200, pool_size=16, triple_weight=1.0, number_weight=0.35, max_overlap=0`
- 訓練中 3+：18/730
- 訓練中 4+：0/730
- 訓練中 2+：160/730
- 訓練 ROI：-82.5%

### 第 3 名

- 結構：`window=100, pool_size=16, triple_weight=1.0, number_weight=0.35, max_overlap=0`
- 訓練中 3+：15/730
- 訓練中 4+：0/730
- 訓練中 2+：172/730
- 訓練 ROI：-82.9%

### 第 4 名

- 結構：`window=30, pool_size=14, triple_weight=1.0, number_weight=0.35, max_overlap=0`
- 訓練中 3+：14/730
- 訓練中 4+：1/730
- 訓練中 2+：178/730
- 訓練 ROI：-55.6%

### 第 5 名

- 結構：`window=60, pool_size=12, triple_weight=1.0, number_weight=0.2, max_overlap=0`
- 訓練中 3+：14/730
- 訓練中 4+：0/730
- 訓練中 2+：176/730
- 訓練 ROI：-82.9%

## 保留驗證結果

- 事先選定結構：`window=60, pool_size=14, triple_weight=1.0, number_weight=0.35, max_overlap=0`
- 中 3+：6/365 (1.64%)
- 中 4+：0/365
- 中 2+：62/365
- ROI：-87.4%
- 命中分布：{0: 73, 1: 230, 2: 56, 3: 6}
- 判定：**未通過，維持目前每日模型**

> 最終結構只依訓練區排名選定；最近 365 期僅驗證一次。未達升級門檻不改每日模型。
