from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Booking, User, Service, Provider
from datetime import datetime

bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')


@bp.route('', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new booking"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'customer':
            return jsonify({"error": "Only customers can create bookings", "code": "UNAUTHORIZED"}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('provider_id') or not data.get('service_id'):
            return jsonify({"error": "Missing required fields", "code": "VALIDATION_ERROR"}), 400
        
        # Verify service and provider
        service = Service.query.get(data['service_id'])
        if not service:
            return jsonify({"error": "Service not found", "code": "NOT_FOUND"}), 404
        
        provider = Provider.query.get(data['provider_id'])
        if not provider:
            return jsonify({"error": "Provider not found", "code": "NOT_FOUND"}), 404
        
        # Create booking
        booking = Booking(
            customer_id=user_id,
            provider_id=provider.user_id,
            service_id=service.id,
            status='pending',
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            description=data.get('description'),
            final_price=data.get('final_price', service.price),
            ai_extracted_data=data.get('ai_extracted_data', {}),
            notes=data.get('notes')
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            "data": booking.to_dict(),
            "message": "Booking created successfully"
        }), 201
    
    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {str(e)}", "code": "VALIDATION_ERROR"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "code": "CREATE_ERROR"}), 500


@bp.route('/my', methods=['GET'])
@jwt_required()
def my_bookings():
    """Get current customer's bookings"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'customer':
            return jsonify({"error": "Only customers can view bookings", "code": "UNAUTHORIZED"}), 403
        
        page = request.args.get('page', type=int, default=1)
        per_page = request.args.get('per_page', type=int, default=10)
        status = request.args.get('status')
        
        query = Booking.query.filter_by(customer_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        bookings = query.order_by(Booking.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        data = [b.to_dict() for b in bookings]
        
        return jsonify({
            "data": {
                "bookings": data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            },
            "message": "Bookings retrieved"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "FETCH_ERROR"}), 500


@bp.route('/assigned', methods=['GET'])
@jwt_required()
def assigned_bookings():
    """Get provider's assigned bookings"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'provider':
            return jsonify({"error": "Only providers can view assigned bookings", "code": "UNAUTHORIZED"}), 403
        
        page = request.args.get('page', type=int, default=1)
        per_page = request.args.get('per_page', type=int, default=10)
        status = request.args.get('status')
        
        query = Booking.query.filter_by(provider_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        bookings = query.order_by(Booking.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        data = [b.to_dict() for b in bookings]
        
        return jsonify({
            "data": {
                "bookings": data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            },
            "message": "Assigned bookings retrieved"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "FETCH_ERROR"}), 500


@bp.route('/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get booking details"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return jsonify({"error": "Booking not found", "code": "NOT_FOUND"}), 404
        
        return jsonify({
            "data": booking.to_dict(),
            "message": "Booking retrieved"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "FETCH_ERROR"}), 500


@bp.route('/<int:booking_id>/status', methods=['PUT'])
@jwt_required()
def update_booking_status(booking_id):
    """Update booking status"""
    try:
        user_id = get_jwt_identity()
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return jsonify({"error": "Booking not found", "code": "NOT_FOUND"}), 404
        
        # Check authorization
        if booking.provider_id != user_id and booking.customer_id != user_id:
            return jsonify({"error": "Unauthorized", "code": "UNAUTHORIZED"}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Allowed: {', '.join(valid_statuses)}", "code": "VALIDATION_ERROR"}), 400
        
        booking.status = new_status
        
        if new_status == 'completed':
            booking.completed_at = datetime.utcnow()
            booking.payment_status = 'completed'
            
            # Update provider stats
            provider = Provider.query.filter_by(user_id=booking.provider_id).first()
            if provider:
                provider.total_jobs += 1
                if booking.final_price:
                    provider.total_earnings += booking.final_price
        
        if new_status == 'cancelled':
            booking.payment_status = 'cancelled'
        
        db.session.commit()
        
        return jsonify({
            "data": booking.to_dict(),
            "message": "Booking status updated"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "code": "UPDATE_ERROR"}), 500
