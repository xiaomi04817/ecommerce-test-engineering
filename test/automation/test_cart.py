"""购物车模块测试 (场景 S03)"""
import pytest


class TestCartAuth:
    """购物车权限测试"""

    @pytest.mark.regression
    @pytest.mark.p1
    def test_get_cart_no_auth(self, client):
        """未登录获取购物车"""
        resp = client.get("/cart")
        client.assert_fail(resp, expected_code=401)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_add_cart_no_auth(self, client):
        """未登录添加购物车"""
        resp = client.post("/cart/items", data={"productId": 1, "quantity": 1})
        client.assert_fail(resp, expected_code=401)


class TestCartOperations:
    """购物车CRUD测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_add_to_cart(self, auth_client):
        """TC-C-003: 有效商品添加到购物车"""
        resp = auth_client.post("/cart/items", data={"productId": 1, "quantity": 2})
        auth_client.assert_success(resp)

        # 验证购物车中有该商品
        cart_resp = auth_client.get("/cart")
        body = auth_client.assert_success(cart_resp)
        items = [i for i in body["data"]["items"] if i["productId"] == 1]
        assert len(items) > 0

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_cart(self, auth_client):
        """TC-C-001: 获取购物车"""
        resp = auth_client.get("/cart")
        body = auth_client.assert_success(resp)
        assert "items" in body["data"]
        assert "totalAmount" in body["data"]

    @pytest.mark.regression
    @pytest.mark.p1
    def test_add_cart_quantity_accumulate(self, auth_client):
        """TC-C-004: 已存在商品数量累加"""
        # 第一次添加
        auth_client.post("/cart/items", data={"productId": 2, "quantity": 1})
        # 第二次添加同一商品
        auth_client.post("/cart/items", data={"productId": 2, "quantity": 2})

        cart_resp = auth_client.get("/cart")
        body = auth_client.assert_success(cart_resp)
        item = next((i for i in body["data"]["items"] if i["productId"] == 2), None)
        assert item is not None
        assert item["quantity"] >= 3  # 1+2 累加

    @pytest.mark.regression
    @pytest.mark.p1
    def test_add_cart_exceed_stock(self, auth_client):
        """TC-C-005: 添加数量超过库存"""
        resp = auth_client.post("/cart/items", data={"productId": 1, "quantity": 999999})
        auth_client.assert_fail(resp, expected_code=400, message_contains="库存不足")

    @pytest.mark.full
    @pytest.mark.p2
    def test_add_zero_stock_product(self, auth_client):
        """TC-C-006: 添加库存为0的商品"""
        resp = auth_client.post("/cart/items", data={"productId": 5, "quantity": 1})  # 商品5库存=0
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_add_cart_zero_quantity(self, auth_client):
        """TC-C-007: 数量为0"""
        resp = auth_client.post("/cart/items", data={"productId": 1, "quantity": 0})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_update_quantity(self, auth_client):
        """TC-C-008: 合法修改数量"""
        # 先添加
        auth_client.post("/cart/items", data={"productId": 3, "quantity": 1})
        # 获取购物车项ID
        cart_resp = auth_client.get("/cart")
        body = auth_client.assert_success(cart_resp)
        item = next((i for i in body["data"]["items"] if i["productId"] == 3), None)
        assert item is not None

        # 修改数量
        resp = auth_client.put(f"/cart/items/{item['id']}", data={"quantity": 5})
        auth_client.assert_success(resp)

        # 验证
        cart_resp2 = auth_client.get("/cart")
        body2 = auth_client.assert_success(cart_resp2)
        item2 = next((i for i in body2["data"]["items"] if i["productId"] == 3), None)
        assert item2["quantity"] == 5

    @pytest.mark.regression
    @pytest.mark.p1
    def test_delete_cart_item(self, auth_client):
        """TC-C-011: 删除购物车商品"""
        # 添加商品
        auth_client.post("/cart/items", data={"productId": 4, "quantity": 1})
        cart_resp = auth_client.get("/cart")
        body = auth_client.assert_success(cart_resp)
        item = next((i for i in body["data"]["items"] if i["productId"] == 4), None)

        if item:
            resp = auth_client.delete(f"/cart/items/{item['id']}")
            auth_client.assert_success(resp)

    # ---- 新增: 异常输入边界 ----

    @pytest.mark.regression
    @pytest.mark.p1
    def test_add_nonexistent_product(self, auth_client):
        """TC-C-B01: 添加不存在的商品到购物车"""
        resp = auth_client.post("/cart/items", data={"productId": 99999, "quantity": 1})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_update_negative_quantity(self, auth_client):
        """TC-C-B02: 修改购物车数量为负数"""
        # 先添加
        auth_client.post("/cart/items", data={"productId": 3, "quantity": 1})
        cart_resp = auth_client.get("/cart")
        body = auth_client.assert_success(cart_resp)
        item = next((i for i in body["data"]["items"] if i["productId"] == 3), None)
        assert item is not None

        # 修改为负数
        resp = auth_client.put(f"/cart/items/{item['id']}", data={"quantity": -1})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_delete_nonexistent_cart_item(self, auth_client):
        """TC-C-B03: 删除不存在的购物车条目"""
        resp = auth_client.delete("/cart/items/99999")
        auth_client.assert_fail(resp, expected_code=400)
