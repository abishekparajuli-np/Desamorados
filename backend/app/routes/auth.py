from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, Provider
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user (customer or provider)"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing required fields", "code": "VALIDATION_ERROR"}), 400
        
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already registered", "code": "EMAIL_EXISTS"}), 409
        
        # Create user
        user = User(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            role=data.get('role', 'customer'),
            gender=data.get('gender'),
            city=data.get('city'),
            is_female=(data.get('gender', '').lower() == 'female')
        )
        user.set_password(data.get('password'))
        
        db.session.add(user)
        db.session.flush()  # Get user ID without committing
        
        # If provider, create provider profile
        if user.role == 'provider':
            provider = Provider(user_id=user.id)
            db.session.add(provider)
        
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            "data": {
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            "message": "User registered successfully"
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "code": "REGISTER_ERROR"}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Login user with email and password"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing email or password", "code": "VALIDATION_ERROR"}), 400
        
        user = User.query.filter_by(email=data.get('email')).first()
        
        if not user or not user.check_password(data.get('password')):
            return jsonify({"error": "Invalid email or password", "code": "AUTH_FAILED"}), 401
        
        # Generate tokens
        access_token = create_access_token(identity=str(user.id))   # RIGHT - string
        refresh_token = create_refresh_token(identity=str(user.id)) # RIGHT - string
        
        return jsonify({
            "data": {
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            "message": "Login successful"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "LOGIN_ERROR"}), 500


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        user_id = int(get_jwt_identity())
        access_token = create_access_token(identity=str(user_id))
        
        return jsonify({
            "data": {"access_token": access_token},
            "message": "Token refreshed successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "REFRESH_ERROR"}), 500


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current logged-in user"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found", "code": "NOT_FOUND"}), 404
        
        return jsonify({
            "data": user.to_dict(),
            "message": "User retrieved successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "FETCH_ERROR"}), 500
