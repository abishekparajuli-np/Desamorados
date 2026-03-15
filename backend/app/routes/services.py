from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Service, ServiceCategory, User, Provider

bp = Blueprint('services', __name__, url_prefix='/api/services')


@bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all service categories"""
    try:
        categories = ServiceCategory.query.all()
        data = [c.to_dict() for c in categories]
        
        return jsonify({
            "data": data,
            "message": "Categories retrieved successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "FETCH_ERROR"}), 500


@bp.route('', methods=['GET'])
def list_services():
    """List services with filtering"""
    try:
        # Filters
        category_id = request.args.get('category_id', type=int)
        provider_id = request.args.get('provider_id', type=int)
        min_price = request.args.get('min_price', type=float, default=0)
        max_price = request.args.get('max_price', type=float, default=float('inf'))
        city = request.args.get('city')
        women_first = request.args.get('women_first', type=lambda x: x.lower() == 'true', default=False)
        page = request.args.get('page', type=int, default=1)
        per_page = request.args.get('per_page', type=int, default=12)
        
        # Base query
        query = Service.query.filter(Service.is_active == True)
        
        if category_id:
            query = query.filter(Service.category_id == category_id)
        
        if provider_id:
            query = query.filter(Service.provider_id == provider_id)
        
        query = query.filter(
            Service.price >= min_price,
            Service.price <= max_price
        )
        
        # Filter by city if provided
        if city:
            query = query.join(Provider).join(User).filter(User.city.ilike(f'%{city}%'))
        
        # Women first filter
        if women_first:
            query = query.join(Provider).join(User).filter(User.is_female == True)
        
        # Get total
        total = query.count()
        
        # Order and paginate
        query = query.order_by(Service.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        services = query.all()
        
        # Format response
        data = []
        for service in services:
            service_dict = service.to_dict()
            # Add provider info
            provider = service.provider
            if provider:
                provider_user = provider.user
                service_dict['provider'] = {
                    'id': provider.id,
                    'user_id': provider_user.id,
                    'name': provider_user.name,
                    'city': provider_user.city,
                    'profile_photo': provider_user.profile_photo,
                    'is_female': provider_user.is_female,
                    'rating': provider.rating,
                    'trust_score': provider.trust_score,
                    'trust_badge': provider.trust_badge,
                    'total_jobs': provider.total_jobs
                }
            data.append(service_dict)
        
        return jsonify({
            "data": {
                "services": data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            },
            "message": "Services retrieved successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "LIST_ERROR"}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_service():
    """Provider creates a new service"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'provider':
            return jsonify({"error": "Only providers can create services", "code": "UNAUTHORIZED"}), 403
        
        provider = user.provider_profile
        if not provider:
            return jsonify({"error": "Provider profile not found", "code": "NOT_FOUND"}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('category_id') or not data.get('title') or not data.get('price'):
            return jsonify({"error": "Missing required fields", "code": "VALIDATION_ERROR"}), 400
        
        # Check category exists
        category = ServiceCategory.query.get(data['category_id'])
        if not category:
            return jsonify({"error": "Category not found", "code": "NOT_FOUND"}), 404
        
        service = Service(
            provider_id=provider.id,
            category_id=data['category_id'],
            title=data['title'],
            description=data.get('description'),
            price=data['price'],
            price_type=data.get('price_type', 'fixed'),
            image_url=data.get('image_url'),
            is_active=True
        )
        
        db.session.add(service)
        db.session.commit()
        
        return jsonify({
            "data": service.to_dict(),
            "message": "Service created successfully"
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "code": "CREATE_ERROR"}), 500


@bp.route('/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
    """Update a service"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'provider':
            return jsonify({"error": "Unauthorized", "code": "UNAUTHORIZED"}), 403
        
        service = Service.query.get(service_id)
        if not service or service.provider_id != user.provider_profile.id:
            return jsonify({"error": "Service not found", "code": "NOT_FOUND"}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            service.title = data['title']
        if 'description' in data:
            service.description = data['description']
        if 'price' in data:
            service.price = data['price']
        if 'price_type' in data:
            service.price_type = data['price_type']
        if 'is_active' in data:
            service.is_active = data['is_active']
        if 'image_url' in data:
            service.image_url = data['image_url']
        
        db.session.commit()
        
        return jsonify({
            "data": service.to_dict(),
            "message": "Service updated successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "code": "UPDATE_ERROR"}), 500


@bp.route('/<int:service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    """Delete a service"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'provider':
            return jsonify({"error": "Unauthorized", "code": "UNAUTHORIZED"}), 403
        
        service = Service.query.get(service_id)
        if not service or service.provider_id != user.provider_profile.id:
            return jsonify({"error": "Service not found", "code": "NOT_FOUND"}), 404
        
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({
            "data": {"id": service_id},
            "message": "Service deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "code": "DELETE_ERROR"}), 500
