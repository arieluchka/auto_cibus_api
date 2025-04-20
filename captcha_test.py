import sys
import os
import time
from internal_data.creds import user_agent
from twocaptcha import TwoCaptcha

api_key = os.getenv('APIKEY_2CAPTCHA', '')
solver = TwoCaptcha(api_key)

def get_captcha_token():
    try:
        print("Requesting captcha token from 2Captcha...")
        
        url = 'https://api.capir.pluxee.co.il/auth/authToken'
        print(f"Using URL: {url}")
        
        result = solver.recaptcha(
            sitekey='6LddY28jAAAAALbiEdodIdIYiM563_AgOW4LMcmu',
            url=url,
            invisible=1,
            userAgent=user_agent,
            cookies="new_site=e0b56031491001d279cc1303da04b0c25540a208a73dcfecfd1f8a90e7897f3b"
        )
        
        print(f"2Captcha result keys: {list(result.keys())}")
        
    except Exception as e:
        sys.exit(f"Error obtaining captcha token: {e}")
    else:
        token = result.get('code')
        if not token:
            sys.exit("Error: no captcha token found in the response.")
        print(f"Captcha token received successfully")
        print(f"Token timestamp: {time.strftime('%H:%M:%S')}")
        print(f"Token length: {len(token)}")
        return token

def try_alternative_urls():
    urls = [
        'https://consumers.pluxee.co.il/login',
        'https://api.capir.pluxee.co.il/auth/authToken', 
        'https://consumers.pluxee.co.il',
        'https://api.consumers.pluxee.co.il'
    ]
    
    print("Testing multiple URLs for captcha validation...")
    
    for url in urls:
        try:
            print(f"\nTrying URL: {url}")
            
            result = solver.recaptcha(
                sitekey='6LddY28jAAAAALbiEdodIdIYiM563_AgOW4LMcmu',
                url=url,
                invisible=1,
                userAgent=user_agent,
                cookies="new_site=e0b56031491001d279cc1303da04b0c25540a208a73dcfecfd1f8a90e7897f3b"
            )
            
            token = result.get('code')
            if token:
                print(f"Success! Token received with URL: {url}")
                print(f"Token length: {len(token)}")
                return token
        except Exception as e:
            print(f"Failed with URL {url}: {e}")
    
    sys.exit("All URLs failed to obtain a valid captcha token")

if __name__ == '__main__':
    token = try_alternative_urls()
    print(f"Final token length: {len(token)}")
    print(f"Token preview: {token[:30]}...")
