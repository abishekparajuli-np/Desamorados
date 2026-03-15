from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from geoalchemy2 import Geometry
from sqlalchemy import func
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='customer', nullable=False)  # customer, provider, admin
    gender = db.Column(db.String(20), nullable=True)  # male, female, other
    profile_photo = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    city = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_female = db.Column(db.Boolean, default=False)  # For Women First feature
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider_profile = db.relationship('Provider', uselist=False, back_populates='user', cascade='all, delete-orphan')
    customer_bookings = db.relationship('Booking', backref='customer', lazy=True, cascade='all, delete-orphan', foreign_keys='Booking.customer_id')
    provider_bookings = db.relationship('Booking', backref='provider', lazy=True, cascade='all, delete-orphan', foreign_keys='Booking.provider_id')
    customer_reviews = db.relationship('Review', backref='customer', lazy=True, cascade='all, delete-orphan', foreign_keys='Review.customer_id')
    provider_reviews = db.relationship('Review', backref='provider', lazy=True, cascade='all, delete-orphan', foreign_keys='Review.provider_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_bookings=False):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'gender': self.gender,
            'profile_photo': self.profile_photo,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'city': self.city,
            'address': self.address,
            'is_verified': self.is_verified,
            'is_female': self.is_female,
            'created_at': self.created_at.isoformat(),
        }
        
        if self.role == 'provider' and self.provider_profile:
            data['provider'] = self.provider_profile.to_dict()
        
        return data


class Provider(db.Model):
    __tablename__ = 'providers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    skills = db.Column(db.JSON, default=[], nullable=False)  # Array of skills
    years_experience = db.Column(db.Integer, default=0, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    rating = db.Column(db.Float, default=5.0, nullable=False)
    total_jobs = db.Column(db.Integer, default=0, nullable=False)
    total_earnings = db.Column(db.Float, default=0.0, nullable=False)
    trust_score = db.Column(db.Integer, default=50, nullable=False)  # 0-100, AI-generated
    trust_badge = db.Column(db.String(50), default='New', nullable=False)  # New, Rising, Trusted, Expert
    id_verified = db.Column(db.Boolean, default=False, nullable=False)
    certifications = db.Column(db.JSON, default=[], nullable=False)  # Array of file paths
    hourly_rate = db.Column(db.Float, nullable=True)
    service_radius_km = db.Column(db.Float, default=10.0, nullable=False)
    wkb_geometry = db.Column(Geometry('POINT', srid=4326), nullable=True)
    review_summary = db.Column(db.Text, nullable=True)  # AI-generated summary
    completion_rate = db.Column(db.Float, default=0.0, nullable=False)  # Percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='provider_profile')
    services = db.relationship('Service', backref='provider', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        # Extract latitude/longitude from geometry if available
        latitude = None
        longitude = None
        if self.wkb_geometry:
            try:
                latitude = db.session.scalar(func.ST_Y(self.wkb_geometry))
                longitude = db.session.scalar(func.ST_X(self.wkb_geometry))
            except:
                pass
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user.name if self.user else None,
            'city': self.user.city if self.user else None,
            'bio': self.bio,
            'skills': self.skills,
            'years_experience': self.years_experience,
            'is_available': self.is_available,
            'is_female': self.user.is_female if self.user else False,
            'latitude': latitude,
            'longitude': longitude,
            'rating': self.rating,
            'total_jobs': self.total_jobs,
            'total_earnings': self.total_earnings,
            'trust_score': self.trust_score,
            'trust_badge': self.trust_badge,
            'id_verified': self.id_verified,
            'certifications': self.certifications,
            'hourly_rate': self.hourly_rate,
            'service_radius_km': self.service_radius_km,
            'review_summary': self.review_summary,
            'completion_rate': self.completion_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
