"""
Booking routes — CRUD operations and status management.
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks, UploadFile, File
import os
import shutil
import uuid
from app.schemas.booking import BookingCreate, BookingUpdateStatus, BookingResponse
from app.auth.dependencies import require_roles
from app.services import booking_service
from app.utils.email import send_booking_confirmation
from typing import List, Optional

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", response_model=List[BookingResponse])
async def get_bookings(
    current_user=Depends(require_roles(["admin", "staff"])),
    status_filter: Optional[str] = Query(None, description="Filter by booking status"),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
):
    """
    Get all bookings. Optionally filter by status or room_id.
    Requires admin or staff role.
    """
    return await booking_service.get_all_bookings(
        status_filter=status_filter,
        room_id=room_id,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    current_user=Depends(require_roles(["admin", "staff"])),
):
    """Get a single booking by BK-XXXX id or MongoDB _id. Requires auth."""
    return await booking_service.get_booking_by_id(booking_id)


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(booking_data: BookingCreate, background_tasks: BackgroundTasks):
    """
    Create a new booking (public — no auth required).
    If room_id is a category name (Standard/Deluxe/Suite), finds first available room.
    """
    booking = await booking_service.create_booking(booking_data.model_dump())
    
    # Schedule the confirmation email to be sent in the background
    background_tasks.add_task(send_booking_confirmation, booking)
    
    return booking


@router.post("/upload-aadhaar", status_code=201)
async def upload_aadhaar(file: UploadFile = File(...)):
    """Upload Aadhaar document (PDF/JPG/JPEG/PNG) and return file path."""
    ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: PDF, JPG, JPEG, PNG"
        )

    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)

    # Generate unique filename preserving extension
    filename = f"aadhaar_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filepath": filepath.replace("\\", "/")}


@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: str,
    status_data: BookingUpdateStatus,
    current_user=Depends(require_roles(["admin", "staff"])),
):
    """
    Update booking status. Valid values: pending, confirmed, checkedin, checkout.
    On checkout → room becomes 'avail'. On confirmed/checkedin → room stays 'booked'.
    Requires admin or staff role.
    """
    return await booking_service.update_booking_status(
        booking_id, status_data.status
    )


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: str,
    current_user=Depends(require_roles(["admin", "staff"])),
):
    """
    Cancel and delete a booking. Frees the room back to 'avail'.
    Requires admin or staff role.
    """
    return await booking_service.cancel_booking(booking_id)
