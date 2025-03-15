"""
Receives:
    token(/username+password)
    link to restaurant (grocery store)
    price of daily cibus to fetch

    --dry flag (wont apply order)
"""

from cibus_api import CibusApi


class AutoCibusInterface:
    def __init__(self, username, password, restaurant_id):
        self.cibus_api = CibusApi(username, password)
        self.__login_and_save_token()

    def __login_and_save_token(self):
        self.cibus_api.get_token()
        self.cibus_api.get_new_site_flag()

    def check_if_ordered_today(self):
        return self.cibus_api.check_if_ordered_today()


if __name__ == '__main__':
    print(AutoCibusInterface(
        username="",
        password="",
        restaurant_id=39282).cibus_api.get_order_dates(
        start_date="01/02/2025",
        end_date="15/02/2025"
    ))