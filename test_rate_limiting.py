"""
Test script for rate limiting functionality
"""
import requests
import time
import asyncio

def test_rate_limiting():
    """Test rate limiting on local FastAPI server"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Rate Limiting Functionality")
    print("=" * 50)
    
    # Test health endpoint (should have high limit)
    print("\n1. Testing Health Endpoint (120/minute limit)")
    for i in range(5):
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            print(f"   Request {i+1}: Status {response.status_code}")
            if 'X-RateLimit-Limit' in response.headers:
                print(f"   Rate Limit Headers: {response.headers.get('X-RateLimit-Limit')}/{response.headers.get('X-RateLimit-Window')}s")
        except requests.exceptions.RequestException as e:
            print(f"   Request {i+1}: Failed - {e}")
        time.sleep(0.5)
    
    # Test token extraction endpoint (should have low limit)
    print("\n2. Testing Token Extraction Endpoint (3/minute limit)")
    print("   Note: This will fail due to invalid credentials, but we're testing rate limiting")
    
    test_payload = {
        "credentials": {
            "user_login": "test_user",
            "password": "test_password",
            "mfa_code": "123456"
        }
    }
    
    for i in range(5):
        try:
            response = requests.post(
                f"{base_url}/api/token/extract", 
                json=test_payload,
                timeout=10
            )
            print(f"   Request {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                print(f"   ✅ Rate limit triggered: {response.json()}")
                break
            elif 'X-RateLimit-Limit' in response.headers:
                print(f"   Rate Limit Headers: {response.headers.get('X-RateLimit-Limit')}/{response.headers.get('X-RateLimit-Window')}s")
        except requests.exceptions.RequestException as e:
            print(f"   Request {i+1}: Failed - {e}")
        
        time.sleep(1)  # Wait 1 second between requests
    
    print("\n✅ Rate limiting test completed")
    print("💡 If rate limiting is working, you should see:")
    print("   - Rate limit headers in responses")
    print("   - HTTP 429 status after exceeding limits")

if __name__ == "__main__":
    print("Starting rate limiting test...")
    print("Make sure FastAPI server is running on localhost:8000")
    
    try:
        test_rate_limiting()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure the FastAPI server is running: python -m uvicorn main:app --host 0.0.0.0 --port 8000")