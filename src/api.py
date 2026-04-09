from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mlflow.sklearn
import mlflow

production_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global production_model
    try:
        experiment = mlflow.get_experiment_by_name("Sentiment_Classifier_MVP")
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="attributes.status = 'FINISHED'",
            order_by=["start_time DESC"],
            max_results=1
        )
        if runs.empty:
            raise Exception("No model trained yet")
        
        latest_run_id = runs.iloc[0].run_id
        model_uri = f"runs:/{latest_run_id}/nlp_model_producc"
        production_model = mlflow.sklearn.load_model(model_uri)

    except Exception as e:
        print(e)
    
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

class ReviewRequest(BaseModel):
    text: str

class ReviewResponse(BaseModel):
    sentiment: str
    confidence: float

@app.post("/predict", response_model=ReviewResponse)
def predict_sentiment(request: ReviewRequest):
    if not production_model:
        raise HTTPException(status_code=500, detail="Model is not available.")
    
    pred = production_model.predict([request.text])[0]
    prob = production_model.predict_proba([request.text])[0].max()

    status = "Positive" if pred == 1 else "Negative"

    return ReviewResponse(sentiment=status, confidence=float(prob))


