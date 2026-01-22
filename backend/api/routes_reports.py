"""
Reports API routes.
Generate and retrieve scheduled NBA betting reports.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, date, timedelta
import logging

from db import get_db
from reports import NBAReportGenerator
from supabase_client import create_isolated_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/750am")
async def get_750am_report(
    report_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Get or generate the 7:50 AM report.
    
    This report includes:
    - Overnight line movements
    - Early sharp action
    - Injury updates
    - Initial value opportunities
    
    Args:
        report_date: Optional date (default: today)
    
    Returns:
        Report content with analysis and recommendations
    """
    try:
        db = get_db()
        
        # Parse or use today's date
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today()
        
        # Check if report already exists
        existing_result = db.table("reports").select("*").eq(
            "report_type", "750am"
        ).eq(
            "report_date", target_date.isoformat()
        ).execute()
        
        if existing_result.data and len(existing_result.data) > 0:
            report = existing_result.data[0]
            return JSONResponse(
                content={
                    "report": report["content"],
                    "generated_at": report["generated_at"],
                    "cached": True
                },
                status_code=200
            )
        
        # Generate new report
        supabase = create_isolated_supabase_client()
        report_generator = NBAReportGenerator(supabase)
        
        report_content = await report_generator.generate_750am_report()
        
        # Store report
        report_entry = {
            "report_type": "750am",
            "report_date": target_date.isoformat(),
            "content": report_content,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        db.table("reports").insert(report_entry).execute()
        
        return JSONResponse(
            content={
                "report": report_content,
                "generated_at": datetime.utcnow().isoformat(),
                "cached": False
            },
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error generating 7:50 AM report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/800am")
async def get_800am_report(
    report_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Get or generate the 8:00 AM report.
    
    This report includes:
    - Full day's slate analysis
    - Model predictions vs market
    - Value plays with confidence scores
    - Bankroll allocation recommendations
    
    Args:
        report_date: Optional date (default: today)
    
    Returns:
        Report content with betting recommendations
    """
    try:
        db = get_db()
        
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today()
        
        existing_result = db.table("reports").select("*").eq(
            "report_type", "800am"
        ).eq(
            "report_date", target_date.isoformat()
        ).execute()
        
        if existing_result.data and len(existing_result.data) > 0:
            report = existing_result.data[0]
            return JSONResponse(
                content={
                    "report": report["content"],
                    "generated_at": report["generated_at"],
                    "cached": True
                },
                status_code=200
            )
        
        supabase = create_isolated_supabase_client()
        report_generator = NBAReportGenerator(supabase)
        
        report_content = await report_generator.generate_800am_report()
        
        report_entry = {
            "report_type": "800am",
            "report_date": target_date.isoformat(),
            "content": report_content,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        db.table("reports").insert(report_entry).execute()
        
        return JSONResponse(
            content={
                "report": report_content,
                "generated_at": datetime.utcnow().isoformat(),
                "cached": False
            },
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error generating 8:00 AM report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/1100am")
async def get_1100am_report(
    report_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Get or generate the 11:00 AM report.
    
    This report includes:
    - Final line moves before locks
    - Late breaking news impact
    - Last-minute value opportunities
    - Confirmed starting lineups
    
    Args:
        report_date: Optional date (default: today)
    
    Returns:
        Report content with final betting recommendations
    """
    try:
        db = get_db()
        
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today()
        
        existing_result = db.table("reports").select("*").eq(
            "report_type", "1100am"
        ).eq(
            "report_date", target_date.isoformat()
        ).execute()
        
        if existing_result.data and len(existing_result.data) > 0:
            report = existing_result.data[0]
            return JSONResponse(
                content={
                    "report": report["content"],
                    "generated_at": report["generated_at"],
                    "cached": True
                },
                status_code=200
            )
        
        supabase = create_isolated_supabase_client()
        report_generator = NBAReportGenerator(supabase)
        
        report_content = await report_generator.generate_1100am_report()
        
        report_entry = {
            "report_type": "1100am",
            "report_date": target_date.isoformat(),
            "content": report_content,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        db.table("reports").insert(report_entry).execute()
        
        return JSONResponse(
            content={
                "report": report_content,
                "generated_at": datetime.utcnow().isoformat(),
                "cached": False
            },
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error generating 11:00 AM report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
