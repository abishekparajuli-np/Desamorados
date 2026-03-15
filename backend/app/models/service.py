from app import db
from datetime import datetime


class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    name_np = db.Column(db.String(120), nullable=True)  # Nepali name
    icon = db.Column(db.String(255), nullable=True)  # Icon URL or emoji
    description = db.Column(db.Text, nullable=True)
    base_price = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    services = db.relationship('Service', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_np': self.name_np,
            'icon': self.icon,
            'description': self.description,
            'base_price': self.base_price,
            'created_at': self.created_at.isoformat(),
        }


class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    price_type = db.Column(db.String(50), default='fixed', nullable=False)  # fixed or hourly
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='service', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'price_type': self.price_type,
            'is_active': self.is_active,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
