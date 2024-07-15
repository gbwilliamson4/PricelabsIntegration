import requests

class SyncCalendars:
    def __init__(self, wp_login_url, sync_url, username, password):
        self.wp_login_url = wp_login_url
        self.sync_url = sync_url
        self.username = username
        self.password = password

    def send_sync_request(self):
        with requests.Session() as s:
            headers1 = {'Cookie': 'wordpress_test_cookie=WP Cookie check'}
            datas = {
                'log': self.username, 'pwd': self.password, 'wp-submit': 'Log In',
                'redirect_to': self.sync_url, 'testcookie': '1'
            }
            s.post(self.wp_login_url, headers=headers1, data=datas)
            resp = s.post(self.sync_url)
            print(resp.status_code)
            return resp.status_code
