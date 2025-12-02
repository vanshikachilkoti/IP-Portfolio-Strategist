import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🔧 IP Strategist - Starting Up...")  
    templates_path = os.path.join('templates')
    if not os.path.exists('templates'):
        print("❌ ERROR: templates directory not found")
        return


    
    # Add src to Python path
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    sys.path.insert(0, src_path)

    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    try:
        from ip_strategist.app import app
        
        print("🚀 Starting IP Strategist Application...")
        print("📍 Open: http://localhost:5000")
        print("💬 Smart chatbot enabled")
        print("📊 Portfolio analysis working")
        print("🎯 No API keys required")
        
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

if __name__ == '__main__':
    main()