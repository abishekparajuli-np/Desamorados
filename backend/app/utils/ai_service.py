import os
from anthropic import Anthropic
import base64
import json


class AIService:
    """Wrapper for Anthropic Claude API"""
    
    def __init__(self):
        self.client = Anthropic()
        self.model = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")
    
    def chat(self, messages, system_prompt=None, max_tokens=1024):
        """Send messages to Claude and get response"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"AI Service Error: {str(e)}")
    
    def extract_booking_details(self, description):
        """Extract structured booking data from natural language"""
        prompt = f"""Extract booking details from this description. Return valid JSON only.
        
Description: {description}

Return a JSON object with these fields (infer from context, use null if not found):
- service_type (string)
- location (string)
- preferred_time (string or null)
- urgency (low/medium/high)
- estimated_budget (number or null)
- problem_description (string)

JSON only, no markdown:"""
        
        response = self.chat([{"role": "user", "content": prompt}], max_tokens=500)
        
        try:
            # Extract JSON from response
            json_str = response.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "service_type": None,
                "location": None,
                "preferred_time": None,
                "urgency": "medium",
                "estimated_budget": None,
                "problem_description": description
            }
    
    def estimate_price(self, service_category, description):
        """Estimate price for a service based on description"""
        prompt = f"""You are a pricing expert for home services in Nepal. 
        
Service Category: {service_category}
Job Description: {description}

Provide a price estimate. Consider Nepal-specific factors like location premium for Kathmandu valley.

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "min_price": number,
  "max_price": number,
  "currency": "NPR",
  "reasoning": "string",
  "complexity": "low|medium|high"
}}"""
        
        response = self.chat([{"role": "user", "content": prompt}], max_tokens=300)
        
        try:
            json_str = response.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "min_price": 500,
                "max_price": 1500,
                "currency": "NPR",
                "reasoning": "Unable to estimate - contact provider",
                "complexity": "medium"
            }
    
    def analyze_image(self, image_base64):
        """Analyze an image to detect problems and suggest services"""
        prompt = "Analyze this image and identify: 1) What problem is shown, 2) What service category it needs, 3) Urgency level, 4) Complexity, 5) What to tell the provider. Return JSON only."
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            response_text = response.content[0].text
            json_str = response_text.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "problem_description": "Unable to analyze image",
                "suggested_service": None,
                "urgency_level": "medium",
                "complexity": "medium",
                "provider_notes": "Please describe the issue"
            }
        except Exception as e:
            raise Exception(f"Image analysis failed: {str(e)}")
    
    def summarize_reviews(self, reviews):
        """Summarize multiple reviews into 2-3 sentences"""
        reviews_text = "\n".join([f"Rating {r['rating']}/5: {r['comment']}" for r in reviews])
        
        prompt = f"""Summarize these reviews in 2-3 sentences. Highlight main themes.

Reviews:
{reviews_text}

Provide a concise, professional summary only."""
        
        response = self.chat([{"role": "user", "content": prompt}], max_tokens=200)
        return response.strip()
    
    def calculate_trust_score(self, provider_data):
        """Calculate AI trust score for a provider"""
        prompt = f"""Based on this provider data, calculate a trust score 0-100 and assign a badge.

Data:
- Years of experience: {provider_data.get('years_experience', 0)}
- ID verified: {provider_data.get('id_verified', False)}
- Total jobs completed: {provider_data.get('total_jobs', 0)}
- Average rating: {provider_data.get('avg_rating', 0)}/5
- Completion rate: {provider_data.get('completion_rate', 0)}%
- Review sentiment: {provider_data.get('review_sentiment', 'neutral')}

Return ONLY valid JSON:
{{
  "trust_score": number (0-100),
  "badge": "New|Rising|Trusted|Expert"
}}"""
        
        try:
            response = self.chat([{"role": "user", "content": prompt}], max_tokens=200)
            json_str = response.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"trust_score": 50, "badge": "New"}
    
    def booking_assistant_chat(self, message_history, language="english"):
        """AI booking assistant for multi-turn conversation"""
        system_prompt = f"""You are SewaSathi's booking assistant for Nepal. Help users book home services.
        
Language: {language}
- Extract service type, location, time, description, urgency from conversation
- Be warm, helpful, and respond in the user's language (Nepali or English)
- When user seems ready to book, return JSON with extracted data
- Available services: Plumbing, House Cleaning, Electrical, Beauty, Carpentry, Painting, AC, Tutoring, Pest Control, Cooking"""
        
        response = self.chat(message_history, system_prompt=system_prompt, max_tokens=500)
        return response
