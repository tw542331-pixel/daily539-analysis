# 今彩539 模型調參驗證

- 搜尋參數組數：12
- 訓練期數：730
- 保留驗證期數：365
- 顯示訓練排名數：5

## 訓練區排名

### 第 1 名

- 參數：`weight_10=0.5, weight_30=0.35, weight_100=0.35, weight_5y=0.1, missing_weight=0.15, pair_weight=0.15, sum_weight=0.15, tail_weight=0.1, repeat_weight=0.25`
- 訓練中 3+：17/730
- 訓練中 4+：1/730
- 訓練中 2+：160/730
- 訓練 ROI：-56.1%

### 第 2 名

- 參數：`weight_10=0.2, weight_30=0.5, weight_100=0.65, weight_5y=0.1, missing_weight=0.15, pair_weight=0.15, sum_weight=0.15, tail_weight=0.1, repeat_weight=0.25`
- 訓練中 3+：17/730
- 訓練中 4+：0/730
- 訓練中 2+：176/730
- 訓練 ROI：-82.0%

### 第 3 名

- 參數：`weight_10=0.35, weight_30=0.45, weight_100=0.65, weight_5y=0.25, missing_weight=0.15, pair_weight=0.15, sum_weight=0.0, tail_weight=0.0, repeat_weight=0.0`
- 訓練中 3+：15/730
- 訓練中 4+：0/730
- 訓練中 2+：174/730
- 訓練 ROI：-82.7%

### 第 4 名

- 參數：`weight_10=0.35, weight_30=0.5, weight_100=0.5, weight_5y=0.1, missing_weight=0.15, pair_weight=0.15, sum_weight=0.15, tail_weight=0.1, repeat_weight=0.25`
- 訓練中 3+：14/730
- 訓練中 4+：0/730
- 訓練中 2+：181/730
- 訓練 ROI：-82.6%

### 第 5 名

- 參數：`weight_10=0.35, weight_30=0.45, weight_100=0.65, weight_5y=0.25, missing_weight=0.15, pair_weight=0.15, sum_weight=0.15, tail_weight=0.1, repeat_weight=0.25`
- 訓練中 3+：14/730
- 訓練中 4+：0/730
- 訓練中 2+：166/730
- 訓練 ROI：-83.6%

## 保留驗證結果

- 事先選定參數：`weight_10=0.5, weight_30=0.35, weight_100=0.35, weight_5y=0.1, missing_weight=0.15, pair_weight=0.15, sum_weight=0.15, tail_weight=0.1, repeat_weight=0.25`
- 中 3+：5/365 (1.37%)
- 中 4+：0/365
- 中 2+：81/365
- ROI：-85.5%
- 命中分布：{0: 78, 1: 206, 2: 76, 3: 5}

> 最終參數只依訓練區排名選定；最近 365 期僅驗證一次，不再用驗證結果挑參數。
