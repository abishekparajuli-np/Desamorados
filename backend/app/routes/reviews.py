from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Review, Booking, User, Provider
from app.utils.ai_service import AIService

bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')
ai_service = AIService()


@bp.route('', methods=['POST'])
@jwt_required()
def create_review():
    """Submit a review for a completed booking"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or user.role != 'customer':
            return jsonify({"error": "Only customers can create reviews", "code": "UNAUTHORIZED"}), 403
        
        data = request.get_json()
        
        # Validate
        if not data or not data.get('booking_id') or not data.get('rating'):
            return jsonify({"error": "Missing booking_id or rating", "code": "VALIDATION_ERROR"}), 400
        
        booking = Booking.query.get(data['booking_id'])
        if not booking or booking.customer_id != user_id:
            return jsonify({"error": "Booking not found", "code": "NOT_FOUND"}), 404
        
        if booking.status != 'completed':
            return jsonify({"error": "Can only review completed bookings", "code": "VALIDATION_ERROR"}), 400
        
        # Check if review already exists
        existing_review = Review.query.filter_by(booking_id=booking.id).first()
        if existing_review:
            return jsonify({"error": "Review already exists for this booking", "code": "CONFLICT"}), 409
        
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5", "code": "VALIDATION_ERROR"}), 400
        
        # Analyze sentiment from comment
        comment = data.get('comment', '')
        sentiment = 'neutral'
        if comment:
            if any(word in comment.lower() for word in ['excellent', 'great', 'amazing', 'good', 'perfect', 'wonderful']):
                sentiment = 'positive'
            elif any(word in comment.lower() for word in ['bad', 'poor', 'terrible', 'awful', 'useless', 'worst']):
                sentiment = 'negative'
            elif rating >= 4:
                sentiment = 'positive'
            elif rating <= 2:
                sentiment = 'negative'
        
        review = Review(
            booking_id=booking.id,
            customer_id=user_id,
            provider_id=booking.provider_id,
            rating=rating,
            comment=comment,
            sentiment=sentiment,
            images=data.get('images', [])
        )
        
        db.session.add(review)
        db.session.flush()  # Get review ID
        
        # Update provider rating
        provider = Provider.query.filter_by(user_id=booking.provider_id).first()
        if provider:
            all_reviews = Review.query.filter_by(provider_id=booking.provider_id).all()
            avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 5.0
            provider.rating = round(avg_rating, 1)
            
            # Trigger review summary if 5+ reviews
            if len(all_reviews) >= 5:
                try:
                    reviews_data = [r.to_dict() for r in all_reviews[-10:]]
                    summary = ai_service.summarize_reviews(reviews_data)
                    provider.review_summary = summary
                except:
                    pass  # Non-critical
        
        db.session.commit()
        
        return jsonify({
            "data": review.to_dict(),
            "message": "Review created successfully"
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "code": "CREATE_ERROR"}), 500


@bp.route('/provider/<int:provider_id>', methods=['GET'])
def get_provider_reviews(provider_id):
    """Get all reviews for a provider"""
    try:
        provider = Provider.query.get(provider_id)
        if not provider:
            return jsonify({"error": "Provider not found", "code": "NOT_FOUND"}), 404
        
        page = request.args.get('page', type=int, default=1)
        per_page = request.args.get('per_page', type=int, default=10)
        
        query = Review.query.filter_by(provider_id=provider.user_id)
        total = query.count()
        
        reviews = query.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        data = [r.to_dict() for r in reviews]
        
        # Calculate stats
        if total > 0:
            avg_rating = sum(r.rating for r in query.all()) / total
        else:
            avg_rating = 0
        
        return jsonify({
            "data": {
                "reviews": data,
                "stats": {
                    "total_reviews": total,
                    "average_rating": round(avg_rating, 1),
                    "ai_summary": provider.review_summary
                },
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            },
            "message": "Reviews retrieved"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "FETCH_ERROR"}), 500


@bp.route('/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """Get a specific review"""
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"error": "Review not found", "code": "NOT_FOUND"}), 404
        
        return jsonify({
            "data": review.to_dict(),
            "message": "Review retrieved"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "code": "FETCH_ERROR"}), 500
