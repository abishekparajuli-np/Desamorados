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
        user_id = int(get_jwt_identity())
        data = request.get_json()

        provider_id = data.get('provider_id')
        service_id = data.get('service_id')

        if not provider_id:
            return jsonify({'error': 'provider_id required'}), 400

        # Auto-resolve service_id if not provided
        if not service_id:
            auto_service = Service.query.filter_by(
                is_active=True
            ).join(
                Provider, Service.provider_id == Provider.id
            ).filter(
                Provider.user_id == provider_id
            ).first()

            if auto_service:
                service_id = auto_service.id
            else:
                # Create a default service
                provider = Provider.query.filter_by(
                    user_id=provider_id
                ).first()
                if not provider:
                    return jsonify({'error': 'Provider not found'}), 404

                from app.models import ServiceCategory
                cat = ServiceCategory.query.first()
                if not cat:
                    return jsonify({'error': 'No service categories'}), 400

                svc = Service(
                    provider_id=provider.id,
                    category_id=cat.id,
                    title='General Service',
                    description='Home service',
                    price=float(data.get('final_price', 500) or 500),
                    price_type='fixed',
                    is_active=True
                )
                db.session.add(svc)
                db.session.flush()
                service_id = svc.id

        # Parse scheduled_at safely
        scheduled_at = None
        raw_dt = data.get('scheduled_at')
        if raw_dt:
            for fmt in ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    scheduled_at = datetime.strptime(
                        raw_dt.replace('Z','').split('+')[0].strip(), fmt
                    )
                    break
                except:
                    continue
        if not scheduled_at:
            scheduled_at = datetime.now()

        booking = Booking(
            customer_id=user_id,
            provider_id=provider_id,
            service_id=service_id,
            status='pending',
            scheduled_at=scheduled_at,
            address=data.get('address', ''),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            description=data.get('description', ''),
            ai_extracted_data=data.get('ai_extracted_data', {}),
            final_price=float(data.get('final_price', 0) or 0),
            payment_status='pending',
            notes=data.get('notes')
        )
        db.session.add(booking)
        db.session.commit()

        # Return provider contact details with booking
        provider = Provider.query.filter_by(user_id=provider_id).first()
        provider_user = User.query.get(provider_id)

        return jsonify({
            'data': {
                'booking': booking.to_dict(),
                'provider': {
                    'id': provider_user.id if provider_user else None,
                    'name': provider_user.name if provider_user else '',
                    'email': provider_user.email if provider_user else '',
                    'phone': provider_user.phone if provider_user else '',
                    'city': provider_user.city if provider_user else '',
                    'is_female': provider_user.is_female if provider_user else False,
                    'profile_photo': provider_user.profile_photo if provider_user else None,
                    'rating': float(provider.rating) if provider else 0,
                    'trust_badge': provider.trust_badge if provider else 'New',
                }
            },
            'message': 'Booking created successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'code': 'BOOKING_ERROR'}), 500


@bp.route('/my', methods=['GET'])
@jwt_required()
def my_bookings():
    """Get current customer's bookings"""
    try:
        user_id = int(get_jwt_identity())
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
        user_id = int(get_jwt_identity())
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
        user_id = int(get_jwt_identity())
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
