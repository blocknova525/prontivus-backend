"""
Change Tracking Service
Tracks database changes and generates notifications for new/updated data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

class ChangeTrackingService:
    def __init__(self, db: Session):
        self.db = db
        self.change_log = {}  # In-memory change log (in production, use Redis or database)
    
    def track_patient_change(self, patient_id: int, change_type: str, old_data: Dict = None, new_data: Dict = None):
        """Track patient data changes"""
        change_key = f"patient_{patient_id}_{change_type}"
        
        change_info = {
            "entity_type": "patient",
            "entity_id": patient_id,
            "change_type": change_type,  # 'created', 'updated', 'deleted'
            "timestamp": datetime.now(),
            "old_data": old_data,
            "new_data": new_data,
            "notified": False
        }
        
        self.change_log[change_key] = change_info
        return change_info
    
    def track_appointment_change(self, appointment_id: int, change_type: str, old_data: Dict = None, new_data: Dict = None):
        """Track appointment data changes"""
        change_key = f"appointment_{appointment_id}_{change_type}"
        
        change_info = {
            "entity_type": "appointment",
            "entity_id": appointment_id,
            "change_type": change_type,
            "timestamp": datetime.now(),
            "old_data": old_data,
            "new_data": new_data,
            "notified": False
        }
        
        self.change_log[change_key] = change_info
        return change_info
    
    def get_recent_changes(self, entity_type: str = None, minutes: int = 5) -> List[Dict]:
        """Get recent changes within specified time window"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_changes = []
        for change_key, change_info in self.change_log.items():
            if change_info["timestamp"] >= cutoff_time:
                if entity_type is None or change_info["entity_type"] == entity_type:
                    recent_changes.append(change_info)
        
        # Sort by timestamp (newest first)
        recent_changes.sort(key=lambda x: x["timestamp"], reverse=True)
        return recent_changes
    
    def get_unnotified_changes(self, entity_type: str = None) -> List[Dict]:
        """Get changes that haven't been notified yet"""
        unnotified_changes = []
        for change_key, change_info in self.change_log.items():
            if not change_info["notified"]:
                if entity_type is None or change_info["entity_type"] == entity_type:
                    unnotified_changes.append(change_info)
        
        # Sort by timestamp (newest first)
        unnotified_changes.sort(key=lambda x: x["timestamp"], reverse=True)
        return unnotified_changes
    
    def mark_changes_as_notified(self, change_keys: List[str]):
        """Mark specific changes as notified"""
        for change_key in change_keys:
            if change_key in self.change_log:
                self.change_log[change_key]["notified"] = True
    
    def get_patient_recent_activity(self, patient_id: int, minutes: int = 10) -> List[Dict]:
        """Get recent activity for a specific patient"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        patient_changes = []
        for change_key, change_info in self.change_log.items():
            if (change_info["entity_type"] == "patient" and 
                change_info["entity_id"] == patient_id and 
                change_info["timestamp"] >= cutoff_time):
                patient_changes.append(change_info)
        
        return sorted(patient_changes, key=lambda x: x["timestamp"], reverse=True)
    
    def cleanup_old_changes(self, hours: int = 24):
        """Clean up changes older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        keys_to_remove = []
        for change_key, change_info in self.change_log.items():
            if change_info["timestamp"] < cutoff_time:
                keys_to_remove.append(change_key)
        
        for key in keys_to_remove:
            del self.change_log[key]
    
    def get_change_statistics(self) -> Dict:
        """Get statistics about tracked changes"""
        total_changes = len(self.change_log)
        unnotified_count = len([c for c in self.change_log.values() if not c["notified"]])
        
        entity_counts = {}
        for change_info in self.change_log.values():
            entity_type = change_info["entity_type"]
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        return {
            "total_changes": total_changes,
            "unnotified_count": unnotified_count,
            "entity_counts": entity_counts,
            "oldest_change": min([c["timestamp"] for c in self.change_log.values()]) if self.change_log else None,
            "newest_change": max([c["timestamp"] for c in self.change_log.values()]) if self.change_log else None
        }

# Global change tracking service instance
change_tracker = ChangeTrackingService(None)

def get_change_tracker(db: Session) -> ChangeTrackingService:
    """Get change tracking service instance"""
    global change_tracker
    if change_tracker.db is None:
        change_tracker.db = db
    return change_tracker
