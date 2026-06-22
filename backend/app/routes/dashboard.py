"""
Dashboard routes — aggregated hotel statistics and recent bookings.
"""
from fastapi import APIRouter
from app.schemas.booking import BookingDashboardResponse
from app.services import dashboard_service
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardStats(BaseModel):
    """Response model for the dashboard statistics endpoint."""
    total_rooms: int
    occupancy: float
    bookings_this_month: int
    satisfaction: float
    recent_bookings: List[BookingDashboardResponse]


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """
    Get aggregated dashboard statistics:
    - Total room count
    - Occupancy percentage
    - Total booking count this month
    - Guest satisfaction score
    - Last 10 bookings formatted for the dashboard table
    """
    stats = await dashboard_service.get_dashboard_stats()
    return DashboardStats(**stats)
