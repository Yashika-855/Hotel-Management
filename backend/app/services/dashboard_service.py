"""
Dashboard service — business logic for aggregating dashboard statistics.
"""
from typing import List
from datetime import datetime
from app.database import get_booking_collection, get_room_collection
from app.schemas.booking import BookingDashboardResponse
import logging

logger = logging.getLogger("LuxeStayAPI")


def _format_date_str(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' → 'Jun 12' for dashboard display."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d")
    except Exception:
        return date_str


def _format_amount(amount: float) -> str:
    """Format amount as '$1,350'."""
    return f"${amount:,.0f}"


async def get_dashboard_stats() -> dict:
    """
    Aggregate dashboard statistics:
    - total_rooms: total count of rooms
    - occupancy: percentage of booked rooms
    - bookings_this_month: total bookings created this month
    - satisfaction: fixed 4.91 rating matching frontend
    - recent_bookings: last 10 bookings formatted for dashboard table
    """
    bookings_col = get_booking_collection()
    rooms_col = get_room_collection()

    total_rooms = await rooms_col.count_documents({})
    occupied_rooms = await rooms_col.count_documents({"status": "booked"})
    occupancy = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0.0

    status_to_class = {
        "pending": "s-pending",
        "confirmed": "s-confirmed",
        "checkedin": "s-checkedin",
        "checkout": "s-checkout",
    }

    cursor = bookings_col.find()
    
    now = datetime.now()
    bookings_this_month = 0
    recent_bookings: List[BookingDashboardResponse] = []

    async for b in cursor:
        created_at = b.get("created_at")
        if created_at and isinstance(created_at, datetime):
            if created_at.year == now.year and created_at.month == now.month:
                bookings_this_month += 1

        room_display = f"{b.get('room_id')} — {b.get('room_name')}"
        formatted_booking = BookingDashboardResponse(
            id=b.get("booking_id"),
            guest=b.get("guest_name"),
            room=room_display,
            checkin=_format_date_str(b.get("checkin")),
            checkout=_format_date_str(b.get("checkout")),
            amount=_format_amount(b.get("amount", 0.0)),
            status=b.get("status", "pending"),
            sc=status_to_class.get(b.get("status", "pending"), "s-pending"),
        )
        recent_bookings.append(formatted_booking)

    # Reverse to show most recent first
    recent_bookings.reverse()

    return {
        "total_rooms": total_rooms,
        "occupancy": round(occupancy, 1),
        "bookings_this_month": bookings_this_month,
        "satisfaction": 4.91,
        "recent_bookings": recent_bookings[:10],
    }
