#!/usr/bin/env python
import os
import sys
import time
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load .env config
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_FILE = os.path.join(BASE_DIR, ".env")

if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)
    print(f"✅ Loaded .env from: {ENV_FILE}")
else:
    print(f"❌ .env file not found at: {ENV_FILE}")

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Import CrewAI
try:
    from crewai import Agent, Crew, Process, Task, LLM as CrewLLM
    CREWAI_AVAILABLE = True
    print("✅ CrewAI imported successfully")
except ImportError as e:
    print(f"❌ CrewAI import failed: {e}")
    CREWAI_AVAILABLE = False

# Setup Gemini with correct model name
GEMINI_KEY = os.getenv('GOOGLE_API_KEY')
MODEL_NAME = "gemini-1.5-flash"  # ✅ Using standard flash model (more reliable than lite)
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"
LLM = None

def init_llm():
    """Initialize LLM without testing to conserve quota"""
    global LLM
    if not GEMINI_KEY:
        print("❌ GOOGLE_API_KEY not found in environment")
        return
    
    if not GEMINI_KEY.startswith('AIza'):
        print(f"❌ Invalid API key format")
        return
    
    print(f"🔑 API Key found: {GEMINI_KEY[:20]}...")
    print(f"⚠️  Skipping initial API test to conserve quota")
    
    # Initialize CrewAI LLM directly without testing
    try:
        print(f"🔄 Initializing CrewAI LLM with gemini/{MODEL_NAME}...")
        LLM = CrewLLM(
            model=f"gemini/{MODEL_NAME}",
            api_key=GEMINI_KEY,
            temperature=0.7
        )
        print("✅ CrewAI LLM initialized successfully!")
    except Exception as e:
        print(f"❌ CrewAI LLM init failed: {e}")
        LLM = None

init_llm()

# Rate limiting - increased to avoid quota issues
LAST_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 15  # ✅ 15 seconds between requests

def rate_limit():
    """Rate limiting to avoid API quota exhaustion"""
    global LAST_REQUEST_TIME
    elapsed = time.time() - LAST_REQUEST_TIME
    if elapsed < MIN_REQUEST_INTERVAL:
        wait_time = MIN_REQUEST_INTERVAL - elapsed
        print(f"⏳ Rate limiting: waiting {wait_time:.1f}s...")
        time.sleep(wait_time)
    LAST_REQUEST_TIME = time.time()

def call_gemini_api(prompt):
    """Call Gemini API directly with HTTP request"""
    try:
        response = requests.post(
            GEMINI_API_URL,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            params={"key": GEMINI_KEY},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            return "⚠️ Rate limit exceeded. Please wait a few minutes and try again. Check your quota at: https://ai.dev/usage"
        else:
            print(f"API Error: {response.status_code}")
            error_msg = response.json()
            print(error_msg)
            return f"API Error: {error_msg.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        print(f"❌ API call error: {e}")
        return f"Error: {str(e)}"

def create_agents(llm):
    """Create AI agents with reduced iterations"""
    return [
        Agent(
            role="Senior Patent Analyst",
            goal="Analyze patentability and provide comprehensive patent strategy",
            backstory="Expert patent analyst with 15+ years of experience in technology patents",
            verbose=True,
            llm=llm,
            max_iter=2,  # ✅ Reduced to minimize API calls
            allow_delegation=False
        ),
        Agent(
            role="Senior Trademark Attorney",
            goal="Check trademark availability and conflicts",
            backstory="Experienced trademark attorney specializing in brand protection",
            verbose=True,
            llm=llm,
            max_iter=2,
            allow_delegation=False
        ),
        Agent(
            role="IP Valuation Director",
            goal="Estimate IP value and market potential",
            backstory="Financial expert in IP valuation with background in venture capital",
            verbose=True,
            llm=llm,
            max_iter=2,
            allow_delegation=False
        ),
    ]

def create_tasks(data, agents):
    """Create tasks for all agents"""
    patent_agent, trademark_agent, valuation_agent = agents
    
    tasks = [
        Task(
            description=f"""ANALYZE PATENTABILITY FOR: {data['technology_description']}

Provide comprehensive analysis including:
1. Novelty and utility assessment
2. Unique aspects and differentiators
3. Patent claims strategy
4. Filing recommendations (provisional vs non-provisional)
5. Potential challenges and solutions
6. International protection considerations

Format with clear sections and bullet points.""",
            expected_output="Detailed patent analysis report with actionable recommendations",
            agent=patent_agent
        ),
        Task(
            description=f"""CHECK TRADEMARK AVAILABILITY FOR: {data['trademark_name']}
Industry: {data['market_description']}

Analyze:
1. Potential conflicts with existing trademarks
2. Distinctiveness and protectability
3. International considerations
4. Recommended trademark classes
5. Risk assessment and mitigation strategies

Provide clear guidance on trademark viability.""",
            expected_output="Trademark conflict analysis with risk assessment",
            agent=trademark_agent
        ),
        Task(
            description=f"""ESTIMATE IP VALUE FOR:
Technology: {data['technology_description']}
Market: {data['market_description']}
Revenue: {data['estimated_revenue']}

Provide:
1. IP portfolio valuation estimate
2. Market opportunity analysis
3. Revenue potential from IP licensing
4. Competitive advantage assessment
5. Investment recommendations

Include both conservative and optimistic scenarios.""",
            expected_output="IP valuation report with financial projections",
            agent=valuation_agent
        ),
    ]
    
    return tasks

@app.route('/')
def index():
    """Serve main interface"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'crewai_available': CREWAI_AVAILABLE,
        'llm_available': LLM is not None,
        'model': MODEL_NAME,
        'quota_info': 'Check usage at: https://ai.dev/usage'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Simple chat endpoint for the chatbot interface"""
    if not GEMINI_KEY:
        return jsonify({
            'success': False, 
            'error': 'AI system not available. Please check API key configuration.'
        }), 500
    
    data = request.json or {}
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    rate_limit()
    
    try:
        prompt = f"""You are an expert IP Strategy Assistant helping with intellectual property questions.

User Question: {user_message}

Provide a helpful, professional response about IP strategy, patents, trademarks, or related topics.
Keep your response concise but informative (under 200 words)."""

        response = call_gemini_api(prompt)
        
        if response:
            return jsonify({
                'success': True,
                'response': response,
                'model_used': MODEL_NAME
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to get response from AI'
            }), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'Error: {str(e)}'
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """Main IP analysis endpoint - SIMPLIFIED VERSION using direct Gemini API"""
    print(f"🔍 /analyze endpoint called")
    print(f"🔍 GEMINI_KEY available: {bool(GEMINI_KEY)}")
    
    if not GEMINI_KEY:
        return jsonify({
            'success': False, 
            'error': 'AI system not available. Please check your configuration and API quota at https://ai.dev/usage'
        }), 500

    data = request.json or {}
    print(f"🔍 Request data received: {data}")
    
    required_fields = [
        'technology_description', 
        'trademark_name', 
        'market_description', 
        'estimated_revenue', 
        'budget', 
        'timeline', 
        'competitor_list'
    ]
    missing = [f for f in required_fields if not data.get(f)]
    
    if missing:
        return jsonify({
            'error': f'Missing fields: {", ".join(missing)}'
        }), 400

    rate_limit()

    try:
        print("\n" + "="*60)
        print("🚀 Starting IP analysis using Gemini API...")
        print("="*60)
        
        # Use simplified approach with direct Gemini API (same as /chat)
        prompt = f"""You are an expert IP Portfolio Strategist. Analyze this intellectual property portfolio:

TECHNOLOGY DESCRIPTION:
{data['technology_description']}

TRADEMARK NAME:
{data['trademark_name']}

TARGET MARKET:
{data['market_description']}

ESTIMATED REVENUE POTENTIAL:
{data['estimated_revenue']}

BUDGET FOR IP PROTECTION:
{data['budget']}

TIMELINE:
{data['timeline']}

COMPETITORS:
{data['competitor_list']}

Provide a comprehensive IP strategy analysis covering:

1. PATENT ANALYSIS:
   - Novelty and patentability assessment
   - Recommended patent strategy
   - Potential challenges and solutions
   - International filing considerations

2. TRADEMARK ANALYSIS:
   - Availability and conflict check
   - Distinctiveness assessment
   - Recommended trademark classes
   - Risk mitigation strategies

3. IP VALUATION:
   - Estimated portfolio value
   - Market opportunity analysis
   - Revenue projection from licensing
   - Investment attractiveness

4. STRATEGIC RECOMMENDATIONS:
   - Prioritized action plan
   - Budget allocation recommendations
   - Timeline with milestones
   - Risk assessment

Format your response with clear headings, bullet points, and actionable insights.
Keep it professional but concise."""

        print(f"⚙️ Calling Gemini API with prompt (length: {len(prompt)} chars)...")
        result = call_gemini_api(prompt)
        
        print("="*60)
        print("✅ Analysis complete!")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'result': result,
            'model_used': MODEL_NAME,
            'note': 'Analysis performed using direct Gemini API'
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ Analysis failed with error:\n{error_trace}")
        
        # Check if it's a quota error
        error_str = str(e)
        if '429' in error_str or 'quota' in error_str.lower() or 'RESOURCE_EXHAUSTED' in error_str:
            return jsonify({
                'success': False, 
                'error': 'API quota exceeded. Please wait a few minutes and try again. Check your usage at: https://ai.dev/usage'
            }), 429
        
        return jsonify({
            'success': False, 
            'error': f'Analysis failed: {str(e)[:200]}'
        }), 500

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting Flask app on port {port}...")
    print(f"🔧 CrewAI Available: {CREWAI_AVAILABLE}")
    print(f"🔧 LLM Available: {LLM is not None}")
    print(f"🔧 Google API Key: {'✅' if GEMINI_KEY else '❌'}")
    app.run(host='0.0.0.0', port=port, debug=True)
