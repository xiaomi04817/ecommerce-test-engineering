"""订单模块测试 — 下单、状态流转、状态机验证 (场景 S05/S06/S07)"""
import pytest


def _setup_order_data(auth_client):
    """辅助函数: 准备下单需要的数据 (模块级，可被其他测试模块复用)"""
    # 获取地址
    addr_resp = auth_client.get("/addresses")
    addresses = addr_resp.json()["data"]
    if not addresses:
        # 创建一个地址
        resp = auth_client.post("/addresses", data={
            "receiverName": "下单人", "phone": "13600136001",
            "province": "浙江", "city": "杭州", "district": "西湖",
            "detail": "文三路88号浙大科技园301"
        })
        addr_id = resp.json()["data"]["id"]
    else:
        addr_id = addresses[0]["id"]

    # 获取商品
    prod_resp = auth_client.get("/products/1")
    product = prod_resp.json()["data"]
    return addr_id, product


class TestCreateOrder:
    """下单测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_create_order_success(self, auth_client, db):
        """TC-O-001: 有效商品+地址创建订单 (场景S05)"""
        addr_id, product = _setup_order_data(auth_client)
        old_stock = db.get_product_stock(1)

        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": 2}],
            "remark": "测试订单"
        })
        body = auth_client.assert_success(resp)
        order = body["data"]
        assert order["orderNo"] is not None
        assert order["status"] == "PENDING"
        assert order["totalAmount"] > 0

        # 验证库存扣减
        new_stock = db.get_product_stock(1)
        assert new_stock == old_stock - 2

    @pytest.mark.regression
    @pytest.mark.p1
    def test_create_order_empty_items(self, auth_client):
        """TC-O-002: 空商品列表下单"""
        addr_id, _ = _setup_order_data(auth_client)
        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": []
        })
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_create_order_insufficient_stock(self, auth_client):
        """TC-O-011(TC-P-011): 库存不足"""
        addr_id, _ = _setup_order_data(auth_client)
        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": 999999}]
        })
        auth_client.assert_fail(resp, expected_code=400, message_contains="库存不足")


class TestOrderStatusFlow:
    """订单状态流转测试"""

    def _create_pending_order(self, auth_client):
        """创建待支付订单并返回order"""
        addr_id, _ = _setup_order_data(auth_client)
        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": 1}]
        })
        return resp.json()["data"]

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_order_pay(self, auth_client):
        """STM-01: PENDING -> PAID (场景S05步骤8)"""
        order = self._create_pending_order(auth_client)
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        body = auth_client.assert_success(resp)
        assert body["data"]["status"] == "PAID"

    @pytest.mark.regression
    @pytest.mark.p1
    def test_order_cancel(self, auth_client, db):
        """STM-02: PENDING -> CANCELLED"""
        order = self._create_pending_order(auth_client)
        old_stock = db.get_product_stock(1)

        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "cancel"})
        body = auth_client.assert_success(resp)
        assert body["data"]["status"] == "CANCELLED"

        # 验证库存恢复
        new_stock = db.get_product_stock(1)
        assert new_stock == old_stock + 1

    @pytest.mark.regression
    @pytest.mark.p1
    def test_order_ship_and_receive(self, auth_client):
        """STM-03 + STM-05: PAID -> SHIPPED -> RECEIVED"""
        order = self._create_pending_order(auth_client)
        # 支付
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        # 发货
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "ship"})
        body = auth_client.assert_success(resp)
        assert body["data"]["status"] == "SHIPPED"
        # 收货
        resp2 = auth_client.put(f"/orders/{order['id']}/status", data={"action": "receive"})
        body2 = auth_client.assert_success(resp2)
        assert body2["data"]["status"] == "RECEIVED"

    @pytest.mark.regression
    @pytest.mark.p1
    def test_order_refund(self, auth_client, db):
        """STM-04: PAID -> REFUNDED"""
        order = self._create_pending_order(auth_client)
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})

        old_stock = db.get_product_stock(1)
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "refund"})
        body = auth_client.assert_success(resp)
        assert body["data"]["status"] == "REFUNDED"

        # 验证库存恢复
        new_stock = db.get_product_stock(1)
        assert new_stock == old_stock + 1

    @pytest.mark.regression
    @pytest.mark.p1
    def test_stm_shipped_to_refunded(self, auth_client):
        """STM-06: SHIPPED -> REFUNDED (合法)"""
        order = self._create_pending_order(auth_client)
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "ship"})
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "refund"})
        body = auth_client.assert_success(resp)
        assert body["data"]["status"] == "REFUNDED"


class TestOrderStateMachineIllegal:
    """状态机非法迁移测试 (场景S07)"""

    def _create_pending_order(self, auth_client):
        addr_id, _ = _setup_order_data(auth_client)
        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": 1}]
        })
        return resp.json()["data"]

    @pytest.mark.full
    @pytest.mark.p0
    def test_pending_to_shipped_illegal(self, auth_client):
        """STM-07: PENDING -> SHIPPED (非法)"""
        order = self._create_pending_order(auth_client)
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "ship"})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p0
    def test_pending_to_received_illegal(self, auth_client):
        """STM-08: PENDING -> RECEIVED (非法)"""
        order = self._create_pending_order(auth_client)
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "receive"})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p0
    def test_shipped_to_paid_illegal(self, auth_client):
        """STM-09: SHIPPED -> PAID (非法逆向流转)"""
        order = self._create_pending_order(auth_client)
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "ship"})
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p0
    def test_terminal_no_change(self, auth_client):
        """STM-10/11/12: 终态不可变"""
        order = self._create_pending_order(auth_client)
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "cancel"})

        # 已取消的订单不能再操作
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.assert_fail(resp, expected_code=400, message_contains="已结束")

    @pytest.mark.full
    @pytest.mark.p0
    def test_terminal_received_immutable(self, auth_client):
        """STM-10: 终态(已收货)不可再变"""
        order = self._create_pending_order(auth_client)
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "ship"})
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "receive"})
        # 尝试再支付
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.assert_fail(resp, expected_code=400, message_contains="已结束")

    @pytest.mark.full
    @pytest.mark.p1
    def test_terminal_cancelled_immutable(self, auth_client):
        """STM-11: 终态(已取消)不可再变"""
        order = self._create_pending_order(auth_client)
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "cancel"})
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p1
    def test_terminal_refunded_immutable(self, auth_client):
        """STM-12: 终态(已退款)不可再变"""
        order = self._create_pending_order(auth_client)
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "refund"})
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        auth_client.assert_fail(resp, expected_code=400)


class TestOrderQuery:
    """订单查询测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_list_orders(self, auth_client):
        """TC-O-005: 分页获取订单列表"""
        resp = auth_client.get("/orders", params={"page": 1, "size": 20})
        body = auth_client.assert_success(resp)
        assert "records" in body["data"]
        assert "total" in body["data"]

    @pytest.mark.regression
    @pytest.mark.p1
    def test_get_order_detail(self, auth_client):
        """TC-O-006: 获取自己订单详情"""
        # 先下单
        addr_id, _ = _setup_order_data(auth_client)
        create_resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": 1}]
        })
        order_id = create_resp.json()["data"]["id"]

        resp = auth_client.get(f"/orders/{order_id}")
        body = auth_client.assert_success(resp)
        assert body["data"]["orderNo"] is not None

    @pytest.mark.regression
    @pytest.mark.p1
    def test_get_order_other_user(self, auth_client):
        """TC-O-007: 获取其他用户订单 (应失败)"""
        resp = auth_client.get("/orders/99999")  # 不存在的订单
        auth_client.assert_fail(resp, expected_code=404)


class TestOrderEdgeCases:
    """订单边界与异常场景"""

    @pytest.mark.regression
    @pytest.mark.p1
    def test_paid_cannot_cancel(self, auth_client):
        """TC-O-B01: PAID → CANCELLED (非法, 允许的迁移只有 SHIPPED/REFUNDED)"""
        addr_id, _ = _setup_order_data(auth_client)
        create_resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": 1}]
        })
        order = create_resp.json()["data"]
        # 支付
        auth_client.put(f"/orders/{order['id']}/status", data={"action": "pay"})
        # 尝试取消 — PAID 状态下不允许取消
        resp = auth_client.put(f"/orders/{order['id']}/status", data={"action": "cancel"})
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_order_nonexistent_product(self, auth_client):
        """TC-O-B02: 下单包含不存在的商品ID"""
        addr_id, _ = _setup_order_data(auth_client)
        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 99999, "quantity": 1}]
        })
        auth_client.assert_fail(resp, expected_code=400, message_contains="不存在")

    @pytest.mark.regression
    @pytest.mark.p1
    def test_order_zero_quantity_item(self, auth_client):
        """TC-O-B03: 下单数量为0"""
        addr_id, _ = _setup_order_data(auth_client)
        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": 0}]
        })
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_order_negative_quantity_item(self, auth_client):
        """TC-O-B04: 下单数量为负数"""
        addr_id, _ = _setup_order_data(auth_client)
        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [{"productId": 1, "quantity": -1}]
        })
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_order_multi_items_stock_deduction(self, auth_client, db):
        """TC-O-B05: 多商品下单后各商品库存分别正确扣减"""
        addr_id, _ = _setup_order_data(auth_client)
        old_stock_1 = db.get_product_stock(1)
        old_stock_2 = db.get_product_stock(2)

        resp = auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [
                {"productId": 1, "quantity": 3},
                {"productId": 2, "quantity": 2}
            ]
        })
        auth_client.assert_success(resp)

        new_stock_1 = db.get_product_stock(1)
        new_stock_2 = db.get_product_stock(2)
        assert new_stock_1 == old_stock_1 - 3, \
            f"Product 1: expected {old_stock_1 - 3}, got {new_stock_1}"
        assert new_stock_2 == old_stock_2 - 2, \
            f"Product 2: expected {old_stock_2 - 2}, got {new_stock_2}"

    @pytest.mark.regression
    @pytest.mark.p1
    def test_cart_emptied_after_order(self, auth_client, db):
        """TC-C-012: 下单成功后购物车中已购商品被清空"""
        # 添加商品到购物车
        auth_client.post("/cart/items", data={"productId": 1, "quantity": 2})
        auth_client.post("/cart/items", data={"productId": 2, "quantity": 1})

        # 验证购物车有货
        cart_before = auth_client.get("/cart")
        before_items = cart_before.json()["data"]["items"]
        assert len(before_items) >= 2

        # 下单
        addr_id, _ = _setup_order_data(auth_client)
        auth_client.post("/orders", data={
            "addressId": addr_id,
            "items": [
                {"productId": 1, "quantity": 2},
                {"productId": 2, "quantity": 1}
            ]
        })

        # 验证购物车中 product 1 和 2 已被清空
        cart_after = auth_client.get("/cart")
        after_items = cart_after.json()["data"]["items"]
        remaining_ids = {i["productId"] for i in after_items}
        assert 1 not in remaining_ids, "Product 1 should be cleared from cart"
        assert 2 not in remaining_ids, "Product 2 should be cleared from cart"
