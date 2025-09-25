"""
Patient Calling Service for Prontivus
Handles patient calling functionality with reception display and notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from enum import Enum

from app.database.database import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)

class CallStatus(Enum):
    """Patient call status"""
    PENDING = "pending"
    CALLED = "called"
    RESPONDED = "responded"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PatientCallService:
    """Service for managing patient calls"""
    
    def __init__(self):
        self.active_calls: Dict[int, Dict[str, Any]] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.reception_display_data: List[Dict[str, Any]] = []
    
    async def call_patient(self, appointment_id: int, doctor_id: int, db: Session) -> Dict[str, Any]:
        """Call a patient for their appointment"""
        try:
            # Get appointment details
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appointment:
                raise ValueError("Appointment not found")
            
            # Get patient details
            patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
            if not patient:
                raise ValueError("Patient not found")
            
            # Get doctor details
            doctor = db.query(User).filter(User.id == doctor_id).first()
            if not doctor:
                raise ValueError("Doctor not found")
            
            # Create call record
            call_data = {
                "call_id": len(self.active_calls) + 1,
                "appointment_id": appointment_id,
                "patient_id": patient.id,
                "patient_name": patient.full_name,
                "patient_phone": patient.phone,
                "doctor_id": doctor_id,
                "doctor_name": doctor.full_name,
                "appointment_time": appointment.appointment_time,
                "status": CallStatus.CALLED.value,
                "called_at": datetime.utcnow(),
                "room_number": appointment.room_number or "Sala 1",
                "specialty": appointment.specialty or "Consulta Geral"
            }
            
            # Add to active calls
            self.active_calls[appointment_id] = call_data
            
            # Add to call history
            self.call_history.append(call_data.copy())
            
            # Update reception display
            await self._update_reception_display()
            
            # Send notification to patient (if phone number available)
            if patient.phone:
                await self._send_patient_notification(call_data)
            
            logger.info(f"Patient {patient.full_name} called by Dr. {doctor.full_name}")
            
            return {
                "success": True,
                "message": f"Paciente {patient.full_name} foi chamado(a)",
                "call_data": call_data
            }
            
        except Exception as e:
            logger.error(f"Error calling patient: {e}")
            return {
                "success": False,
                "message": f"Erro ao chamar paciente: {str(e)}"
            }
    
    async def respond_to_call(self, appointment_id: int, response: str) -> Dict[str, Any]:
        """Patient responds to call"""
        try:
            if appointment_id not in self.active_calls:
                return {
                    "success": False,
                    "message": "Chamada não encontrada"
                }
            
            call_data = self.active_calls[appointment_id]
            call_data["status"] = CallStatus.RESPONDED.value
            call_data["response"] = response
            call_data["responded_at"] = datetime.utcnow()
            
            # Update call history
            for call in self.call_history:
                if call["appointment_id"] == appointment_id:
                    call.update(call_data)
                    break
            
            # Update reception display
            await self._update_reception_display()
            
            logger.info(f"Patient {call_data['patient_name']} responded: {response}")
            
            return {
                "success": True,
                "message": f"Resposta registrada: {response}",
                "call_data": call_data
            }
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {
                "success": False,
                "message": f"Erro ao processar resposta: {str(e)}"
            }
    
    async def complete_call(self, appointment_id: int) -> Dict[str, Any]:
        """Mark call as completed"""
        try:
            if appointment_id not in self.active_calls:
                return {
                    "success": False,
                    "message": "Chamada não encontrada"
                }
            
            call_data = self.active_calls[appointment_id]
            call_data["status"] = CallStatus.COMPLETED.value
            call_data["completed_at"] = datetime.utcnow()
            
            # Remove from active calls
            del self.active_calls[appointment_id]
            
            # Update call history
            for call in self.call_history:
                if call["appointment_id"] == appointment_id:
                    call.update(call_data)
                    break
            
            # Update reception display
            await self._update_reception_display()
            
            logger.info(f"Call for {call_data['patient_name']} completed")
            
            return {
                "success": True,
                "message": "Chamada finalizada",
                "call_data": call_data
            }
            
        except Exception as e:
            logger.error(f"Error completing call: {e}")
            return {
                "success": False,
                "message": f"Erro ao finalizar chamada: {str(e)}"
            }
    
    async def cancel_call(self, appointment_id: int, reason: str = "Cancelado") -> Dict[str, Any]:
        """Cancel a patient call"""
        try:
            if appointment_id not in self.active_calls:
                return {
                    "success": False,
                    "message": "Chamada não encontrada"
                }
            
            call_data = self.active_calls[appointment_id]
            call_data["status"] = CallStatus.CANCELLED.value
            call_data["cancelled_at"] = datetime.utcnow()
            call_data["cancel_reason"] = reason
            
            # Remove from active calls
            del self.active_calls[appointment_id]
            
            # Update call history
            for call in self.call_history:
                if call["appointment_id"] == appointment_id:
                    call.update(call_data)
                    break
            
            # Update reception display
            await self._update_reception_display()
            
            logger.info(f"Call for {call_data['patient_name']} cancelled: {reason}")
            
            return {
                "success": True,
                "message": f"Chamada cancelada: {reason}",
                "call_data": call_data
            }
            
        except Exception as e:
            logger.error(f"Error cancelling call: {e}")
            return {
                "success": False,
                "message": f"Erro ao cancelar chamada: {str(e)}"
            }
    
    async def _update_reception_display(self):
        """Update reception display data"""
        self.reception_display_data = []
        
        for call_data in self.active_calls.values():
            display_item = {
                "patient_name": call_data["patient_name"],
                "doctor_name": call_data["doctor_name"],
                "room_number": call_data["room_number"],
                "specialty": call_data["specialty"],
                "status": call_data["status"],
                "called_at": call_data["called_at"],
                "waiting_time": (datetime.utcnow() - call_data["called_at"]).total_seconds() / 60
            }
            self.reception_display_data.append(display_item)
        
        # Sort by waiting time (longest first)
        self.reception_display_data.sort(key=lambda x: x["waiting_time"], reverse=True)
    
    async def _send_patient_notification(self, call_data: Dict[str, Any]):
        """Send notification to patient (SMS/WhatsApp)"""
        try:
            # This would integrate with SMS/WhatsApp service
            # For now, just log the notification
            message = f"""
            🏥 Prontivus - Cuidado inteligente
            
            Olá {call_data['patient_name']},
            
            Você foi chamado(a) pelo Dr(a). {call_data['doctor_name']} 
            na {call_data['room_number']}.
            
            Por favor, dirija-se à sala indicada.
            
            Horário: {call_data['appointment_time']}
            Especialidade: {call_data['specialty']}
            """
            
            logger.info(f"Sending notification to {call_data['patient_phone']}: {message}")
            
            # TODO: Integrate with actual SMS/WhatsApp service
            # await sms_service.send_sms(call_data['patient_phone'], message)
            
        except Exception as e:
            logger.error(f"Error sending patient notification: {e}")
    
    def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get all active calls"""
        return list(self.active_calls.values())
    
    def get_call_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get call history"""
        return self.call_history[-limit:]
    
    def get_reception_display(self) -> List[Dict[str, Any]]:
        """Get reception display data"""
        return self.reception_display_data
    
    def get_patient_waiting_list(self, db: Session) -> List[Dict[str, Any]]:
        """Get patients waiting for their appointments"""
        try:
            # Get today's appointments that haven't been called yet
            today = datetime.utcnow().date()
            current_time = datetime.utcnow().time()
            
            appointments = db.query(Appointment).filter(
                and_(
                    Appointment.appointment_date == today,
                    Appointment.appointment_time <= current_time,
                    Appointment.status.in_(['scheduled', 'confirmed'])
                )
            ).all()
            
            waiting_list = []
            for appointment in appointments:
                # Check if already called
                if appointment.id in self.active_calls:
                    continue
                
                patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
                doctor = db.query(User).filter(User.id == appointment.doctor_id).first()
                
                if patient and doctor:
                    waiting_item = {
                        "appointment_id": appointment.id,
                        "patient_name": patient.full_name,
                        "patient_phone": patient.phone,
                        "doctor_name": doctor.full_name,
                        "appointment_time": appointment.appointment_time,
                        "room_number": appointment.room_number or "Sala 1",
                        "specialty": appointment.specialty or "Consulta Geral",
                        "waiting_time": (datetime.combine(today, current_time) - 
                                       datetime.combine(today, appointment.appointment_time)).total_seconds() / 60
                    }
                    waiting_list.append(waiting_item)
            
            # Sort by appointment time
            waiting_list.sort(key=lambda x: x["appointment_time"])
            
            return waiting_list
            
        except Exception as e:
            logger.error(f"Error getting waiting list: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get call statistics"""
        total_calls = len(self.call_history)
        active_calls = len(self.active_calls)
        
        status_counts = {}
        for call in self.call_history:
            status = call.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_calls": total_calls,
            "active_calls": active_calls,
            "status_counts": status_counts,
            "average_waiting_time": self._calculate_average_waiting_time()
        }
    
    def _calculate_average_waiting_time(self) -> float:
        """Calculate average waiting time for completed calls"""
        completed_calls = [call for call in self.call_history if call.get("status") == "completed"]
        
        if not completed_calls:
            return 0.0
        
        total_waiting_time = 0
        for call in completed_calls:
            if "called_at" in call and "completed_at" in call:
                waiting_time = (call["completed_at"] - call["called_at"]).total_seconds() / 60
                total_waiting_time += waiting_time
        
        return total_waiting_time / len(completed_calls)

# Global patient call service instance
patient_call_service = PatientCallService()
