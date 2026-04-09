from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import mlflow.sklearn
import mlflow
import joblib
from transformers import TextCleaner

_ = TextCleaner

production_model = None
startup_error = None
model_source = None
STATIC_DIR = Path(__file__).parent / "static"
DEFAULT_MODEL_PATH = Path(__file__).parent / "artifacts" / "sentiment_model.joblib"


def load_production_model():
    configured_model_path = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
    if configured_model_path.exists():
        return joblib.load(configured_model_path), f"artifact:{configured_model_path}"

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    experiment = mlflow.get_experiment_by_name("Sentiment_Classifier_MVP")
    if experiment is None:
        raise RuntimeError(
            "Model artifact not found and MLflow experiment 'Sentiment_Classifier_MVP' does not exist in this environment."
        )

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["start_time DESC"],
        max_results=1,
    )
    if runs.empty:
        raise RuntimeError("MLflow experiment exists but has no FINISHED runs.")

    latest_run_id = runs.iloc[0].run_id
    model_uri = f"runs:/{latest_run_id}/nlp_model_producc"
    return mlflow.sklearn.load_model(model_uri), f"mlflow:{model_uri}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global production_model, startup_error, model_source
    try:
        production_model, model_source = load_production_model()
        startup_error = None
    except Exception as e:
        startup_error = str(e)
        model_source = None
        print(f"[startup] model loading failed: {startup_error}")
    
    yield

app = FastAPI(
    title="AI Sentiment Classifier MVP",
    description="NLP API to classify reviews of technological products.",
    version="1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ReviewRequest(BaseModel):
    text: str

class ReviewResponse(BaseModel):
    sentiment: str
    confidence: float


@app.get("/", include_in_schema=False)
def root():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")

    return FileResponse(index_file)


@app.get("/styles.css", include_in_schema=False)
def styles_file():
    css_file = STATIC_DIR / "styles.css"
    if not css_file.exists():
        raise HTTPException(status_code=404, detail="styles.css not found.")

    return FileResponse(css_file)


@app.get("/app.js", include_in_schema=False)
def js_file():
    js_file_path = STATIC_DIR / "app.js"
    if not js_file_path.exists():
        raise HTTPException(status_code=404, detail="app.js not found.")

    return FileResponse(js_file_path)


@app.get("/health")
def health_check():
    return {
        "status": "ok" if production_model is not None else "degraded",
        "model_loaded": production_model is not None,
        "model_source": model_source,
        "error": startup_error,
    }

@app.post("/predict", response_model=ReviewResponse)
def predict_sentiment(request: ReviewRequest):
    if not production_model:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Model is not available.",
                "startup_error": startup_error,
            }
        )
    
    pred = production_model.predict([request.text])[0]
    prob = production_model.predict_proba([request.text])[0].max()

    status = "Positive" if pred == 1 else "Negative"

    return ReviewResponse(sentiment=status, confidence=float(prob))


