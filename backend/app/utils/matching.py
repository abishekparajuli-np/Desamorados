import json
from app.models import Provider, Service, ServiceCategory, User
from app.utils.ai_service import AIService


class ProviderMatcher:
    """Smart provider matching using AI"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def match_providers(self, service_type, location, budget=None, preferred_gender=None, description=None):
        """Find and rank best providers for a job"""
        
        # Find service category
        category = ServiceCategory.query.filter_by(name=service_type).first() or \
                  ServiceCategory.query.filter_by(name_np=service_type).first()
        
        if not category:
            return {"error": "Service category not found", "providers": []}
        
        # Find candidate providers
        candidates = Service.query.filter_by(category_id=category.id, is_active=True).all()
        provider_list = []
        
        for service in candidates:
            provider = Provider.query.get(service.provider_id)
            user = provider.user
            
            if not provider.is_available:
                continue
            
            candidate_data = {
                "provider_id": provider.id,
                "user_id": user.id,
                "name": user.name,
                "city": user.city,
                "rating": provider.rating,
                "expertise": provider.skills,
                "years_experience": provider.years_experience,
                "service_price": service.price,
                "is_female": user.is_female,
                "profile_photo": user.profile_photo,
                "total_jobs": provider.total_jobs,
                "trust_score": provider.trust_score,
            }
            
            provider_list.append(candidate_data)
        
        if not provider_list:
            return {"error": "No providers available", "providers": []}
        
        # Use AI to rank providers
        ranking_prompt = self._build_ranking_prompt(
            provider_list, 
            service_type, 
            location, 
            budget, 
            preferred_gender,
            description
        )
        
        try:
            ai_response = self.ai_service.chat([{"role": "user", "content": ranking_prompt}], max_tokens=1000)
            ranked = self._parse_ai_ranking(ai_response, provider_list)
            return {"providers": ranked[:5]}  # Return top 5
        except Exception as e:
            # Fallback to simple ranking by rating
            ranked = sorted(provider_list, key=lambda p: p['rating'], reverse=True)
            for p in ranked:
                p['match_reason'] = f"Top rated provider with {p['rating']} rating"
            return {"providers": ranked[:5]}
    
    def _build_ranking_prompt(self, providers, service_type, location, budget, preferred_gender, description):
        """Build AI ranking prompt"""
        providers_json = json.dumps(providers[:10])  # Top 10 candidates
        
        prompt = f"""You are a provider matching algorithm for SewaSathi (Nepal home services).

PROVIDERS (JSON array):
{providers_json}

JOB DETAILS:
- Service: {service_type}
- Location: {location}
- Budget: {budget or 'flexible'} NPR
- Gender preference: {preferred_gender or 'any'}
- Description: {description or 'none provided'}

RANKING RULES:
1. Match service expertise
2. Consider location proximity
3. Rating >= 4.5 gets bonus points
4. Trust score weight: 20%
5. Female providers get +10 bonus if "women first" preference
6. Recent good reviews weight heavily
7. Experience > 3 years gets preference

Return ONLY valid JSON array (no markdown):
[
  {{
    "provider_id": number,
    "match_score": number (0-100),
    "match_reason": "string explaining why they're a good match"
  }},
  ...
]

Order by match_score descending."""
        
        return prompt
    
    def _parse_ai_ranking(self, ai_response, provider_list):
        """Parse AI ranking response"""
        try:
            json_str = ai_response.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            
            rankings = json.loads(json_str)
            
            # Merge rankings with provider details
            result = []
            for rank in rankings:
                provider = next((p for p in provider_list if p['provider_id'] == rank['provider_id']), None)
                if provider:
                    provider['match_score'] = rank.get('match_score', 50)
                    provider['match_reason'] = rank.get('match_reason', 'Good match')
                    result.append(provider)
            
            return sorted(result, key=lambda p: p['match_score'], reverse=True)
        except:
            # Fallback
            for p in provider_list:
                p['match_score'] = p['rating'] * 20
                p['match_reason'] = 'Highly rated'
            return sorted(provider_list, key=lambda p: p['match_score'], reverse=True)
