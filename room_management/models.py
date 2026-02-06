"""Database models for Room Management Application"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Room(db.Model):
    """Room model for storing room information"""
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False, default='Standard')
    floor = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    check_ins_outs = db.relationship('CheckInOut', backref='room', lazy=True, 
                                       order_by='CheckInOut.created_at.desc()')
    
    def __repr__(self):
        return f'<Room {self.room_number}>'
    
    def to_dict(self):
        """Convert room to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'floor': self.floor,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class CheckInOut(db.Model):
    """Check-in/Check-out records for rooms"""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=True)
    reason = db.Column(db.String(255), nullable=True)  # Reason for check-out
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<CheckInOut Room {self.room_id}: {self.check_in_date} - {self.check_out_date}>'
    
    def to_dict(self):
        """Convert check-in/out to dictionary"""
        return {
            'id': self.id,
            'room_id': self.room_id,
            'room_number': self.room.room_number if self.room else None,
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else None,
            'check_out_date': self.check_out_date.isoformat() if self.check_out_date else None,
            'reason': self.reason,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def is_currently_occupied(self):
        """Check if room is currently occupied (no check-out date)"""
        return self.check_out_date is None


class VacancySettings(db.Model):
    """Settings for vacancy calculation criteria"""
    id = db.Column(db.Integer, primary_key=True)
    early_checkout_day = db.Column(db.Integer, nullable=False, default=5)
    late_checkout_day = db.Column(db.Integer, nullable=False, default=25)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<VacancySettings Early:{self.early_checkout_day} Late:{self.late_checkout_day}>'
    
    def to_dict(self):
        """Convert settings to dictionary"""
        return {
            'id': self.id,
            'early_checkout_day': self.early_checkout_day,
            'late_checkout_day': self.late_checkout_day,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def get_settings():
        """Get current settings or create default if none exist"""
        settings = VacancySettings.query.first()
        if not settings:
            settings = VacancySettings()
            db.session.add(settings)
            db.session.commit()
        return settings
