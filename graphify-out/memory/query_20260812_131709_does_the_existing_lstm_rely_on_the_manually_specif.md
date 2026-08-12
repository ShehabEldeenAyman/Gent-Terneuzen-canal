---
type: "query"
date: "2026-08-12T13:17:09.160524+00:00"
question: "Does the existing LSTM rely on the manually specified delay range of 46.5 hours?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["lag_analysis()", "deep_learning()", "create_sequences()"]
---

# Q: Does the existing LSTM rely on the manually specified delay range of 46.5 hours?

## Answer

Expanded from graph vocabulary: [lstm, sequences, lag, model, sensors, matrix]. No. In lag_analysis_fuseki.ipynb, the XGBoost/SVR/MLP path consumes lag_results through df_ml_features and explicitly shifts each upstream sensor by the selected lag, including Terneuzen at 46.5 hours. The separate LSTM path starts from raw aligned df_grid sensor channels, uses a 48-hour sequence window (192 quarter-hour samples), and never references lag_results or df_ml_features. It can learn temporal associations within that 48-hour history implicitly, but 46.5 hours is near the boundary and has only 1.5 hours of surrounding context, so a 72-hour lookback would be safer. The frontend deep_learning implementation follows the same raw-sequence design.

## Outcome

- Signal: useful

## Source Nodes

- lag_analysis()
- deep_learning()
- create_sequences()