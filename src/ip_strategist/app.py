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
MODEL_NAME = "gemini-2.5-flash-lite"  # ✅ Using lite version for better free tier limits
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
        # Agent(
        #     role="Chief IP Strategist",
        #     goal="Develop comprehensive IP protection strategy",
        #     backstory="Strategic IP consultant who has advised Fortune 500 companies",
        #     verbose=True,
        #     llm=llm,
        #     max_iter=2,
        #     allow_delegation=False
        # ),
        # Agent(
        #     role="Competitive Intelligence Director",
        #     goal="Analyze competitor IP landscape",
        #     backstory="Intelligence analyst specialized in competitive IP monitoring",
        #     verbose=True,
        #     llm=llm,
        #     max_iter=2,
        #     allow_delegation=False
        # ),
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
#         Task(
#             description=f"""DEVELOP IP FILING STRATEGY:
# Budget: {data['budget']}
# Timeline: {data['timeline']}
# Technology: {data['technology_description']}
# Market: {data['market_description']}

# Create strategic plan including:
# 1. Prioritized filing recommendations
# 2. Budget allocation across IP types
# 3. Timeline with milestones
# 4. Geographic filing strategy
# 5. Risk mitigation approaches
# 6. Cost-benefit analysis

# Provide a clear roadmap for IP protection.""",
#             expected_output="Comprehensive IP filing strategy with timeline and budget breakdown",
#             agent=strategy_agent
#         ),
#         Task(
#             description=f"""ANALYZE COMPETITOR IP LANDSCAPE:
# Competitors: {data['competitor_list']}
# Technology: {data['technology_description']}

# Research and report on:
# 1. Competitor patent portfolios
# 2. Potential IP conflicts
# 3. White space opportunities
# 4. Freedom to operate assessment
# 5. Strategic positioning recommendations
# 6. Monitoring recommendations

# Provide actionable competitive intelligence.""",
#             expected_output="Competitive IP analysis with strategic recommendations",
#             agent=competitor_agent
#         ),
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
def analyze_ip():
    """Main IP analysis endpoint"""
    if not CREWAI_AVAILABLE or not LLM:
        return jsonify({
            'success': False, 
            'error': 'AI system not available. Please check your configuration and API quota at https://ai.dev/usage'
        }), 500

    data = request.json or {}
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
        print("🚀 Starting IP analysis...")
        print("="*60)
        
        agents = create_agents(LLM)
        tasks = create_tasks(data, agents)

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        print("⚙️ Running crew analysis (this may take several minutes)...")
        result = crew.kickoff()
        
        print("="*60)
        print("✅ Analysis complete!")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'result': str(result),
            'model_used': MODEL_NAME
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

# if __name__ == "__main__":
#     print("\n" + "="*60)
#     print("🚀 IP STRATEGIST STARTING")
#     print("="*60)
#     print(f"📊 CrewAI Available: {CREWAI_AVAILABLE}")
#     print(f"🤖 LLM Available: {LLM is not None}")
#     print(f"🔮 Model: {MODEL_NAME}")
#     print(f"⏱️  Rate Limit: {MIN_REQUEST_INTERVAL}s between requests")
#     print(f"📈 Check quota: https://ai.dev/usage")
#     print("="*60 + "\n")
    
#     app.run(host='0.0.0.0', port=5000, debug=True)



# #!/usr/bin/env python
# import os
# import time
# import requests
# from flask import Flask, render_template, request, jsonify
# from dotenv import load_dotenv

# # ----------------------------
# # Load .env config
# # ----------------------------
# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# ENV_FILE = os.path.join(BASE_DIR, ".env")

# if os.path.exists(ENV_FILE):
#     load_dotenv(ENV_FILE)
#     print(f"✅ Loaded .env from: {ENV_FILE}")
# else:
#     print(f"❌ .env file not found at: {ENV_FILE}")

# # ----------------------------
# # Flask app setup
# # ----------------------------
# app = Flask(__name__)
# app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# # ----------------------------
# # Import CrewAI (optional)
# # ----------------------------
# try:
#     from crewai import Agent, Crew, Process, Task, LLM as CrewLLM
#     CREWAI_AVAILABLE = True
#     print("✅ CrewAI imported successfully")
# except Exception as e:
#     print(f"❌ CrewAI import failed: {e}")
#     CREWAI_AVAILABLE = False

# # ----------------------------
# # Gemini / LLM setup
# # ----------------------------
# GEMINI_KEY = os.getenv('GOOGLE_API_KEY')
# MODEL_NAME = "gemini-2.5-flash-lite"
# GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"
# LLM = None

# def init_llm():
#     """Initialize CrewAI-backed LLM (no test call to conserve quota)."""
#     global LLM
#     if not GEMINI_KEY:
#         print("❌ GOOGLE_API_KEY not found in environment")
#         return

#     if not GEMINI_KEY.startswith('AIza'):
#         print("❌ Invalid API key format")
#         return

#     print(f"🔑 API Key found: {GEMINI_KEY[:20]}...")
#     print("⚠️  Skipping initial API test to conserve quota")
#     try:
#         print(f"🔄 Initializing CrewAI LLM with gemini/{MODEL_NAME}...")
#         LLM = CrewLLM(model=f"gemini/{MODEL_NAME}", api_key=GEMINI_KEY, temperature=0.7)
#         print("✅ CrewAI LLM initialized successfully!")
#     except Exception as e:
#         print(f"❌ CrewAI LLM init failed: {e}")
#         LLM = None

# init_llm()

# # ----------------------------
# # Rate limiting
# # ----------------------------
# LAST_REQUEST_TIME = 0
# MIN_REQUEST_INTERVAL = 15  # seconds

# def rate_limit():
#     """Rate limiting to avoid API quota exhaustion"""
#     global LAST_REQUEST_TIME
#     elapsed = time.time() - LAST_REQUEST_TIME
#     if elapsed < MIN_REQUEST_INTERVAL:
#         wait_time = MIN_REQUEST_INTERVAL - elapsed
#         print(f"⏳ Rate limiting: waiting {wait_time:.1f}s...")
#         time.sleep(wait_time)
#     LAST_REQUEST_TIME = time.time()

# # ----------------------------
# # Gemini API caller
# # ----------------------------
# def call_gemini_api(prompt):
#     """Call Gemini API directly with HTTP request (simple wrapper)."""
#     try:
#         response = requests.post(
#             GEMINI_API_URL,
#             json={"contents": [{"parts": [{"text": prompt}]}]},
#             params={"key": GEMINI_KEY},
#             headers={"Content-Type": "application/json"},
#             timeout=30
#         )
#         if response.status_code == 200:
#             result = response.json()
#             return result['candidates'][0]['content']['parts'][0]['text']
#         elif response.status_code == 429:
#             return "⚠️ Rate limit exceeded. Please wait a few minutes and try again. Check your quota at: https://ai.dev/usage"
#         else:
#             print(f"API Error: {response.status_code}")
#             try:
#                 error_msg = response.json()
#                 print(error_msg)
#                 return f"API Error: {error_msg.get('error', {}).get('message', 'Unknown error')}"
#             except Exception:
#                 return f"API Error: {response.status_code}"
#     except Exception as e:
#         print(f"❌ API call error: {e}")
#         return f"Error: {str(e)}"

# # ----------------------------
# # Output refinement helper
# # ----------------------------
# def refine_output(raw_text: str, short: bool = True) -> str:
#     """
#     Use Gemini to clean the raw agent output:
#     - remove chain-of-thought
#     - remove internal reasoning
#     - produce a concise, well-formatted report (headers, bullets)
#     """
#     if not GEMINI_KEY:
#         # If no API key, return raw text (best-effort)
#         return raw_text

#     # Keep the refinement prompt strict and prescriptive.
#     length_directive = "Keep it to one page, concise." if short else "Keep it concise and well-structured."
#     prompt = f"""
# You are an expert editor. Clean and refine the following AI output.

# Rules:
# - REMOVE any chain-of-thought, internal reasoning, or 'thinking' statements.
# - DO NOT include the LLM's thought process or how the answer was produced.
# - FORMAT the output with clear headers, short paragraphs, and bullets where helpful.
# - BE CONCISE and professional. {length_directive}
# - Keep technical assertions, numbers, and recommendations intact.
# - Do not call out that you removed reasoning.

# CONTENT:
# {raw_text}
# """

#     refined = call_gemini_api(prompt)
#     # Fallback: if the model returned an error message, or is identical/empty, return raw_text trimmed.
#     if not refined or "API Error" in refined or "Rate limit exceeded" in refined:
#         return raw_text.strip()
#     return refined.strip()

# # ----------------------------
# # CrewAI agents & tasks
# # ----------------------------
# def create_agents(llm):
#     """Create AI agents with reduced iterations to save quota."""
#     return [
#         Agent(
#             role="Senior Patent Analyst",
#             goal="Analyze patentability and provide comprehensive patent strategy",
#             backstory="Expert patent analyst with 15+ years of experience in technology patents",
#             verbose=True,
#             llm=llm,
#             max_iter=2,
#             allow_delegation=False
#         ),
#         Agent(
#             role="Senior Trademark Attorney",
#             goal="Check trademark availability and conflicts",
#             backstory="Experienced trademark attorney specializing in brand protection",
#             verbose=True,
#             llm=llm,
#             max_iter=2,
#             allow_delegation=False
#         ),
#         Agent(
#             role="IP Valuation Director",
#             goal="Estimate IP value and market potential",
#             backstory="Financial expert in IP valuation with background in venture capital",
#             verbose=True,
#             llm=llm,
#             max_iter=2,
#             allow_delegation=False
#         ),
#     ]

# def create_tasks(data, agents):
#     """Create tasks for all agents"""
#     patent_agent, trademark_agent, valuation_agent = agents

#     tasks = [
#         Task(
#             description=f"""ANALYZE PATENTABILITY FOR: {data['technology_description']}

# Provide comprehensive analysis including:
# 1. Novelty and utility assessment
# 2. Unique aspects and differentiators
# 3. Patent claims strategy
# 4. Filing recommendations (provisional vs non-provisional)
# 5. Potential challenges and solutions
# 6. International protection considerations

# Format with clear sections and bullet points.""",
#             expected_output="Detailed patent analysis report with actionable recommendations",
#             agent=patent_agent
#         ),
#         Task(
#             description=f"""CHECK TRADEMARK AVAILABILITY FOR: {data['trademark_name']}
# Industry: {data['market_description']}

# Analyze:
# 1. Potential conflicts with existing trademarks
# 2. Distinctiveness and protectability
# 3. International considerations
# 4. Recommended trademark classes
# 5. Risk assessment and mitigation strategies

# Provide clear guidance on trademark viability.""",
#             expected_output="Trademark conflict analysis with risk assessment",
#             agent=trademark_agent
#         ),
#         Task(
#             description=f"""ESTIMATE IP VALUE FOR:
# Technology: {data['technology_description']}
# Market: {data['market_description']}
# Revenue: {data['estimated_revenue']}

# Provide:
# 1. IP portfolio valuation estimate
# 2. Market opportunity analysis
# 3. Revenue potential from IP licensing
# 4. Competitive advantage assessment
# 5. Investment recommendations

# Include both conservative and optimistic scenarios.""",
#             expected_output="IP valuation report with financial projections",
#             agent=valuation_agent
#         ),
#     ]
#     return tasks

# # ----------------------------
# # Flask routes
# # ----------------------------
# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/health')
# def health():
#     return jsonify({
#         'status': 'healthy',
#         'crewai_available': CREWAI_AVAILABLE,
#         'llm_available': LLM is not None,
#         'model': MODEL_NAME,
#         'quota_info': 'Check usage at: https://ai.dev/usage'
#     })

# @app.route('/chat', methods=['POST'])
# def chat():
#     """Simple chat endpoint for short IP Q&A"""
#     if not GEMINI_KEY:
#         return jsonify({'success': False, 'error': 'AI system not available. Check API key.'}), 500

#     data = request.json or {}
#     user_message = data.get('message', '').strip()
#     if not user_message:
#         return jsonify({'error': 'No message provided'}), 400

#     rate_limit()
#     try:
#         prompt = f"""You are an expert IP Strategy Assistant.

# User Question: {user_message}

# Give a concise, professional answer (<= 200 words)."""
#         response = call_gemini_api(prompt)
#         if response:
#             return jsonify({'success': True, 'response': response.strip(), 'model_used': MODEL_NAME})
#         return jsonify({'success': False, 'error': 'Failed to get response from AI'}), 500
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500

# @app.route('/analyze', methods=['POST'])
# def analyze_ip():
#     """Main IP analysis endpoint - runs Crew, then refines output."""
#     if not CREWAI_AVAILABLE or not LLM:
#         return jsonify({
#             'success': False,
#             'error': 'AI system not available. Please check your configuration and API quota at https://ai.dev/usage'
#         }), 500

#     data = request.json or {}
#     required_fields = [
#         'technology_description',
#         'trademark_name',
#         'market_description',
#         'estimated_revenue',
#         'budget',
#         'timeline',
#         'competitor_list'
#     ]
#     missing = [f for f in required_fields if not data.get(f)]
#     if missing:
#         return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

#     rate_limit()

#     try:
#         print("\n" + "="*60)
#         print("🚀 Starting IP analysis...")
#         print("="*60)

#         agents = create_agents(LLM)
#         tasks = create_tasks(data, agents)

#         crew = Crew(
#             agents=agents,
#             tasks=tasks,
#             process=Process.sequential,
#             verbose=True
#         )

#         print("⚙️ Running crew analysis (this may take a while)...")
#         raw_result = crew.kickoff()
#         raw_text = str(raw_result).strip()

#         print("="*60)
#         print("✅ Analysis complete!")
#         print("="*60 + "\n")

#         # ----------------------------
#         # REFINE the raw output to remove chain-of-thought and make it concise
#         # ----------------------------
#         refined = refine_output(raw_text, short=True)

#         return jsonify({
#             'success': True,
#             'result_raw': raw_text,
#             'result_refined': refined,
#             'model_used': MODEL_NAME
#         })

#     except Exception as e:
#         import traceback
#         error_trace = traceback.format_exc()
#         print(f"\n❌ Analysis failed with error:\n{error_trace}")

#         error_str = str(e)
#         if '429' in error_str or 'quota' in error_str.lower() or 'RESOURCE_EXHAUSTED' in error_str:
#             return jsonify({
#                 'success': False,
#                 'error': 'API quota exceeded. Please wait and try again. Check your usage at: https://ai.dev/usage'
#             }), 429

#         return jsonify({'success': False, 'error': f'Analysis failed: {str(e)[:200]}'}), 500

# # ----------------------------
# # Run app
# # ----------------------------
# if __name__ == "__main__":
#     print("\n" + "="*60)
#     print("🚀 IP STRATEGIST STARTING")
#     print("="*60)
#     print(f"📊 CrewAI Available: {CREWAI_AVAILABLE}")
#     print(f"🤖 LLM Available: {LLM is not None}")
#     print(f"🔮 Model: {MODEL_NAME}")
#     print(f"⏱️ Rate Limit: {MIN_REQUEST_INTERVAL}s between requests")
#     print(f"📈 Check quota: https://ai.dev/usage")
#     print("="*60 + "\n")

#     app.run(host='0.0.0.0', port=5000, debug=True)
