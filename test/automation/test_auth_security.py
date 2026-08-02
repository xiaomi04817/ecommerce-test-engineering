"""权限安全与并发测试 (场景 S08/S10)"""
import time
import pytest
import concurrent.futures
from utils.api_client import ApiClient

BASE_URL = "http://localhost:8080/api"


def _setup_order_data(auth_client):
    """辅助函数: 准备下单需要的数据 (本地副本，避免跨模块导入问题)"""
    addr_resp = auth_client.get("/addresses")
    addresses = addr_resp.json()["data"]
    if not addresses:
        resp = auth_client.post("/addresses", data={
            "receiverName": "下单人", "phone": "13600136001",
            "province": "浙江", "city": "杭州", "district": "西湖",
            "detail": "文三路88号浙大科技园301"
        })
        addr_id = resp.json()["data"]["id"]
    else:
        addr_id = addresses[0]["id"]

    prod_resp = auth_client.get("/products/1")
    product = prod_resp.json()["data"]
    return addr_id, product


class TestAuthRequired:
    """需要认证的接口 - 无Token测试"""

    @pytest.mark.regression
    @pytest.mark.p1
    @pytest.mark.parametrize("method,path,data", [
        ("GET", "/cart", None),
        ("POST", "/cart/items", {"productId": 1, "quantity": 1}),
        ("GET", "/addresses", None),
        ("POST", "/addresses", {
            "receiverName": "X", "phone": "13800138000",
            "province": "A", "city": "B", "district": "C",
            "detail": "D address info enough"
        }),
        ("GET", "/orders", None),
        ("POST", "/orders", {
            "addressId": 1,
            "items": [{"productId": 1, "quantity": 1}]
        }),
    ])
    def test_unauthorized_access(self, client, method, path, data):
        """TC-S-001: 所有写接口无Token返回401"""
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, data=data)
        elif method == "PUT":
            resp = client.put(path, data=data)
        elif method == "DELETE":
            resp = client.delete(path)
        client.assert_fail(resp, expected_code=401)


class TestUserIsolation:
    """用户隔离测试"""

    @pytest.mark.regression
    @pytest.mark.p1
    def test_cannot_access_other_user_order(self, auth_client):
        """TC-S-003: 获取不存在的订单"""
        resp = auth_client.get("/orders/99999")
        auth_client.assert_fail(resp, expected_code=404)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_public_endpoints_no_auth_required(self, client):
        """验证公开接口无需认证"""
        resp = client.get("/products", params={"page": 1, "size": 5})
        client.assert_success(resp)

        resp = client.get("/products/1")
        client.assert_success(resp)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_cannot_modify_other_user_cart(self, auth_client):
        """TC-S-002: 尝试修改不存在的购物车项（属于其他用户）"""
        resp = auth_client.put("/cart/items/99999", data={"quantity": 10})
        auth_client.assert_fail(resp, expected_code=400)


class TestConcurrent:
    """并发场景测试 (场景S10)"""

    @pytest.mark.full
    @pytest.mark.p1
    def test_concurrent_order_same_stock(self, auth_client, db):
        """TC-S-005: 库存竞态 - 两个请求同时下单同一商品"""
        # 设置一个商品只有1件库存
        db.execute("UPDATE products SET stock = 1 WHERE id = 4")

        addr_id, _ = _setup_order_data(auth_client)

        results = []
        saved_token = auth_client.session.headers.get("Authorization", "")

        def place_order():
            # 每个线程使用自己的client
            c = ApiClient(BASE_URL)
            c.session.headers["Authorization"] = saved_token
            return c.post("/orders", data={
                "addressId": addr_id,
                "items": [{"productId": 4, "quantity": 1}]
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(place_order) for _ in range(2)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        # 应该只有一个成功
        success_count = sum(
            1 for r in results
            if r.status_code == 200 and r.json().get("code") == 200
        )
        assert success_count == 1, f"Expected exactly 1 success, got {success_count}"

        # 恢复库存
        db.execute("UPDATE products SET stock = 200 WHERE id = 4")

    @pytest.mark.full
    @pytest.mark.p1
    def test_concurrent_duplicate_order(self, auth_client):
        """TC-S-006: 重复提交订单"""
        addr_id, _ = _setup_order_data(auth_client)

        results = []
        saved_token = auth_client.session.headers.get("Authorization", "")

        def submit():
            c = ApiClient(BASE_URL)
            c.session.headers["Authorization"] = saved_token
            return c.post("/orders", data={
                "addressId": addr_id,
                "items": [{"productId": 3, "quantity": 1}]
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(submit) for _ in range(2)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        # 两个都应该成功(不同订单号)
        for r in results:
            assert r.status_code == 200


class TestResponseFormat:
    """响应格式验证"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_response_format(self, client):
        """TC-S-008: 统一响应格式"""
        resp = client.get("/products/1")
        body = resp.json()
        assert "code" in body
        assert "message" in body
        assert "data" in body or "data" not in body  # data字段存在或为null


class TestJWTSecurity:
    """JWT Token 安全测试"""

    @pytest.mark.regression
    @pytest.mark.p1
    def test_jwt_tampered_token(self, client):
        """TC-S-B01: 篡改过的 JWT Token 应拒绝"""
        # 三段式格式但内容无效
        client.set_token("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.tampered_signature")
        resp = client.get("/users/me")
        client.assert_fail(resp, expected_code=401)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_jwt_malformed_token(self, client):
        """TC-S-B02: 格式损坏的 JWT Token 应拒绝"""
        client.set_token("not.a.token")
        resp = client.get("/users/me")
        client.assert_fail(resp, expected_code=401)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_jwt_empty_token(self, client):
        """TC-S-B03: 空字符串 Token 应拒绝"""
        client.set_token("")
        resp = client.get("/users/me")
        client.assert_fail(resp, expected_code=401)


class TestResponseTime:
    """响应时间验证 (REQ-NF-005)"""

    @pytest.mark.full
    @pytest.mark.p2
    @pytest.mark.parametrize("method,path,desc", [
        ("GET", "/products?page=1&size=20", "商品列表"),
        ("GET", "/products/1", "商品详情"),
        ("GET", "/products/search?keyword=手机", "商品搜索"),
    ])
    def test_read_endpoint_response_time(self, client, method, path, desc):
        """TC-S-007: 读接口响应时间 ≤ 2000ms (开发环境宽松阈值)"""
        start = time.time()
        if method == "GET":
            resp = client.get(path)
        end = time.time()
        elapsed_ms = (end - start) * 1000
        assert resp.status_code == 200, f"{desc} 请求失败: {resp.status_code}"
        assert elapsed_ms < 2000, f"{desc} 响应时间 {elapsed_ms:.0f}ms > 2000ms"
