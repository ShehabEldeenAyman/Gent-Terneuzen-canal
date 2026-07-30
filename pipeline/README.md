# Pipeline Playground

The playground exposes the Water-Link and Waterinfo-conductivity pipelines as
fixed, inspectable stages. It does not start or use the forecasting service.

From the repository root, install the Python requirements and run:

```powershell
python -m pip install -r requirements.txt
uvicorn pipeline.playground_server:app --reload --port 8000
```

Then, in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). The front end calls the
playground API on port 8000. Set `VITE_PIPELINE_API_URL` if the API is hosted
elsewhere.

Each action is deliberately fixed to a named use case and stage; the API does
not accept arbitrary shell commands or paths. Generated CSV, Turtle, SHACL
report, and N3 artifacts can be previewed in the interface.
