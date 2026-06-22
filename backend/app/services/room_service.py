"""
Room service — business logic for room CRUD operations and availability search.
"""
from datetime import datetime, timezone
from typing import List, Optional
from app.database import get_room_collection, get_booking_collection
from app.core.exceptions import NotFoundException, BadRequestException
import logging

logger = logging.getLogger("LuxeStayAPI")


def _serialize_room(doc: dict) -> dict:
    """Convert MongoDB doc to a JSON-safe dict for RoomResponse."""
    doc = dict(doc)
    doc.pop("_id", None)
    if "id" not in doc or doc["id"] is None:
        doc["id"] = ""
    if "feats" not in doc:
        doc["feats"] = []
    if "fcls" not in doc:
        doc["fcls"] = []
    if "cls" not in doc:
        doc["cls"] = "r1"
    return doc


async def get_all_rooms(status_filter: Optional[str] = None) -> List[dict]:
    """
    Retrieve all rooms with optional status/type filter.
    status_filter: 'all' | 'avail' | 'booked' | 'maint' | 'suite'
    """
    rooms_col = get_room_collection()
    query: dict = {}

    if status_filter and status_filter != "all":
        if status_filter == "suite":
            query["type"] = {"$regex": "Suite", "$options": "i"}
        else:
            query["status"] = status_filter

    cursor = rooms_col.find(query)
    rooms = []
    async for doc in cursor:
        rooms.append(_serialize_room(doc))
    return rooms


async def get_room_by_id(room_id: str) -> dict:
    """Get a single room by its room number/ID. Raises NotFoundException."""
    rooms_col = get_room_collection()
    doc = await rooms_col.find_one({"id": room_id})
    if not doc:
        raise NotFoundException(f"Room {room_id} not found")
    return _serialize_room(doc)


async def search_available_rooms(
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    room_type: Optional[str] = None,
) -> List[dict]:
    """
    Search available rooms by date range and type.
    Excludes rooms that have overlapping active bookings.
    """
    rooms_col = get_room_collection()
    bookings_col = get_booking_collection()

    # Build base query — only available rooms
    query: dict = {"status": "avail"}

    if room_type and room_type.lower() not in ("all", ""):
        query["type"] = {"$regex": room_type, "$options": "i"}

    cursor = rooms_col.find(query)
    candidate_rooms = []
    async for doc in cursor:
        candidate_rooms.append(_serialize_room(doc))

    # If dates provided, exclude rooms booked within that range
    if checkin and checkout:
        from datetime import datetime as dt
        try:
            ci = dt.strptime(checkin, "%Y-%m-%d")
            co = dt.strptime(checkout, "%Y-%m-%d")
            if ci >= co:
                raise BadRequestException("Check-out must be after check-in")
        except ValueError:
            raise BadRequestException("Dates must be in YYYY-MM-DD format")

        # Find room_ids that have overlapping active bookings in this range
        booked_room_ids = set()
        booking_cursor = bookings_col.find({
            "status": {"$in": ["confirmed", "checkedin", "pending"]},
            "$or": [
                {"checkin": {"$lt": checkout}, "checkout": {"$gt": checkin}},
            ],
        })
        async for b in booking_cursor:
            booked_room_ids.add(b.get("room_id"))

        candidate_rooms = [r for r in candidate_rooms if r.get("id") not in booked_room_ids]

    return candidate_rooms


async def create_room(room_data: dict) -> dict:
    """
    Create a new room. Raises BadRequestException if room ID already exists.
    """
    rooms_col = get_room_collection()

    existing = await rooms_col.find_one({"id": room_data["id"]})
    if existing:
        raise BadRequestException(f"Room with ID {room_data['id']} already exists")

    room_data["created_at"] = datetime.now(timezone.utc)
    await rooms_col.insert_one(room_data)
    logger.info(f"Room created: {room_data['id']}")
    return _serialize_room(room_data)


async def update_room(room_id: str, update_data: dict) -> dict:
    """Update a room's properties. Raises NotFoundException."""
    rooms_col = get_room_collection()

    existing = await rooms_col.find_one({"id": room_id})
    if not existing:
        raise NotFoundException(f"Room {room_id} not found")

    filtered = {k: v for k, v in update_data.items() if v is not None}
    filtered["updated_at"] = datetime.now(timezone.utc)

    if filtered:
        await rooms_col.update_one({"id": room_id}, {"$set": filtered})

    updated = await rooms_col.find_one({"id": room_id})
    return _serialize_room(updated)


async def update_room_status(room_id: str, new_status: str) -> dict:
    """
    Update only a room's status field.
    Valid values: avail, booked, maint.
    """
    if new_status not in ["avail", "booked", "maint"]:
        raise BadRequestException("Status must be one of: avail, booked, maint")

    rooms_col = get_room_collection()
    existing = await rooms_col.find_one({"id": room_id})
    if not existing:
        raise NotFoundException(f"Room {room_id} not found")

    await rooms_col.update_one({"id": room_id}, {"$set": {"status": new_status}})
    updated = await rooms_col.find_one({"id": room_id})
    return _serialize_room(updated)


async def delete_room(room_id: str) -> dict:
    """Delete a room by room ID. Raises NotFoundException."""
    rooms_col = get_room_collection()

    existing = await rooms_col.find_one({"id": room_id})
    if not existing:
        raise NotFoundException(f"Room {room_id} not found")

    await rooms_col.delete_one({"id": room_id})
    logger.info(f"Room deleted: {room_id}")
    return {"message": f"Room {room_id} deleted successfully"}
