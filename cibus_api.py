import time
import requests
import json

from additional_data import authorization_url, data_url, app_id, call_types
from internal_data.creds import user_agent


def check_if_work_day():
    return time.strftime("%A") in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

def check_before_seven_pm_israel_time():
    israel_time = time.gmtime(time.time() + 2 * 3600)  # Israel is UTC+2
    return int(time.strftime("%H", israel_time)) < 19

class CibusDish:
    def __init__(self, category_id, dish_id, dish_price):
        self.category_id = category_id
        self.dish_id = dish_id
        self.dish_price = dish_price


class CibusApi:
    def __init__(self, username, password, token=""):
        self._session = requests.Session()

        self.__username=username
        self.__password=password
        self.__token=token
        self.__new_site="" # todo: does "new_site" still being used?

    def __cookies(self):
        return {'token': self.__token}

    def __new_site_cookie(self):
        return {
            'new_site': "e0b56031491001d279cc1303da04b0c25540a208a73dcfecfd1f8a90e7897f3b"
        }

    def __post_request(self, url, data):
        return self._session.post(
            url=url,
            headers=self.generate_data_header(),
            cookies=self.__cookies(),
            json=data

        )

    def __get_request(self, url):
        return self._session.get(
            url=url,
            headers=self.generate_data_header(),
            cookies=self.__cookies(),
        )

    def generate_header(self):
        return {
            "application-id": app_id,
            "User-Agent": user_agent
        }

    def generate_data_header(self):
        return {
            "authority": "api.consumers.pluxee.co.il",
            "application-id": app_id,
            "token": self.__token,
            "new_site": self.__new_site
        }

    def get_token(self, recaptcha_token):
        auth_url = "https://api.capir.pluxee.co.il/auth/authToken"
        
        headers = {
            "authority": "api.capir.pluxee.co.il",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "he",
            "application-id": "E5D5FEF5-A05E-4C64-AEBA-BA0CECA0E402",
            "origin": "https://consumers.pluxee.co.il",
            "referer": "https://consumers.pluxee.co.il/",
            "User-Agent": user_agent,
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        # Removed method, path, and scheme headers as they might confuse the server
        
        data = {
            "username": self.__username,
            "password": self.__password,
            "company": "",
            "reCAPTCHAToken": recaptcha_token
        }
        
        cookies = self.__new_site_cookie()
        
        print(f"Authenticating with username: {self.__username}")
        print(f"reCAPTCHA token length: {len(recaptcha_token)}")
        print(f"Token timestamp: {time.strftime('%H:%M:%S')}")
        print(f"Using cookies: {cookies}")
        
        try:
            res = self._session.post(
                url=auth_url, 
                headers=headers, 
                json=data, 
                cookies=cookies,
                timeout=30
            )
            
            print(f"Auth response status: {res.status_code}")
            print(f"Auth response headers: {dict(res.headers)}")
            
            for cookie in res.cookies:
                print(f"Received cookie: {cookie.name}={cookie.value}")
                self._session.cookies.set(cookie.name, cookie.value)
            
            try:
                response_data = json.loads(res.text)
                print(f"Auth response body: {json.dumps(response_data, indent=2)}")
                
                if res.status_code == 200:
                    self.__token = response_data.get("data", {}).get("token")
                    if not self.__token:
                        print("Warning: Token field not found in successful response")
                    else:
                        print("Successfully obtained authentication token")
                    return response_data
                else:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    print(f"Authentication failed: {error_msg}")
                    return None
            except json.JSONDecodeError:
                print(f"Failed to parse auth response: {res.text}")
                return None
                
        except Exception as e:
            print(f"Exception during authentication request: {str(e)}")
            return None

    def get_new_site_flag(self):
        data = {
            "type": call_types["new_site_flag"]
        }
        res = self._session.post(url=data_url, headers=self.generate_header(), json=data)
        self.__new_site = res.headers["Set-Cookie"].split(";")[0].split("=")[1]

    def get_order_dates(self, start_date, end_date):  # in "19/12/2024" format
        data = {
            "from_date": start_date,
            "to_date": end_date,
            "type": call_types["order_history"]
        }
        res = self.__post_request(url=data_url, data=data)
        return [order["date"] for order in json.loads(res.text)["list"]]

    def check_if_ordered_today(self):
        today = time.strftime("%d/%m/%Y")
        return today in self.get_order_dates(today, today)

    def get_cart_info(self):
        data = {
            "type": call_types["cart_information"]
        }
        res = self.__post_request(url=data_url, data=data)
        return json.loads(res.text)["total_price"]

    def get_dish_id_by_price(self, price, restaurant_id):
        all_items = list(self.get_restaurant_items(restaurant_id).items())[0][1]
        for dish in all_items:
            if dish.dish_price == price:
                return dish

    def get_restaurant_items(self, restaurant_id) -> dict:
        url = f"https://api.consumers.pluxee.co.il/api/rest_menu_tree.py?restaurant_id={restaurant_id}&order_type=2"
        res_items_dict = {}  # {category_id: [CibusDish]}
        res = self.__get_request(url=url)
        for chunk in json.loads(res.content)['12']:
            res_items_dict[chunk["element_id"]] = []
            for res_item in chunk["13"]:
                res_items_dict[chunk["element_id"]].append(CibusDish(
                    category_id=chunk["element_id"],
                    dish_id=res_item["element_id"],
                    dish_price=res_item["price"]
                ))
        return res_items_dict


    def add_dish_to_cart(self, category_id, dish_id, dish_price):  # used https://consumers.pluxee.co.il/restaurants/pickup/restaurant/39282
        data = {
            "dish_list": {
                "category_id": category_id,
                "dish_id": dish_id,
                "dish_price": dish_price,
                "co_owner_id": -1,
                "extra_list": []
            },
            "order_type": 2,
            "type": call_types["add_to_cart"]
        }
        print(data)
        res = self.__post_request(url=data_url, data=data)
        return json.loads(res.text)

    # def get_info(self):
    #     url = "https://api.consumers.pluxee.co.il/api/rest_menu_tree.py?restaurant_id=39282&comp_id=2538&order_type=2&element_type_deep=16&lang=he&address_id=1001196621"
    #     headers = {
    #         "authority": "api.consumers.pluxee.co.il",
    #         "application-id": app_id,
    #         "token": self.__token,
    #     }
    #     res = self._session.get(url=url, headers=headers)
    #     return res

    def apply_order(self):
        data = {
            "order_time": "18:45",  # TODO keep on 18:45? or always choose the closest 15 mins?
            "type": call_types["apply_order"]
        }

        try:
            print(f"Applying order with token: {self.__token[:10]}...")
            print(f"Using cookies: {self.__cookies()}")
            print(f"Headers: {self.generate_data_header()}")
            
            res = self.__post_request(url=data_url, data=data)
            
            print(f"Apply order response status: {res.status_code}")
            print(f"Apply order headers: {dict(res.headers)}")
            
            try:
                response_data = json.loads(res.text)
                print(f"Apply order response: {json.dumps(response_data, indent=2)}")
                
                if res.status_code >= 400:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    print(f"Apply order failed: {error_msg}")
                    
                    # If unauthorized, token might be expired
                    if res.status_code == 401:
                        print("Authentication token appears to be invalid or expired")
                        return {"status": "error", "message": "Authentication failed"}
                
                return response_data
            except json.JSONDecodeError:
                print(f"Failed to parse apply order response: {res.text}")
                return {"status": "error", "message": "Invalid response format"}
                
        except Exception as e:
            print(f"Error applying order: {str(e)}")
            return {"status": "error", "message": str(e)}

    def retry_auth_if_needed(self, recaptcha_token=None):
        from captcha_test import get_captcha_token
        
        if not self.__token or not recaptcha_token:
            recaptcha_token = get_captcha_token()
        
        result = self.get_token(recaptcha_token)
        if not result or not self.__token:
            print("Authentication retry failed")
            return False
            
        print(f"Authentication retry successful, new token: {self.__token[:10]}...")
        return True
