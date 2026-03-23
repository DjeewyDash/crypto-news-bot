import urllib.request
import json
import ssl

# TA CLÉ ICI
API_KEY = "AIzaSyAMFBmLmbL68Kv3-6q3i76tJMN_iYo0X0w" # Celle vue sur ta capture

def test_ultra_simple():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={API_KEY}&currencies=ETH"
    
    # On force le Mac à ignorer ses vieux certificats SSL
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # On se déguise en vrai Safari sur Mac M1
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
    }

    print("Vérification en cours...")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
            print("\n✅ CA MARCHE ENFIN !")
            for post in data.get('results', [])[:3]:
                print(f"- {post['title']}")
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")

if __name__ == "__main__":
    test_ultra_simple()
