# test_server.py
import socket
import requests
import json

def get_all_ips():
    """Get all non-localhost IPs"""
    ips = []
    for interface in socket.getaddrinfo(socket.gethostname(), None):
        ip = interface[4][0]
        if not ip.startswith('127.') and not ip.startswith('169.254.'):
            ips.append(ip)
    return list(set(ips))

def test_server(ip, port=5000):
    """Test server connection"""
    print(f"\n🔍 Testing server on {ip}:{port}")
    
    # Test GET
    try:
        url = f"http://{ip}:{port}/api/live-open"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            print(f"✅ GET Success: {response.json()}")
            
            # Test POST
            post_url = f"http://{ip}:{port}/api/ingest"
            post_data = {
                "mac": "AA:BB:CC:DD:EE:01",
                "rssi": -65,
                "tsUtc": "2024-01-15T10:30:00Z"
            }
            post_response = requests.post(post_url, json=post_data, timeout=3)
            print(f"✅ POST Success: {post_response.json()}")
            
            return True
        else:
            print(f"❌ GET Failed: Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed: Server not reachable")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 BLE SERVER DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Get all IPs
    all_ips = get_all_ips()
    print(f"Found IPs: {all_ips}")
    
    # Test each IP
    results = {}
    for ip in all_ips:
        results[ip] = test_server(ip)
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY:")
    print("=" * 60)
    
    for ip, success in results.items():
        status = "✅ WORKING" if success else "❌ NOT WORKING"
        print(f"{ip}: {status}")
        
        if success:
            print(f"   📡 URL for RUTX10: http://{ip}:5000/api/ingest")
    
    print("=" * 60)

if __name__ == "__main__":
    main()