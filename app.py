from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Get environment variables
API_TOKEN = os.getenv('API_TOKEN', 'lpu-super-secret-token-2024')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning('GEMINI_API_KEY not set. Set it with: $env:GEMINI_API_KEY = "your-key"')

# Rate limiting tracker (simple in-memory)
rate_limits = {}

@app.route('/generate', methods=['POST'])
def generate_answer():
    """
    Receive extracted question and return AI-generated answer using Google Gemini
    
    Request payload:
    {
        "hwid": "device-id",
        "app_id": "app-id",
        "api_token": "token",
        "message": "question text",
        "images": []
    }
    
    Response:
    {
        "success": true,
        "answer": "generated answer",
        "stats": {
            "limit": 100,
            "used": 5
        }
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
        
        # Validate API token
        provided_token = data.get('api_token', '')
        if provided_token != API_TOKEN:
            return jsonify({'success': False, 'error': 'Invalid API token'}), 401
        
        # Get message
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Message is empty'}), 400
        
        hwid = data.get('hwid', '')
        
        # Check if Gemini API key is set
        if not GEMINI_API_KEY:
            return jsonify({
                'success': False, 
                'error': 'Gemini API key not configured on server'
            }), 500
        
        logger.info(f'[{hwid}] Processing question: {message[:100]}...')
        
        # Call Google Gemini API
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(message)
            answer = response.text
            
            logger.info(f'[{hwid}] Generated answer length: {len(answer)} chars')
        except Exception as e:
            logger.error(f'[{hwid}] Gemini API error: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'LLM error: {str(e)}'
            }), 500
        
        # Update rate limit tracker
        if hwid not in rate_limits:
            rate_limits[hwid] = {'used': 0}
        rate_limits[hwid]['used'] += 1
        used = rate_limits[hwid]['used']
        
        return jsonify({
            'success': True,
            'answer': answer,
            'stats': {
                'limit': 100,
                'used': used
            }
        }), 200
    
    except Exception as e:
        logger.error(f'Unhandled error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'server': 'LPU Backend Running'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
