# Lag analytics workspace

This standalone service turns the workflow in `time_series_analysis/lag_analysis.ipynb`
into an interactive API without importing or changing the notebook or pipeline execution
code. It reads SOSA observations from Apache Jena Fuseki, prepares a 15-minute grid, and
offers independent endpoints for:

- live data loading and visualization;
- causally constrained lag/cross-correlation analysis;
- XGBoost, SVR, and MLP delta forecasting;
- an LSTM autoencoder plus forecast head;
- one- and multidimensional matrix profiles, motifs, and discords.

## Start

From the repository root:

```powershell
python -m pip install -r lag_analytics_workspace/requirements.txt
python -m uvicorn lag_analytics_workspace.server:app --reload --port 8010
```

The frontend expects this service at `http://localhost:8010`. Override that with
`VITE_ANALYTICS_API_URL` when starting Vite.

## Fuseki configuration

The service uses the same environment variable names as the ingestion code:

```powershell
$env:FUSEKI_DATA_URL = "http://localhost:3030/dataset/data"
# Optional explicit override:
$env:FUSEKI_QUERY_URL = "http://localhost:3030/dataset/query"
$env:ANALYTICS_DEFAULT_GRAPH_URI = "http://example.com/Gent-Terneuzen"
```

No Virtuoso endpoint or `SPARQLWrapper` is used. Queries are sent as read-only SPARQL
requests to Fuseki's `/query` endpoint.

## Conductivity units

All analytics use **milliSiemens per centimetre (mS/cm)**. The reader groups values
by observation before pivoting and uses QUDT unit metadata to normalize them.

It also recognizes the legacy graph produced by the former alignment formula:

- Waterinfo values stored in S/m but labelled mS/cm are multiplied by 10.
- Water-Link observations containing both raw µS/cm and converted S/m results are
  collapsed to one value and divided by 1,000 from the raw measurement.

This compatibility behavior is activated only when the duplicate Water-Link
raw/converted signature is present in the queried graph. A graph rebuilt with the
corrected alignment implementation is therefore read normally without an extra factor.
