"""
Patient Calling API endpoints
Handles patient calling functionality with reception display
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.database.database import get_db
from app.services.patient_call_service import patient_call_service

router = APIRouter()

class CallPatientRequest(BaseModel):
    appointment_id: int
    doctor_id: int

class RespondToCallRequest(BaseModel):
    appointment_id: int
    response: str

class CancelCallRequest(BaseModel):
    appointment_id: int
    reason: str = "Cancelado"

@router.post("/call")
async def call_patient(
    request: CallPatientRequest,
    db: Session = Depends(get_db)
):
    """Call a patient for their appointment"""
    try:
        result = await patient_call_service.call_patient(
            request.appointment_id, 
            request.doctor_id, 
            db
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": result["call_data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling patient: {str(e)}")

@router.post("/respond")
async def respond_to_call(
    request: RespondToCallRequest,
    db: Session = Depends(get_db)
):
    """Patient responds to call"""
    try:
        result = await patient_call_service.respond_to_call(
            request.appointment_id,
            request.response
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": result["call_data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")

@router.post("/complete")
async def complete_call(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """Mark call as completed"""
    try:
        result = await patient_call_service.complete_call(appointment_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": result["call_data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing call: {str(e)}")

@router.post("/cancel")
async def cancel_call(
    request: CancelCallRequest,
    db: Session = Depends(get_db)
):
    """Cancel a patient call"""
    try:
        result = await patient_call_service.cancel_call(
            request.appointment_id,
            request.reason
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": result["call_data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling call: {str(e)}")

@router.get("/active")
async def get_active_calls():
    """Get all active calls"""
    try:
        active_calls = patient_call_service.get_active_calls()
        
        return {
            "status": "success",
            "data": {
                "active_calls": active_calls,
                "count": len(active_calls)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active calls: {str(e)}")

@router.get("/history")
async def get_call_history(limit: int = 50):
    """Get call history"""
    try:
        history = patient_call_service.get_call_history(limit)
        
        return {
            "status": "success",
            "data": {
                "call_history": history,
                "count": len(history)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting call history: {str(e)}")

@router.get("/reception-display")
async def get_reception_display():
    """Get reception display data"""
    try:
        display_data = patient_call_service.get_reception_display()
        
        return {
            "status": "success",
            "data": {
                "display_data": display_data,
                "count": len(display_data)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting reception display: {str(e)}")

@router.get("/waiting-list")
async def get_waiting_list(db: Session = Depends(get_db)):
    """Get patients waiting for their appointments"""
    try:
        waiting_list = patient_call_service.get_patient_waiting_list(db)
        
        return {
            "status": "success",
            "data": {
                "waiting_list": waiting_list,
                "count": len(waiting_list)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting waiting list: {str(e)}")

@router.get("/statistics")
async def get_call_statistics():
    """Get call statistics"""
    try:
        stats = patient_call_service.get_statistics()
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.get("/status/{appointment_id}")
async def get_call_status(appointment_id: int):
    """Get call status for specific appointment"""
    try:
        active_calls = patient_call_service.get_active_calls()
        
        for call in active_calls:
            if call["appointment_id"] == appointment_id:
                return {
                    "status": "success",
                    "data": {
                        "appointment_id": appointment_id,
                        "call_status": call["status"],
                        "called_at": call["called_at"],
                        "waiting_time": call.get("waiting_time", 0)
                    }
                }
        
        # Check if call was completed or cancelled
        history = patient_call_service.get_call_history()
        for call in history:
            if call["appointment_id"] == appointment_id:
                return {
                    "status": "success",
                    "data": {
                        "appointment_id": appointment_id,
                        "call_status": call["status"],
                        "called_at": call.get("called_at"),
                        "completed_at": call.get("completed_at"),
                        "cancelled_at": call.get("cancelled_at")
                    }
                }
        
        return {
            "status": "success",
            "data": {
                "appointment_id": appointment_id,
                "call_status": "not_called"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting call status: {str(e)}")
