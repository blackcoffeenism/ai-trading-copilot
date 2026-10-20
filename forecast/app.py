import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np

# Try importing Chronos pipeline
try:
    import torch
    from chronos import ChronosPipeline
    CHRONOS_AVAILABLE = True
except ImportError:
    CHRONOS_AVAILABLE = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield

app = FastAPI(title="Chronos Forecasting Engine", lifespan=lifespan)

class ForecastRequest(BaseModel):
    history: List[float]
    prediction_length: int = 12

class ForecastResponse(BaseModel):
    median: List[float]
    upper_90: List[float]
    lower_90: List[float]
    method: str

# Global variable to hold loaded Chronos model
pipeline = None

def load_model():
    global pipeline
    if CHRONOS_AVAILABLE:
        try:
            print("Loading Amazon Chronos-T5-mini model...")
            pipeline = ChronosPipeline.from_pretrained(  # pyright: ignore[reportPossiblyUnboundVariable]
                "amazon/chronos-t5-mini",
                device_map="cpu",  # Fallback to CPU for safety in dev containers
                torch_dtype=torch.float32  # pyright: ignore[reportPossiblyUnboundVariable]
            )
            print("Chronos-T5 model loaded successfully.")
        except Exception as e:
            print(f"Failed to load Chronos model: {str(e)}. Using fallback forecaster.")
            pipeline = None
    else:
        print("Chronos package not installed. Running in math-fallback mode.")

@app.post("/forecast", response_model=ForecastResponse)
def generate_forecast(req: ForecastRequest):
    if len(req.history) < 5:
        raise HTTPException(status_code=400, detail="Historical price series too short. Minimum length is 5.")
        
    # If Chronos is loaded, run inference
    if pipeline is not None and CHRONOS_AVAILABLE:
        try:
            import torch
            context = torch.tensor(req.history)
            forecast = pipeline.predict(context, req.prediction_length)
            
            # Extract quantiles
            # forecast shape: [num_samples, prediction_length]
            low, median, high = np.percentile(forecast[0].numpy(), [10, 50, 90], axis=0)
            
            return ForecastResponse(
                median=median.tolist(),
                upper_90=high.tolist(),
                lower_90=low.tolist(),
                method="Chronos-T5"
            )
        except Exception as e:
            print(f"Chronos inference failed: {str(e)}. Falling back to statistical engine...")
            
    # Fallback: Auto-Regressive Volatility Drift Engine
    history_arr = np.array(req.history)
    log_returns = np.diff(np.log(history_arr))
    drift = np.mean(log_returns)
    volatility = np.std(log_returns)
    
    last_price = req.history[-1]
    median = []
    upper = []
    lower = []
    
    # Simulate future paths using Geometric Brownian Motion
    for step in range(1, req.prediction_length + 1):
        # Median path (no noise)
        pred_median = last_price * np.exp(drift * step)
        median.append(pred_median)
        
        # 90% confidence bands based on expanding variance over steps
        variance = (volatility ** 2) * step
        std_err = np.sqrt(variance)
        
        upper.append(pred_median * np.exp(1.645 * std_err))
        lower.append(pred_median * np.exp(-1.645 * std_err))
        
    return ForecastResponse(
        median=median,
        upper_90=upper,
        lower_90=lower,
        method="Geometric Brownian Motion (Fallback)"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
