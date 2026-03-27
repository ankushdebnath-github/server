from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
API_TOKEN = os.getenv('API_TOKEN_LPU', 'lpu-super-secret-token-2024')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
MAX_REQUESTS_PER_DAY = int(os.getenv('MAX_REQUESTS_PER_DAY', '100'))

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info('✅ Gemini API configured')
else:
    logger.warning('⚠️ GEMINI_API_KEY not set')

# System prompts for better answers
MCQ_PROMPT = """You are an expert academic assistant. 
Analyze this MCQ and provide ONLY the correct answer.
Be concise. No explanations. Format: [ANSWER] Your answer"""

CODE_PROMPT = """You are an expert programmer.
Solve this coding problem.
Provide ONLY the code - no explanations or markdown blocks."""

# Improved rate limiting with daily reset
rate_limits = {}

def get_rate_limit_key(hwid):
    """Get today's rate limit key"""
    today = datetime.now().strftime('%Y-%m-%d')
    return f"{hwid}_{today}"

def check_and_update_rate_limit(hwid):
    """Check rate limit and update counter"""
    key = get_rate_limit_key(hwid)
    if key not in rate_limits:
        rate_limits[key] = {'used': 0}
    
    if rate_limits[key]['used'] >= MAX_REQUESTS_PER_DAY:
        return False  # Limit exceeded
    
    rate_limits[key]['used'] += 1
    return True

def detect_question_type(text):
    """Detect if question is MCQ or Code (optimization for better prompts)"""
    text_lower = text.lower()
    code_indicators = ['code', 'function', 'def ', 'class ', 'print(', 'sql', 'section 2']
    mcq_indicators = ['option', 'choose', 'select', 'a)', 'b)', 'c)', 'd)', 'mcq']
    
    code_score = sum(1 for indicator in code_indicators if indicator in text_lower)
    mcq_score = sum(1 for indicator in mcq_indicators if indicator in text_lower)
    
    return 'code' if code_score > mcq_score else 'mcq'

@app.route('/generate', methods=['POST'])
def generate_answer():
    """
    Optimized endpoint with:
    - System prompts for MCQ vs Code
    - Better rate limiting with daily reset
    - Input validation
    - Response validation
    """
    import time
    start_time = time.time()
    
    try:
        data = request.json
        
        # Validate request
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
        
        # Validate API token
        if data.get('api_token') != API_TOKEN:
            logger.warning('❌ Invalid API token')
            return jsonify({'success': False, 'error': 'Invalid API token'}), 401
        
        # Get and validate message
        message = data.get('message', '').strip()
        if not message or len(message) < 5:
            return jsonify({'success': False, 'error': 'Question text too short'}), 400
        
        hwid = data.get('hwid', 'unknown')
        
        # Check rate limit BEFORE processing
        if not check_and_update_rate_limit(hwid):
            logger.warning(f'❌ Rate limit exceeded: {hwid}')
            return jsonify({
                'success': False,
                'error': f'Daily limit reached ({MAX_REQUESTS_PER_DAY}). Try tomorrow.'
            }), 429
        
        # Validate Gemini setup
        if not GEMINI_API_KEY:
            logger.error('❌ Gemini API not configured')
            return jsonify({'success': False, 'error': 'Server not configured'}), 500
        
        # Detect question type
        q_type = detect_question_type(message)
        system_prompt = MCQ_PROMPT if q_type == 'mcq' else CODE_PROMPT
        
        logger.info(f'[{hwid[:8]}...] Type: {q_type}, Chars: {len(message)}')
        
        # Call Gemini with system prompt
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            response = model.generate_content(
                f"{system_prompt}\n\n{message}",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.2 if q_type == 'mcq' else 0.3
                )
            )
            
            answer = response.text.strip()
            
            if not answer:
                return jsonify({'success': False, 'error': 'Empty response'}), 500
            
            elapsed = time.time() - start_time
            logger.info(f'✅ [{hwid[:8]}...] Answer: {len(answer)} chars, {elapsed:.2f}s')
            
            return jsonify({
                'success': True,
                'answer': answer,
                'type': q_type,
                'stats': {
                    'limit': MAX_REQUESTS_PER_DAY,
                    'used': rate_limits[get_rate_limit_key(hwid)]['used'],
                    'response_time': round(elapsed, 2)
                }
            }), 200
        
        except Exception as e:
            logger.error(f'❌ LLM error: {str(e)}')
            return jsonify({'success': False, 'error': f'LLM error: {str(e)[:100]}'}), 500
    
    except Exception as e:
        logger.error(f'❌ Unhandled error: {str(e)}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'LPU Backend',
        'timestamp': datetime.now().isoformat(),
        'gemini': 'configured' if GEMINI_API_KEY else 'not_configured'
    }), 200

@app.route('/stats', methods=['GET'])
def stats():
    """Get server statistics (optional - for monitoring)"""
    total_requests = sum(data['used'] for data in rate_limits.values())
    active_devices = len(set(key.split('_')[0] for key in rate_limits.keys()))
    
    return jsonify({
        'total_requests': total_requests,
        'active_devices': active_devices,
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info('=' * 50)
    logger.info('🚀 LPU Helper Backend Starting')
    logger.info(f'📍 Port: {port}')
    logger.info(f'🔒 API Token: Required')
    logger.info(f'📖 Max requests/day: {MAX_REQUESTS_PER_DAY}')
    logger.info('=' * 50)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True  # Enable threading for concurrent requests
    )
