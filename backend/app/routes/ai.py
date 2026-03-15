from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import logging
from app import db
from app.models import Review, Provider, User, Booking
from app.utils.ai_service import AIService
from app.utils.matching import ProviderMatcher
import base64
import json
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Initialize AI service with error handling
try:
    ai_service = AIService()
    logger.info('AI Service initialized successfully')
except Exception as e:
    logger.error(f'Failed to initialize AI Service: {str(e)}')
    ai_service = None

matcher = ProviderMatcher()

# Simple rate limiting (in-memory)
request_counts = {}


def rate_limit(max_requests=20, window=60):
    """Rate limit decorator (20 req/min per user)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = get_jwt_identity() if request.headers.get('Authorization') else 'anon'
            now = datetime.utcnow()
            key = f"{user_id}:{now.minute}"
            
            if key not in request_counts:
                request_counts[key] = []
            
            request_counts[key] = [t for t in request_counts[key] if (now - t).total_seconds() < window]
            
            if len(request_counts[key]) >= max_requests:
                return jsonify({"error": "Rate limit exceeded", "code": "RATE_LIMIT"}), 429
            
            request_counts[key].append(now)
            return f(*args, **kwargs)
        return decorated
    return decorator


@bp.route('/chat', methods=['POST'])
@rate_limit(max_requests=20)
def chat():
    """AI booking chatbot - multi-turn conversation"""
    try:
        if not ai_service:
            return jsonify({
                'error': 'AI service not available - ANTHROPIC_API_KEY not configured',
                'code': 'AI_SERVICE_UNAVAILABLE'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided', 'code': 'VALIDATION_ERROR'}), 400
        
        messages = data.get('messages', [])
        language = data.get('language', 'english')
        
        if not messages:
            return jsonify({'error': 'No messages provided', 'code': 'VALIDATION_ERROR'}), 400
        
        logger.info(f'Chat request: {len(messages)} messages, language: {language}')
        
        # Chat with AI
        response = ai_service.booking_assistant_chat(messages, language)
        
        return jsonify({
            'data': {
                'response': response,
                'language': language
            },
            'message': 'Chat response received'
        }), 200
    
    except Exception as e:
        logger.error(f'Chat error: {str(e)}', exc_info=True)
        return jsonify({
            'error': str(e),
            'code': 'CHAT_ERROR'
        }), 500


@bp.route('/extract-booking', methods=['POST'])
@rate_limit(max_requests=20)
def extract_booking():
    """Extract structured booking data from natural language or image"""
    try:
        if not ai_service:
            return jsonify({
                'error': 'AI service not available - ANTHROPIC_API_KEY not configured',
                'code': 'AI_SERVICE_UNAVAILABLE'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided', 'code': 'VALIDATION_ERROR'}), 400
        
        description = data.get('description')
        image_base64 = data.get('image')
        
        if image_base64:
            logger.info('Extracting booking from image')
            extracted = ai_service.analyze_image(image_base64)
        elif description:
            logger.info(f'Extracting booking from text: {description[:50]}...')
            extracted = ai_service.extract_booking_details(description)
        else:
            return jsonify({'error': 'No description or image provided', 'code': 'VALIDATION_ERROR'}), 400
        
        return jsonify({
            'data': extracted,
            'message': 'Booking details extracted successfully'
        }), 200
    
    except Exception as e:
        logger.error(f'Extract booking error: {str(e)}', exc_info=True)
        return jsonify({
            'error': str(e),
            'code': 'EXTRACTION_ERROR'
        }), 500


@bp.route('/estimate-price', methods=['POST'])
@rate_limit(max_requests=20)
def estimate_price():
    """AI price estimation based on service and description"""
    try:
        if not ai_service:
            return jsonify({
                'error': 'AI service not available - ANTHROPIC_API_KEY not configured',
                'code': 'AI_SERVICE_UNAVAILABLE'
            }), 503
        
        data = request.get_json()
        service_category = data.get('service_category')
        description = data.get('description')
        
        if not service_category or not description:
            return jsonify({"error": "Missing service_category or description", "code": "VALIDATION_ERROR"}), 400
        
        if not ai_service:
            return jsonify({
                'error': 'AI service not available - ANTHROPIC_API_KEY not configured',
                'code': 'AI_SERVICE_UNAVAILABLE'
            }), 503
        
        estimate = ai_service.estimate_price(service_category, description)
        
        return jsonify({
            "data": estimate,
            "message": "Price estimation generated"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "ESTIMATION_ERROR"}), 500


@bp.route('/match-providers', methods=['POST'])
@rate_limit(max_requests=20)
def match_providers():
    """AI-ranked provider recommendations"""
    try:
        data = request.get_json()
        service_type = data.get('service_type')
        location = data.get('location')
        budget = data.get('budget')
        preferred_gender = data.get('preferred_gender')
        description = data.get('description')
        
        if not service_type or not location:
            return jsonify({"error": "Missing service_type or location", "code": "VALIDATION_ERROR"}), 400
        
        # Get matched providers
        result = matcher.match_providers(
            service_type,
            location,
            budget,
            preferred_gender,
            description
        )
        
        return jsonify({
            "data": result,
            "message": "Provider recommendations generated"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "MATCHING_ERROR"}), 500


@bp.route('/analyze-image', methods=['POST'])
@rate_limit(max_requests=10)
def analyze_image():
    """Upload photo to detect problem and suggest service"""
    try:
        # Check if image in request
        if 'image' not in request.files:
            return jsonify({"error": "No image provided", "code": "VALIDATION_ERROR"}), 400
        
        file = request.files['image']
        
        # Validate file
        if file.filename == '':
            return jsonify({"error": "No filename", "code": "VALIDATION_ERROR"}), 400
        
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return jsonify({"error": "Invalid file type. Allowed: jpg, jpeg, png", "code": "VALIDATION_ERROR"}), 400
        
        # Read and encode image
        file_data = file.read()
        image_base64 = base64.b64encode(file_data).decode('utf-8')
        
        if not ai_service:
            return jsonify({
                'error': 'AI service not available - ANTHROPIC_API_KEY not configured',
                'code': 'AI_SERVICE_UNAVAILABLE'
            }), 503
        
        # Analyze
        analysis = ai_service.analyze_image(image_base64)
        
        return jsonify({
            "data": analysis,
            "message": "Image analyzed successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "IMAGE_ANALYSIS_ERROR"}), 500


@bp.route('/summarize-reviews', methods=['POST'])
@jwt_required()
def summarize_reviews():
    """AI summarize provider reviews"""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        
        if not provider_id:
            return jsonify({"error": "provider_id required", "code": "VALIDATION_ERROR"}), 400
        
        provider = Provider.query.get(provider_id)
        if not provider:
            return jsonify({"error": "Provider not found", "code": "NOT_FOUND"}), 404
        
        if not ai_service:
            return jsonify({
                'error': 'AI service not available - ANTHROPIC_API_KEY not configured',
                'code': 'AI_SERVICE_UNAVAILABLE'
            }), 503
        
        # Get all reviews for this provider
        reviews = Review.query.filter_by(provider_id=provider.user_id).all()
        
        if len(reviews) < 5:
            return jsonify({
                "data": {
                    "summary": None,
                    "review_count": len(reviews),
                    "message": "Need at least 5 reviews for AI summary"
                },
                "message": "Insufficient reviews"
            }), 200
        
        reviews_data = [r.to_dict() for r in reviews[-10:]]  # Last 10 reviews
        summary = ai_service.summarize_reviews(reviews_data)
        
        # Store summary
        provider.review_summary = summary
        db.session.commit()
        
        return jsonify({
            "data": {
                "summary": summary,
                "review_count": len(reviews)
            },
            "message": "Reviews summarized successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "SUMMARY_ERROR"}), 500


@bp.route('/trust-score', methods=['POST'])
@jwt_required()
def calculate_trust_score():
    """Generate AI trust score for provider"""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        
        if not provider_id:
            return jsonify({"error": "provider_id required", "code": "VALIDATION_ERROR"}), 400
        
        provider = Provider.query.get(provider_id)
        if not provider:
            return jsonify({"error": "Provider not found", "code": "NOT_FOUND"}), 404
        
        # Prepare provider data for AI
        reviews = Review.query.filter_by(provider_id=provider.user_id).all()
        
        # Calculate sentiment
        sentiments = [r.sentiment for r in reviews if r.sentiment]
        positive_count = sum(1 for s in sentiments if s == 'positive')
        positive_pct = (positive_count / len(sentiments) * 100) if sentiments else 50
        
        sentiment_map = {
            'positive': 'positive',
            'neutral': 'neutral',
            'negative': 'negative'
        }
        avg_sentiment = 'positive' if positive_pct > 60 else ('negative' if positive_pct < 30 else 'neutral')
        
        provider_data = {
            'years_experience': provider.years_experience,
            'id_verified': provider.id_verified,
            'total_jobs': provider.total_jobs,
            'avg_rating': provider.rating,
            'completion_rate': provider.completion_rate,
            'review_sentiment': avg_sentiment
        }
        
        # Get trust score from AI
        result = ai_service.calculate_trust_score(provider_data)
        
        # Update provider
        provider.trust_score = result['trust_score']
        provider.trust_badge = result['badge']
        db.session.commit()
        
        return jsonify({
            "data": result,
            "message": "Trust score calculated"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "TRUST_SCORE_ERROR"}), 500
