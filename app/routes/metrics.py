"""Routes for serving performance metrics."""

from datetime import timedelta
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.metrics import get_metrics_aggregator

router = APIRouter()

# Set up templates
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/metrics", response_class=HTMLResponse)
async def view_metrics(request: Request, hours: float = 1.0):
    """
    View performance metrics dashboard.
    
    Args:
        request: FastAPI request object
        hours: Time window in hours to display metrics for
    """
    metrics = get_metrics_aggregator().get_metrics(time_window=timedelta(hours=hours))
    return templates.TemplateResponse(
        "metrics.html",
        {"request": request, "metrics": metrics}
    )

@router.get("/metrics/json")
async def get_metrics_json(hours: float = 1.0):
    """
    Get performance metrics as JSON.
    
    Args:
        hours: Time window in hours to get metrics for
    """
    return JSONResponse(
        get_metrics_aggregator().get_metrics(time_window=timedelta(hours=hours))
    ) 