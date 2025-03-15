import time
import requests
import json

from additional_data import authorization_url, data_url, app_id, call_types

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
            "application-id": app_id
        }

    def generate_data_header(self):
        return {
            "authority": "api.consumers.pluxee.co.il",
            "application-id": app_id,
            "token": self.__token,
            "new_site": self.__new_site
        }

    def get_token(self):  # possible with new capcha?
        data = {
            "company": "",
            "username": self.__username,
            "password": self.__password
        }
        res = self._session.post(url=authorization_url, headers=self.generate_header(), json=data)
        time.sleep(1)
        print(res.text)
        self.__token = json.loads(res.text)["data"]["token"]

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

        res = self.__post_request(url=data_url, data=data)
        print(res.content)
        return res
