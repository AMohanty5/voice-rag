"""
Grafana Cloud Authentication Test Script

This script helps you verify your Grafana Cloud credentials are configured correctly.
"""

import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_grafana_config():
    """Test Grafana Cloud configuration"""
    
    print("=" * 80)
    print("🔍 Grafana Cloud Configuration Test")
    print("=" * 80)
    print()
    
    # Check endpoint
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    print(f"📊 Endpoint: {endpoint}")
    
    if not endpoint:
        print("❌ ERROR: OTEL_EXPORTER_OTLP_ENDPOINT not set in .env")
        return False
    elif "otlp-gateway" not in endpoint:
        print("⚠️  WARNING: Endpoint doesn't look like a Grafana OTLP endpoint")
    else:
        print("✅ Endpoint looks good")
    
    print()
    
    # Check headers
    headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    print(f"🔑 Headers: {headers[:50]}..." if headers and len(headers) > 50 else f"🔑 Headers: {headers}")
    
    if not headers:
        print("❌ ERROR: OTEL_EXPORTER_OTLP_HEADERS not set in .env")
        return False
    
    # Check for common issues
    issues = []
    
    if not headers.startswith("Authorization="):
        issues.append("❌ Headers should start with 'Authorization='")
    
    if "Basic " not in headers:
        issues.append("❌ Headers should contain 'Basic ' (with space)")
    
    if "%20" in headers:
        issues.append("❌ Remove %20 from .env file - use space instead")
    
    if "Basic%20" in headers:
        issues.append("❌ Change 'Basic%20' to 'Basic ' (space instead of %20)")
    
    if issues:
        print()
        for issue in issues:
            print(issue)
        print()
        print("💡 Fix: Update your .env file:")
        print("   OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <your_base64_token>")
        print("   (Use a SPACE between 'Basic' and your token)")
        return False
    
    print("✅ Header format looks good")
    print()
    
    # Try to decode credentials
    try:
        # Extract the Base64 part
        auth_part = headers.replace("Authorization=", "").replace("Basic ", "").strip()
        
        print(f"🔐 Base64 Token (first 30 chars): {auth_part[:30]}...")
        print()
        
        # Decode
        decoded = base64.b64decode(auth_part).decode('utf-8')
        
        # Check format
        if ":" in decoded:
            parts = decoded.split(":", 1)
            instance_id = parts[0]
            token_preview = parts[1][:20] if len(parts) > 1 else "N/A"
            
            print("✅ Credentials decoded successfully!")
            print(f"   Instance ID: {instance_id}")
            print(f"   Token (first 20 chars): {token_preview}...")
            print()
            
            # Validate format
            if not instance_id.isdigit():
                print("⚠️  WARNING: Instance ID should be numeric")
            
            if not token_preview.startswith("glc_"):
                print("⚠️  WARNING: Token should start with 'glc_'")
            
            print("=" * 80)
            print("✅ Configuration Test PASSED")
            print("=" * 80)
            print()
            print("Next steps:")
            print("1. Run your bot: uv run bot.py")
            print("2. Check logs for: '✅ OpenTelemetry configured for Grafana Cloud'")
            print("3. Verify no authentication errors appear")
            print()
            return True
            
        else:
            print("❌ ERROR: Decoded credentials don't contain ':' separator")
            print(f"   Decoded value: {decoded[:50]}...")
            print()
            print("💡 Credentials should be Base64 encoded in format: instance_id:token")
            print("   Example: 1598636:glc_eyJvIjoiMTU5ODYzNiIsIm4iOiJwaXBlY2F0...")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to decode credentials: {e}")
        print()
        print("💡 Make sure your token is properly Base64 encoded")
        print("   Format: Base64(instance_id:token)")
        return False

if __name__ == "__main__":
    success = test_grafana_config()
    
    if not success:
        print()
        print("=" * 80)
        print("❌ Configuration Test FAILED")
        print("=" * 80)
        print()
        print("📚 See GRAFANA_AUTH_TROUBLESHOOTING.md for detailed help")
        print()
        exit(1)
