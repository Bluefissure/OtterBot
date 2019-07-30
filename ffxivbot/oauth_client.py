import json
import urllib.parse
import requests

class OAuthQQ:
    def __init__(self, client_id, client_key, redirect_uri):
        self.client_id = client_id
        self.client_key = client_key
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        """获取授权页面的网址"""
        params = {'client_id': self.client_id,
                  'response_type': 'code',
                  'redirect_uri': self.redirect_uri,
                  'scope': 'get_user_info',
                  'state': 1}
        url = 'https://graph.qq.com/oauth2.0/authorize?%s' % urllib.parse.urlencode(params)
        return url

    def get_access_token(self, code):
        """根据code获取access_token"""
        params = {'grant_type': 'authorization_code',
                  'client_id': self.client_id,
                  'client_secret': self.client_key,
                  'code': code,
                  'redirect_uri': self.redirect_uri}
        url = 'https://graph.qq.com/oauth2.0/token?%s' % urllib.parse.urlencode(params)

        response = requests.post(url, data=params)
        result = urllib.parse.parse_qs(response.text)
        access_token = str(result['access_token'][0])
        self.access_token = access_token
        return access_token

    def get_open_id(self):
        """获取QQ的OpenID"""
        params = {'access_token': self.access_token}
        url = 'https://graph.qq.com/oauth2.0/me?%s' % urllib.parse.urlencode(params)

        response = requests.post(url, data=params)
        v_str = str(response.text)[9:-3]
        v_json = json.loads(v_str)
        openid = v_json['openid']
        self.openid = openid
        return openid

    def get_qq_info(self):
        """获取QQ用户的资料信息"""
        params = {'access_token': self.access_token,
                  'oauth_consumer_key': self.client_id,
                  'openid': self.openid}
        url = 'https://graph.qq.com/user/get_user_info?%s' % urllib.parse.urlencode(params)

        response = requests.post(url, data=params)
        return json.loads(response.text)