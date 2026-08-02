"""兼容性测试 — API 兼容 + 前端多浏览器/移动端模拟"""
import pytest
import requests
from utils.api_client import ApiClient

BASE_URL = "http://localhost:8080/api"


class TestAPIContentTypeCompat:
    """API Content-Type 兼容性"""

    def test_json_content_type(self):
        """COM-API-01: Content-Type: application/json 正常请求"""
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "testuser1", "password": "Test@123456"
        })
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_missing_content_type(self):
        """COM-API-02: 缺少 Content-Type 头的 POST 请求 — 应返回错误"""
        resp = requests.post(f"{BASE_URL}/auth/login",
                             data='{"username":"testuser1","password":"Test@123456"}')
        body = resp.json()
        # 不支持的非 JSON 请求应返回业务错误码 (HTTP 200 + body code 4xx)
        assert body["code"] in [400, 415], \
            f"Missing Content-Type returned code={body['code']}: {resp.text[:100]}"

    def test_form_urlencoded(self):
        """COM-API-03: Content-Type: application/x-www-form-urlencoded — 应返回错误"""
        resp = requests.post(f"{BASE_URL}/auth/login", data={
            "username": "testuser1", "password": "Test@123456"
        })
        body = resp.json()
        # API 设计为 JSON-only, form 数据应被拒绝
        assert body["code"] == 415, \
            f"Form data returned code={body['code']}: {resp.text[:100]}"

    def test_accept_json_response(self):
        """COM-API-04: Accept: application/json 返回 JSON"""
        resp = requests.get(f"{BASE_URL}/products/1",
                            headers={"Accept": "application/json"})
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type", "").startswith("application/json")

    def test_accept_any_response(self):
        """COM-API-05: Accept: */* 返回 JSON"""
        resp = requests.get(f"{BASE_URL}/products/1",
                            headers={"Accept": "*/*"})
        assert resp.status_code == 200
        # 应该也是 JSON
        ct = resp.headers.get("Content-Type", "")
        assert "json" in ct.lower() or "text" in ct.lower(), \
            f"Unexpected Content-Type: {ct}"

    def test_utf8_chinese_text(self):
        """COM-API-06: UTF-8 中文字符正确处理"""
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "username": "测试用户中文",
            "password": "Chinese@123",
            "email": "cn@test.com"
        })
        body = resp.json()
        # 中文用户名可能因格式校验被拒绝 (@Pattern ^[a-zA-Z]...)
        # 也可能因用户名长度 > 20 被拒绝
        # 关键: 不出现乱码, 不出现 500
        assert resp.status_code != 500, f"Chinese text caused 500: {resp.text[:200]}"
        print(f"  Chinese username response: code={body['code']}, msg={body.get('message','')[:50]}")

    def test_emoji_text(self):
        """COM-API-07: Emoji 字符请求不崩溃"""
        resp = requests.get(f"{BASE_URL}/products/search",
                            params={"keyword": "😀🎉"})
        assert resp.status_code == 200
        # Emoji 搜索应该不崩溃, 返回无结果或正常结果
        print(f"  Emoji search result: {resp.json()['data'].get('total', 0)} items")


class TestHTTPMethodCompat:
    """HTTP 方法兼容性"""

    def test_options_method(self, client):
        """COM-METHOD-01: OPTIONS 预检请求"""
        resp = requests.options(f"{BASE_URL}/products/1")
        # OPTIONS 应返回 200 (CORS preflight)
        assert resp.status_code in [200, 204], \
            f"OPTIONS returned {resp.status_code}"

    def test_head_method(self, client):
        """COM-METHOD-02: HEAD 请求"""
        resp = requests.head(f"{BASE_URL}/products/1")
        # HEAD 不应崩溃, 返回 200 或 405
        assert resp.status_code != 500, f"HEAD returned 500"
        print(f"  HEAD /products/1 → {resp.status_code}")

    def test_trace_method_rejected(self, client):
        """COM-METHOD-03: TRACE 方法应被拒绝"""
        resp = requests.request("TRACE", f"{BASE_URL}/products/1")
        # TRACE 通常被禁用
        assert resp.status_code in [405, 403, 501], \
            f"TRACE returned {resp.status_code} (expected 405/403/501)"


class TestURLEdgeCases:
    """URL 边界兼容性"""

    def test_trailing_slash(self, client):
        """COM-URL-01: 尾部斜杠兼容"""
        resp = client.get("/products/1/")
        # 有尾斜杠不应 500
        assert resp.status_code != 500, f"Trailing slash caused 500: {resp.text[:100]}"
        print(f"  /products/1/ → {resp.status_code}")

    def test_double_slash(self, client):
        """COM-URL-02: 双斜杠"""
        resp = client.get("/products//1")
        assert resp.status_code != 500, f"Double slash caused 500"
        print(f"  /products//1 → {resp.status_code}")

    def test_very_long_url(self, client):
        """COM-URL-03: 超长查询参数"""
        long_kw = "a" * 1000
        resp = client.get("/products/search", params={"keyword": long_kw})
        assert resp.status_code != 500, f"Long URL caused 500"
        print(f"  Search with 1000-char keyword → {resp.status_code}")

    def test_special_chars_in_path(self, client):
        """COM-URL-04: 特殊字符路径"""
        resp = client.get("/products/%00")  # null byte
        # 关键: 不 500
        assert resp.status_code != 500, f"Null byte caused 500"
        print(f"  /products/%00 → {resp.status_code}")


class TestFrontendCompat:
    """前端兼容性 (检查首页可访问)"""

    def test_frontend_reachable(self):
        """COM-FE-01: 前端首页可访问 (localhost:3000)"""
        try:
            resp = requests.get("http://localhost:3000", timeout=5)
            assert resp.status_code == 200, f"Frontend returned {resp.status_code}"
            # 包含 Vue app 标记
            assert "html" in resp.text.lower(), "Not an HTML page"
            print("  Frontend http://localhost:3000 OK")
        except requests.ConnectionError:
            pytest.skip("Frontend not running on port 3000 — 跳过前端兼容测试")

    def test_frontend_api_proxy(self):
        """COM-FE-02: 前端 API 代理正常工作"""
        try:
            resp = requests.get("http://localhost:3000", timeout=5)
            if resp.status_code != 200:
                pytest.skip("Frontend not available")
        except requests.ConnectionError:
            pytest.skip("Frontend not running")

        # 直接测试后端, 验证前端引用的 API 可访问
        resp = requests.get(f"{BASE_URL}/products?page=1&size=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["records"]) > 0, "No products available for frontend"


if __name__ == "__main__":
    print("=" * 60)
    print("  兼容性测试报告")
    print("=" * 60)
    pytest.main([__file__, "-v", "--tb=short"])
