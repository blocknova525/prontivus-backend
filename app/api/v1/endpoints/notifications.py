"""
Notifications API Endpoints
Real-time notifications for appointments, patients, system events, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum

from ....database.database import get_db
from ..dependencies.auth import get_current_user_flexible
from ....services.change_tracking_service import get_change_tracker

router = APIRouter()

class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class NotificationCategory(str, Enum):
    APPOINTMENT = "appointment"
    PATIENT = "patient"
    SYSTEM = "system"
    FINANCIAL = "financial"
    LICENSE = "license"

# Mock notifications data
MOCK_NOTIFICATIONS = [
    {
        "id": "1",
        "type": NotificationType.WARNING,
        "title": "Licença próxima do vencimento",
        "message": "Expira em 7 dias",
        "timestamp": datetime.now() - timedelta(hours=2),
        "read": False,
        "category": NotificationCategory.LICENSE,
        "action_url": "/admin/licencas",
        "action_label": "Ver Licenças"
    },
    {
        "id": "2", 
        "type": NotificationType.INFO,
        "title": "Novo paciente cadastrado",
        "message": "Maria Silva - 14:30",
        "timestamp": datetime.now() - timedelta(hours=4),
        "read": False,
        "category": NotificationCategory.PATIENT,
        "action_url": "/secretaria/pacientes",
        "action_label": "Ver Pacientes"
    },
    {
        "id": "3",
        "type": NotificationType.SUCCESS,
        "title": "Backup realizado",
        "message": "Hoje às 03:00",
        "timestamp": datetime.now() - timedelta(hours=6),
        "read": True,
        "category": NotificationCategory.SYSTEM,
        "action_url": "/admin",
        "action_label": "Ver Sistema"
    },
    {
        "id": "4",
        "type": NotificationType.INFO,
        "title": "Consulta agendada",
        "message": "João Santos com Dr. Pedro Lima - Amanhã 09:00",
        "timestamp": datetime.now() - timedelta(hours=8),
        "read": False,
        "category": NotificationCategory.APPOINTMENT,
        "action_url": "/agenda",
        "action_label": "Ver Agenda"
    },
    {
        "id": "5",
        "type": NotificationType.WARNING,
        "title": "Estoque baixo",
        "message": "Paracetamol 750mg - Apenas 5 unidades",
        "timestamp": datetime.now() - timedelta(hours=12),
        "read": False,
        "category": NotificationCategory.SYSTEM,
        "action_url": "/estoque",
        "action_label": "Ver Estoque"
    },
    {
        "id": "6",
        "type": NotificationType.INFO,
        "title": "Consulta confirmada",
        "message": "Sua consulta com Dr. João Silva foi confirmada para 25/09 às 15:00",
        "timestamp": datetime.now() - timedelta(hours=1),
        "read": False,
        "category": NotificationCategory.APPOINTMENT,
        "action_url": "/patient/appointments",
        "action_label": "Ver Agendamentos",
        "user_id": 5
    },
    {
        "id": "7",
        "type": NotificationType.SUCCESS,
        "title": "Receita disponível",
        "message": "Nova receita médica disponível para download",
        "timestamp": datetime.now() - timedelta(hours=3),
        "read": False,
        "category": NotificationCategory.PATIENT,
        "action_url": "/patient/prescriptions",
        "action_label": "Ver Receitas",
        "user_id": 5
    },
    {
        "id": "8",
        "type": NotificationType.INFO,
        "title": "Lembrete de consulta",
        "message": "Você tem uma consulta agendada para amanhã às 10:30",
        "timestamp": datetime.now() - timedelta(hours=6),
        "read": True,
        "category": NotificationCategory.APPOINTMENT,
        "action_url": "/patient/appointments",
        "action_label": "Ver Agendamentos",
        "user_id": 5
    }
]

def generate_notifications_from_changes(changes: List[dict]) -> List[dict]:
    """Generate notification objects from database changes"""
    notifications = []
    
    for change in changes:
        entity_type = change["entity_type"]
        change_type = change["change_type"]
        entity_id = change["entity_id"]
        timestamp = change["timestamp"]
        
        if entity_type == "patient":
            if change_type == "updated":
                notification = {
                    "id": f"change_{entity_id}_{change_type}_{timestamp.timestamp()}",
                    "type": NotificationType.INFO,
                    "title": "Paciente atualizado",
                    "message": f"Os dados do paciente ID {entity_id} foram atualizados",
                    "timestamp": timestamp,
                    "read": False,
                    "category": NotificationCategory.PATIENT,
                    "action_url": f"/admin/patients/{entity_id}",
                    "action_label": "Ver Paciente",
                    "change_id": f"patient_{entity_id}_{change_type}"
                }
                notifications.append(notification)
            
            elif change_type == "deleted":
                notification = {
                    "id": f"change_{entity_id}_{change_type}_{timestamp.timestamp()}",
                    "type": NotificationType.WARNING,
                    "title": "Paciente excluído",
                    "message": f"O paciente ID {entity_id} foi removido do sistema",
                    "timestamp": timestamp,
                    "read": False,
                    "category": NotificationCategory.PATIENT,
                    "action_url": "/admin/patients",
                    "action_label": "Ver Pacientes",
                    "change_id": f"patient_{entity_id}_{change_type}"
                }
                notifications.append(notification)
        
        elif entity_type == "appointment":
            if change_type == "created":
                notification = {
                    "id": f"change_{entity_id}_{change_type}_{timestamp.timestamp()}",
                    "type": NotificationType.SUCCESS,
                    "title": "Nova consulta agendada",
                    "message": f"Nova consulta ID {entity_id} foi agendada",
                    "timestamp": timestamp,
                    "read": False,
                    "category": NotificationCategory.APPOINTMENT,
                    "action_url": f"/appointments/{entity_id}",
                    "action_label": "Ver Consulta",
                    "change_id": f"appointment_{entity_id}_{change_type}"
                }
                notifications.append(notification)
            
            elif change_type == "updated":
                notification = {
                    "id": f"change_{entity_id}_{change_type}_{timestamp.timestamp()}",
                    "type": NotificationType.INFO,
                    "title": "Consulta atualizada",
                    "message": f"A consulta ID {entity_id} foi modificada",
                    "timestamp": timestamp,
                    "read": False,
                    "category": NotificationCategory.APPOINTMENT,
                    "action_url": f"/appointments/{entity_id}",
                    "action_label": "Ver Consulta",
                    "change_id": f"appointment_{entity_id}_{change_type}"
                }
                notifications.append(notification)
    
    return notifications

@router.get("/", response_model=List[dict])
async def list_notifications(
    limit: Optional[int] = Query(10, ge=1, le=100),
    unread_only: Optional[bool] = Query(False),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Get user notifications - only shows notifications for newly updated data"""
    import os
    
    # Get notifications from database changes
    change_tracker = get_change_tracker(db)
    recent_changes = change_tracker.get_unnotified_changes()
    change_notifications = generate_notifications_from_changes(recent_changes)
    
    # Combine with some static notifications (system alerts, etc.)
    static_notifications = [
        {
            "id": "static_1",
            "type": NotificationType.WARNING,
            "title": "Licença próxima do vencimento",
            "message": "Expira em 7 dias",
            "timestamp": datetime.now() - timedelta(hours=2),
            "read": False,
            "category": NotificationCategory.LICENSE,
            "action_url": "/admin/licencas",
            "action_label": "Ver Licenças"
        }
    ]
    
    # Combine all notifications
    notifications = change_notifications + static_notifications
    
    # For patients, only show their own notifications
    if current_user["type"] == "patient":
        notifications = [n for n in notifications if n.get("user_id") == current_user["id"]]
    # For staff, show all notifications (no user_id filter)
    
    # Filter by unread only if requested
    if unread_only:
        notifications = [n for n in notifications if not n["read"]]
    
    # Filter by category if provided
    if category:
        notifications = [n for n in notifications if n["category"].value == category]
    
    # Sort by timestamp (newest first)
    notifications.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Apply limit
    notifications = notifications[:limit]
    
    return notifications

@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Get unread notifications count"""
    import os
    
    # Count unread change-based notifications
    change_tracker = get_change_tracker(db)
    unnotified_changes = change_tracker.get_unnotified_changes()
    change_count = len(unnotified_changes)
    
    # Count unread static notifications
    static_count = len([n for n in MOCK_NOTIFICATIONS if not n["read"]])
    
    total_unread = change_count + static_count
    
    return {"unread_count": total_unread}

@router.put("/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Mark notification as read"""
    import os
    
    # Handle change-based notifications
    if notification_id.startswith("change_"):
        # Extract change information from notification ID
        parts = notification_id.split("_")
        if len(parts) >= 4:
            entity_id = parts[1]
            change_type = parts[2]
            
            # Mark the corresponding change as notified
            change_tracker = get_change_tracker(db)
            change_key = f"patient_{entity_id}_{change_type}"
            change_tracker.mark_changes_as_notified([change_key])
            
            return {"message": "Change notification marked as read", "notification_id": notification_id}
    
    # Handle static notifications (fallback to mock data)
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # Find and mark mock notification as read
        for notification in MOCK_NOTIFICATIONS:
            if notification["id"] == notification_id:
                notification["read"] = True
                return {"message": "Notification marked as read", "notification_id": notification_id}
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    else:
        # TODO: Implement real database update
        return {"message": "Notification marked as read", "notification_id": notification_id}

@router.put("/mark-all-read", response_model=dict)
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Mark all notifications as read"""
    import os
    
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # Mark all mock notifications as read
        for notification in MOCK_NOTIFICATIONS:
            notification["read"] = True
        
        return {"message": "All notifications marked as read"}
    else:
        # TODO: Implement real database update
        return {"message": "All notifications marked as read"}

@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_flexible),
):
    """Delete notification"""
    import os
    
    if os.getenv("USE_DATABASE", "false").lower() == "false":
        # Find and remove mock notification
        for i, notification in enumerate(MOCK_NOTIFICATIONS):
            if notification["id"] == notification_id:
                MOCK_NOTIFICATIONS.pop(i)
                return {"message": "Notification deleted", "notification_id": notification_id}
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    else:
        # TODO: Implement real database deletion
        return {"message": "Notification deleted", "notification_id": notification_id}
