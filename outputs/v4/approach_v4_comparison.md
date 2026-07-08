# Approach v4 Comparison Table

| Horizon   | Version                      | F1-Score   | Precision   | Recall   | False Alarm Rate   |   MAE (degC) |   RMSE (degC) |
|:----------|:-----------------------------|:-----------|:------------|:---------|:-------------------|-------------:|--------------:|
| 5 Min     | LightGBM (All Features)      | 91.11%     | 91.84%      | 90.39%   | 0.1080%            |       0.1349 |        0.273  |
| 5 Min     | LightGBM (Selected Features) | 88.38%     | 85.93%      | 90.97%   | 0.2003%            |       0.1497 |        0.2801 |
| 5 Min     | LSTM (All Features)          | 90.11%     | 95.43%      | 85.35%   | 0.0549%            |       0.1465 |        0.2548 |
| 5 Min     | LSTM (Selected Features)     | 89.86%     | 90.82%      | 88.92%   | 0.1209%            |       0.1508 |        0.2599 |
| 5 Min     | Seq2Seq (All Features)       | 90.26%     | 88.94%      | 91.63%   | 0.1533%            |       0.1469 |        0.2665 |
| 5 Min     | Seq2Seq (Selected Features)  | 89.46%     | 86.77%      | 92.31%   | 0.1894%            |       0.1559 |        0.2642 |
| 15 Min    | LightGBM (All Features)      | 86.95%     | 88.66%      | 85.31%   | 0.1468%            |       0.2292 |        0.4204 |
| 15 Min    | LightGBM (Selected Features) | 85.19%     | 83.31%      | 87.17%   | 0.2349%            |       0.2456 |        0.4332 |
| 15 Min    | LSTM (All Features)          | 85.85%     | 84.20%      | 87.58%   | 0.2211%            |       0.2406 |        0.4136 |
| 15 Min    | LSTM (Selected Features)     | 86.84%     | 89.10%      | 84.69%   | 0.1394%            |       0.2397 |        0.4009 |
| 15 Min    | Seq2Seq (All Features)       | 85.34%     | 85.99%      | 84.69%   | 0.1857%            |       0.2445 |        0.4269 |
| 15 Min    | Seq2Seq (Selected Features)  | 83.47%     | 79.22%      | 88.19%   | 0.3113%            |       0.2462 |        0.428  |
| 30 Min    | LightGBM (All Features)      | 84.27%     | 85.86%      | 82.74%   | 0.1832%            |       0.3121 |        0.5419 |
| 30 Min    | LightGBM (Selected Features) | 81.37%     | 80.13%      | 82.64%   | 0.2755%            |       0.3362 |        0.5674 |
| 30 Min    | LSTM (All Features)          | 81.37%     | 87.06%      | 76.39%   | 0.1528%            |       0.3249 |        0.5501 |
| 30 Min    | LSTM (Selected Features)     | 82.23%     | 78.80%      | 85.96%   | 0.3112%            |       0.3285 |        0.5548 |
| 30 Min    | Seq2Seq (All Features)       | 78.43%     | 81.68%      | 75.43%   | 0.2277%            |       0.3489 |        0.5732 |
| 30 Min    | Seq2Seq (Selected Features)  | 76.89%     | 70.43%      | 84.66%   | 0.4785%            |       0.344  |        0.5844 |
| 60 Min    | LightGBM (All Features)      | 72.74%     | 74.15%      | 71.38%   | 0.3347%            |       0.4196 |        0.673  |
| 60 Min    | LightGBM (Selected Features) | 73.15%     | 73.86%      | 72.44%   | 0.3448%            |       0.4435 |        0.6873 |
| 60 Min    | LSTM (All Features)          | 73.80%     | 66.60%      | 82.74%   | 0.5584%            |       0.4469 |        0.6881 |
| 60 Min    | LSTM (Selected Features)     | 72.46%     | 76.48%      | 68.84%   | 0.2850%            |       0.4435 |        0.6844 |
| 60 Min    | Seq2Seq (All Features)       | 63.57%     | 70.24%      | 58.06%   | 0.3312%            |       0.4974 |        0.7533 |
| 60 Min    | Seq2Seq (Selected Features)  | 64.46%     | 56.00%      | 75.94%   | 0.8032%            |       0.4854 |        0.7759 |
