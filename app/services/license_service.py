"""
License service
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.license import License
from app.schemas.license import LicenseCreate, LicenseUpdate
from app.core.exceptions import NotFoundError, ValidationError

class LicenseService:
    """License service class"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_license(self, license_data: LicenseCreate) -> License:
        """Create a new license"""
        try:
            license = License(**license_data.dict())
            self.db.add(license)
            self.db.commit()
            self.db.refresh(license)
            return license
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create license: {str(e)}")
    
    def get_license(self, license_id: int) -> License:
        """Get a license by ID"""
        license = self.db.query(License).filter(License.id == license_id).first()
        
        if not license:
            raise NotFoundError("License not found")
        
        return license
    
    def get_licenses(self, skip: int = 0, limit: int = 100) -> List[License]:
        """Get all licenses"""
        return self.db.query(License).offset(skip).limit(limit).all()
    
    def list_licenses(self, tenant_id: int = 0) -> List[License]:
        """List licenses (for API compatibility)"""
        if tenant_id > 0:
            return self.db.query(License).filter(License.tenant_id == tenant_id).all()
        return self.db.query(License).all()
    
    def get_license_by_tenant(self, tenant_id: int) -> License:
        """Get license for a specific tenant"""
        license = self.db.query(License).filter(License.tenant_id == tenant_id).first()
        
        if not license:
            raise NotFoundError("License not found for tenant")
        
        return license
    
    def update_license(self, license_id: int, license_data: LicenseUpdate) -> License:
        """Update a license"""
        license = self.get_license(license_id)
        
        try:
            update_data = license_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(license, field, value)
            
            self.db.commit()
            self.db.refresh(license)
            return license
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update license: {str(e)}")
    
    def delete_license(self, license_id: int) -> bool:
        """Delete a license"""
        license = self.get_license(license_id)
        
        try:
            self.db.delete(license)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete license: {str(e)}")
    
    def activate_license(self, license_id: int) -> License:
        """Activate a license"""
        license = self.get_license(license_id)
        license.status = "active"
        
        try:
            self.db.commit()
            self.db.refresh(license)
            return license
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to activate license: {str(e)}")
    
    def suspend_license(self, license_id: int) -> License:
        """Suspend a license"""
        license = self.get_license(license_id)
        license.status = "suspended"
        
        try:
            self.db.commit()
            self.db.refresh(license)
            return license
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to suspend license: {str(e)}")
    
    def check_license_status(self, tenant_id: int) -> dict:
        """Check license status for a tenant"""
        try:
            license = self.get_license_by_tenant(tenant_id)
            return {
                "status": license.status,
                "type": license.type,
                "expires": license.end_date,
                "max_users": license.max_users,
                "max_patients": license.max_patients,
                "features": license.features
            }
        except NotFoundError:
            return {
                "status": "no_license",
                "type": None,
                "expires": None,
                "max_users": 0,
                "max_patients": 0,
                "features": []
            }
