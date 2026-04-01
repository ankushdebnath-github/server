from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv
from datetime import datetime
import re
import ast

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

# Language-specific code prompts
LANGUAGE_PROMPTS = {
    'python': """You are an expert competitive programmer writing CONTEST CODE in Python.
IMPORTANT: Return ONLY working Python code, nothing else.
- Complete solution that reads from input() and prints output
- Include all necessary imports
- Handle all edge cases from the problem
- Your code must be syntactically valid Python
- NO explanations, NO comments, NO markdown
- Just the code and nothing else""",
    
    'cpp': """You are an expert competitive programmer writing CONTEST CODE in C++.
IMPORTANT: Return ONLY working C++ code, nothing else.
- Complete solution that reads from cin and writes to cout
- Include all necessary headers (#include directives)
- Handle all edge cases from the problem
- Your code must be syntactically valid C++
- NO explanations, NO comments, NO markdown
- Just the code and nothing else""",
    
    'java': """You are an expert competitive programmer writing CONTEST CODE in Java.
IMPORTANT: Return ONLY working Java code, nothing else.
- Complete solution with main() method that reads from System.in and writes to System.out
- Include all necessary imports
- Handle all edge cases from the problem
- Your code must be syntactically valid Java
- NO explanations, NO comments, NO markdown
- Just the code and nothing else""",
    
    'javascript': """You are an expert competitive programmer writing CONTEST CODE in JavaScript.
IMPORTANT: Return ONLY working JavaScript code, nothing else.
- Complete solution that reads from stdin and writes to stdout
- Handle all edge cases from the problem
- Your code must be syntactically valid JavaScript
- NO explanations, NO comments, NO markdown
- Just the code and nothing else""",
    
    'c': """You are an expert competitive programmer writing CONTEST CODE in C.
IMPORTANT: Return ONLY working C code, nothing else.
- Complete solution that reads from stdin and writes to stdout
- Include all necessary headers
- Handle all edge cases from the problem
- Your code must be syntactically valid C
- NO explanations, NO comments, NO markdown
- Just the code and nothing else""",

    'default': """You are an expert competitive programmer writing CONTEST CODE.
IMPORTANT: Return ONLY working code, nothing else.
- Complete solution that reads from input and prints output
- Include all necessary imports
- Handle all edge cases from the problem
- Your code must be syntactically valid
- NO explanations, NO comments, NO markdown
- Just the code and nothing else"""
}

CODE_PROMPT = LANGUAGE_PROMPTS['default']


def strip_code_fences(text):
    """Remove markdown code fences if the model includes them."""
    if not text:
        return ''
    cleaned = text.strip()
    cleaned = re.sub(r'^```[a-zA-Z0-9_+-]*\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    return cleaned.strip()


def looks_like_python_problem(message):
    """Best-effort check if coding response should be valid Python."""
    if not message:
        return False
    m = message.lower()
    hints = ['python', 'pypy', 'def ', 'input format', 'sample input', 'sample output']
    return any(h in m for h in hints)


def detect_programming_language(message):
    """Detect the programming language from problem statement."""
    if not message:
        return 'python'  # Default fallback
    
    message_lower = message.lower()
    
    # Language detection patterns
    language_patterns = {
        'python': ['python', 'pypy', 'python3', 'python2', '.py', 'def ', 'indent'],
        'cpp': ['c++', 'cpp', 'c++ ', '#include', 'iostream', 'cin', 'cout', 'vector<', 'stl', '.cpp'],
        'java': ['java', 'import java', 'public class', 'public static void main', 'scanner', '.java'],
        'javascript': ['javascript', 'js ', 'node', 'console.log', 'function ', '.js', 'const ', 'let '],
        'c': ['c language', ' c ', '#include <stdio.h>', 'scanf', 'printf', '.c ', 'main()'],
        'csharp': ['c#', 'csharp', 'c# ', 'using system', 'console.writeline', '.cs'],
        'golang': ['golang', 'go ', 'package main', 'func main', 'fmt.println', '.go'],
        'ruby': ['ruby', 'ruby on', '.rb ', 'def ', 'puts ', 'require'],
        'php': ['php', '<?php', 'echo ', '<?', 'php '],
        'swift': ['swift', 'swift ', 'func ', 'print(', '.swift'],
        'kotlin': ['kotlin', 'kotlin ', 'fun main', '.kt'],
        'rust': ['rust', 'rust ', 'fn main', 'println!', '.rs'],
        'sql': ['sql', 'select', 'from ', 'where ', 'database']
    }
    
    # Score each language based on keyword matches
    scores = {}
    for lang, patterns in language_patterns.items():
        score = sum(1 for pattern in patterns if pattern in message_lower)
        if score > 0:
            scores[lang] = score
    
    # Return highest scoring language, default to python
    if scores:
        detected_lang = max(scores, key=scores.get)
        print(f'[LANG_DETECT] Language: {detected_lang} (score: {scores[detected_lang]})')
        return detected_lang
    
    print('[LANG_DETECT] No language detected, defaulting to Python')
    return 'python'


def is_incomplete_code(answer, original_message=''):
    """Detect obviously broken/incomplete code answers from the model."""
    if not answer:
        return True

    text = strip_code_fences(answer)
    low = text.lower()
    lines = text.strip().split('\n')

    # Known bad templates/hallucinations.
    bad_markers = [
        '# enter your code here',
        'import read',
        'todo',
        'pass  #',
        'your code here',
        'example:',
        'sample:',
        '```',
        'solution:',
        'here is the code',
        'this code'
    ]
    if any(marker in low for marker in bad_markers):
        print(f'[VALIDATION] Rejected: bad marker found')
        return True

    # Very short outputs are often truncated.
    if len(text) < 80:
        print(f'[VALIDATION] Rejected: too short ({len(text)} chars)')
        return True

    # Must end with a real statement, not incomplete.
    last_line = lines[-1].strip() if lines else ''
    if last_line.endswith(':'):
        print(f'[VALIDATION] Rejected: ends with colon (incomplete block)')
        return True
    if last_line.endswith('='):
        print(f'[VALIDATION] Rejected: ends with equals (incomplete assignment)')
        return True
    if last_line.endswith((',', '\\')):
        print(f'[VALIDATION] Rejected: ends with continuation character')
        return True

    # Unbalanced delimiters are a strong sign of truncation.
    pairs = {'(': ')', '[': ']', '{': '}'}
    stack = []
    for ch in text:
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in (')', ']', '}'):
            if not stack or stack.pop() != ch:
                print(f'[VALIDATION] Rejected: unbalanced delimiters')
                return True
    if stack:
        print(f'[VALIDATION] Rejected: unclosed delimiters')
        return True

    # Must have at least one input() or reading from stdin
    if not any(x in low for x in ['input(', 'stdin', 'read(']):
        if not any(x in low for x in ['sys.argv', 'sys.stdin']):
            print(f'[VALIDATION] Warning: no input() found, but continuing')

    # If this appears to be Python, require syntax-valid code.
    if looks_like_python_problem(original_message):
        try:
            ast.parse(text)
            print(f'[VALIDATION] Passed: syntax valid')
        except SyntaxError as e:
            print(f'[VALIDATION] Rejected: syntax error - {e}')
            return True

    return False

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
    code_indicators = [
        'code', 'function', 'def ', 'class ', 'print(', 'sql', 'section 2',
        'input format', 'output format', 'sample input', 'sample output',
        'constraints', 'stdin', 'stdout', 'hackerrank', 'collections.counter'
    ]
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
        
        # Prefer explicit type from client hotkey mode when available.
        forced_type = str(data.get('question_type', '')).strip().lower()
        if forced_type in ('code', 'mcq'):
            q_type = forced_type
        else:
            q_type = detect_question_type(message)
        
        # Detect programming language for code problems
        detected_language = 'python'
        if q_type == 'code':
            # Check if user forced a language selection
            forced_lang = str(data.get('forced_language', '')).strip().lower()
            if forced_lang in ('python', 'cpp', 'java', 'javascript', 'c', 'csharp', 'golang', 'ruby', 'php', 'swift', 'kotlin', 'rust', 'sql'):
                detected_language = forced_lang
                print(f'[LANG] Using forced language: {forced_lang}')
            else:
                detected_language = detect_programming_language(message)
            
            system_prompt = LANGUAGE_PROMPTS.get(detected_language, LANGUAGE_PROMPTS['default'])
        else:
            system_prompt = MCQ_PROMPT
        
        logger.info(f'[{hwid[:8]}...] Type: {q_type}, Language: {detected_language}, Chars: {len(message)}')
        
        # Call Gemini with system prompt
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')

            response = model.generate_content(
                f"{system_prompt}\n\n{message}",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2200,
                    temperature=0.1 if q_type == 'mcq' else 0.05
                )
            )

            answer = strip_code_fences(response.text.strip())

            if q_type == 'code' and is_incomplete_code(answer, message):
                logger.warning(f'⚠️ Incomplete code detected for {hwid[:8]}... ({detected_language}), retrying with stricter prompt')
                
                # Language-specific repair prompts
                if detected_language == 'cpp':
                    repair_prompt = (
                        f"SOLVE THIS CODING PROBLEM IN C++ ONLY.\n\n"
                        f"{message}\n\n"
                        f"Write ONLY complete C++ code. Nothing else.\n"
                        f"- Read input with cin\n"
                        f"- Print output with cout\n"
                        f"- Include all #include directives\n"
                        f"- Must be syntactically valid C++\n"
                        f"- No comments. No explanations.\n"
                        f"Code:"
                    )
                elif detected_language == 'java':
                    repair_prompt = (
                        f"SOLVE THIS CODING PROBLEM IN JAVA ONLY.\n\n"
                        f"{message}\n\n"
                        f"Write ONLY complete Java code with main() method. Nothing else.\n"
                        f"- Read input from System.in\n"
                        f"- Print output to System.out\n"
                        f"- Include all necessary imports\n"
                        f"- Must be syntactically valid Java\n"
                        f"- No comments. No explanations.\n"
                        f"Code:"
                    )
                elif detected_language == 'javascript':
                    repair_prompt = (
                        f"SOLVE THIS CODING PROBLEM IN JAVASCRIPT ONLY.\n\n"
                        f"{message}\n\n"
                        f"Write ONLY complete JavaScript code. Nothing else.\n"
                        f"- Read input from stdin\n"
                        f"- Print output to stdout\n"
                        f"- Must be syntactically valid JavaScript\n"
                        f"- No comments. No explanations.\n"
                        f"Code:"
                    )
                else:  # Python or default
                    repair_prompt = (
                        f"SOLVE THIS CODING PROBLEM IN PYTHON ONLY.\n\n"
                        f"{message}\n\n"
                        f"Write ONLY the complete Python code. Nothing else.\n"
                        f"- Read input with input()\n"
                        f"- Print the output\n"
                        f"- Must be syntactically valid\n"
                        f"- No comments. No explanations.\n"
                        f"Code:"
                    )
                
                retry_response = model.generate_content(
                    repair_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=2500,
                        temperature=0.02
                    )
                )
                answer = strip_code_fences(retry_response.text.strip())
                logger.info(f'[Retry] Got {len(answer)} chars for {detected_language}')

            if not answer:
                return jsonify({'success': False, 'error': 'Empty response'}), 500

            elapsed = time.time() - start_time
            logger.info(f'✅ [{hwid[:8]}...] Answer: {len(answer)} chars, {elapsed:.2f}s')

            return jsonify({
                'success': True,
                'answer': answer,
                'type': q_type,
                'language': detected_language if q_type == 'code' else 'n/a',
                'stats': {
                    'limit': MAX_REQUESTS_PER_DAY,
                    'used': rate_limits[get_rate_limit_key(hwid)]['used'],
                    'response_time': round(elapsed, 2)
                }
            }), 200

        except Exception as e:
            err_str = str(e)
            logger.error(f'❌ LLM error: {err_str}')

            # Detect common quota/429 patterns from the LLM provider and return 429 with Retry-After
            low = err_str.lower()
            if '429' in err_str or 'quota' in low or 'exceeded your current quota' in low:
                retry_after = 60
                logger.warning(f'🔁 LLM quota exceeded for {hwid[:8]}..., returning 429')
                return (jsonify({'success': False, 'error': 'LLM quota exceeded. Check billing/plan.'}),
                        429,
                        {'Retry-After': str(retry_after)})

            return jsonify({'success': False, 'error': f'LLM error: {err_str[:200]}'}), 500
    
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
