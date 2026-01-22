"""
Uploads API routes.
Handle bookmaker screenshot uploads and metadata storage.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import logging

from db import get_db
from models import UploadStub

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("")
async def upload_screenshot(
    file: UploadFile = File(...),
    bookmaker: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    Store bookmaker screenshot metadata.
    
    Note: This is a stub implementation. Actual file storage would use:
    - Cloud storage (S3, GCS, Supabase Storage)
    - Local filesystem with proper security
    - CDN for serving files
    
    For now, we only store metadata about the upload.
    
    Args:
        file: Uploaded file
        bookmaker: Optional bookmaker name
        notes: Optional notes about the upload
    
    Returns:
        Upload confirmation with metadata ID
    """
    try:
        db = get_db()
        
        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        file_size = 0
        
        # Read file to check size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: 10MB"
            )
        
        # In production: Upload to cloud storage
        # storage_url = await upload_to_cloud_storage(contents, file.filename)
        
        # For now: Store metadata only
        upload_entry = {
            "filename": file.filename,
            "upload_date": datetime.utcnow().isoformat(),
            "bookmaker": bookmaker,
            "notes": notes,
            # In production, add:
            # "storage_url": storage_url,
            # "file_size": file_size,
            # "content_type": file.content_type
        }
        
        result = db.table("upload_stubs").insert(upload_entry).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store upload metadata")
        
        upload_record = result.data[0]
        
        logger.info(
            f"Screenshot uploaded: {file.filename} "
            f"(bookmaker: {bookmaker}, size: {file_size} bytes)"
        )
        
        return JSONResponse(
            content={
                "success": True,
                "upload_id": upload_record["id"],
                "filename": file.filename,
                "bookmaker": bookmaker,
                "uploaded_at": upload_record["upload_date"],
                "message": "Screenshot metadata stored successfully"
            },
            status_code=201
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading screenshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
