"""API Client — 封装 requests 库，提供统一的请求方法"""

import requests
import json
from typing import Optional


class ApiClient:
    """HTTP API 客户端"""

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def set_token(self, token: str):
        """设置 JWT Token"""
        self.token = token
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self):
        """清除 Token（模拟未登录状态）"""
        self.token = None
        self.session.headers.pop("Authorization", None)

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get(self, path: str, params: Optional[dict] = None, **kwargs):
        """GET 请求"""
        return self.session.get(self._url(path), params=params, **kwargs)

    def post(self, path: str, data: Optional[dict] = None, **kwargs):
        """POST 请求"""
        return self.session.post(self._url(path), json=data, **kwargs)

    def put(self, path: str, data: Optional[dict] = None, **kwargs):
        """PUT 请求"""
        return self.session.put(self._url(path), json=data, **kwargs)

    def delete(self, path: str, **kwargs):
        """DELETE 请求"""
        return self.session.delete(self._url(path), **kwargs)

    @staticmethod
    def assert_success(response: requests.Response, expected_code: int = 200):
        """断言响应成功"""
        assert response.status_code == 200, \
            f"Expected HTTP 200, got {response.status_code}: {response.text}"
        body = response.json()
        assert body.get("code") == expected_code, \
            f"Expected code {expected_code}, got {body.get('code')}: {body.get('message')}"
        return body

    @staticmethod
    def assert_fail(response: requests.Response, expected_http: int = 200,
                    expected_code: int = 400, message_contains: Optional[str] = None):
        """断言响应失败"""
        body = response.json()
        assert body.get("code") == expected_code, \
            f"Expected code {expected_code}, got {body.get('code')}"
        if message_contains:
            assert message_contains in body.get("message", ""), \
                f"Expected message containing '{message_contains}', got '{body.get('message')}'"
        return body
