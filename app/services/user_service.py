"""
User service
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import NotFoundError, ValidationError

class UserService:
    """User service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_users(self) -> List[User]:
        """List all users"""
        return self.db.query(User).all()
    
    def get_user(self, user_id: int) -> User:
        """Get user by ID"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_cpf(self, cpf: str) -> Optional[User]:
        """Get user by CPF"""
        return self.db.query(User).filter(User.cpf == cpf).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create new user"""
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValidationError("Email already registered")
        
        # Check if username already exists (if provided)
        if user_data.username:
            existing_username = self.db.query(User).filter(User.username == user_data.username).first()
            if existing_username:
                raise ValidationError("Username already taken")
        
        # Check if CPF already exists (if provided)
        if user_data.cpf:
            existing_cpf = self.db.query(User).filter(User.cpf == user_data.cpf).first()
            if existing_cpf:
                raise ValidationError("CPF already registered")
        
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            cpf=user_data.cpf,
            phone=user_data.phone,
            crm=user_data.crm,
            specialty=user_data.specialty
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user"""
        user = self.get_user(user_id)
        
        # Check if email already exists (if changing)
        if user_data.email and user_data.email != user.email:
            existing_user = self.db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise ValidationError("Email already registered")
        
        # Update fields
        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: int) -> None:
        """Delete user"""
        user = self.get_user(user_id)
        self.db.delete(user)
        self.db.commit()
    
    def activate_user(self, user_id: int) -> User:
        """Activate user account"""
        user = self.get_user(user_id)
        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user_id: int) -> User:
        """Deactivate user account"""
        user = self.get_user(user_id)
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_user(self, user_id: int) -> User:
        """Verify user email"""
        user = self.get_user(user_id)
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
