"""收货地址模块测试 (场景 S04)"""
import pytest


class TestAddressCRUD:
    """地址增删改查"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_add_address(self, auth_client):
        """TC-A-002: 有效信息新增地址"""
        resp = auth_client.post("/addresses", data={
            "receiverName": "张三",
            "phone": "13800138001",
            "province": "广东省",
            "city": "深圳市",
            "district": "南山区",
            "detail": "科技园路1号创新大厦1001室",
            "isDefault": False
        })
        body = auth_client.assert_success(resp)
        assert body["data"]["receiverName"] == "张三"

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_list_addresses(self, auth_client):
        """TC-A-001: 获取地址列表"""
        resp = auth_client.get("/addresses")
        body = auth_client.assert_success(resp)
        assert isinstance(body["data"], list)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_add_address_invalid_phone(self, auth_client):
        """TC-A-003: 手机号格式非法"""
        resp = auth_client.post("/addresses", data={
            "receiverName": "张三",
            "phone": "12345",
            "province": "广东",
            "city": "深圳",
            "district": "南山",
            "detail": "详细地址12345"
        })
        auth_client.assert_fail(resp, expected_code=400, message_contains="手机")

    @pytest.mark.regression
    @pytest.mark.p1
    def test_add_address_empty_name(self, auth_client):
        """TC-A-004: 收件人为空"""
        resp = auth_client.post("/addresses", data={
            "receiverName": "",
            "phone": "13800138001",
            "province": "广东",
            "city": "深圳",
            "district": "南山",
            "detail": "详细地址12345"
        })
        auth_client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_update_address(self, auth_client):
        """TC-A-006: 修改地址"""
        # 先创建
        resp = auth_client.post("/addresses", data={
            "receiverName": "李四", "phone": "13900139001",
            "province": "北京", "city": "北京", "district": "朝阳",
            "detail": "建国路100号A座2001室"
        })
        addr_id = resp.json()["data"]["id"]

        # 修改
        resp2 = auth_client.put(f"/addresses/{addr_id}", data={
            "receiverName": "李四改", "phone": "13900139001",
            "province": "北京", "city": "北京", "district": "海淀",
            "detail": "中关村大街1号B座301室"
        })
        auth_client.assert_success(resp2)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_delete_address(self, auth_client):
        """TC-A-007: 删除地址"""
        resp = auth_client.post("/addresses", data={
            "receiverName": "王五", "phone": "13700137001",
            "province": "上海", "city": "上海", "district": "浦东",
            "detail": "张江路500号C座808室"
        })
        addr_id = resp.json()["data"]["id"]

        resp2 = auth_client.delete(f"/addresses/{addr_id}")
        auth_client.assert_success(resp2)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_address_no_auth(self, client):
        """未登录获取地址列表"""
        resp = client.get("/addresses")
        client.assert_fail(resp, expected_code=401)

    @pytest.mark.full
    @pytest.mark.p2
    def test_address_max_limit(self, auth_client):
        """TC-A-005: 地址数量上限"""
        # 创建10个地址
        for i in range(10):
            auth_client.post("/addresses", data={
                "receiverName": f"用户{i}", "phone": f"1380013{i:04d}",
                "province": "省", "city": "市", "district": "区",
                "detail": f"第{i}条详细地址信息"
            })
        # 第11个应失败
        resp = auth_client.post("/addresses", data={
            "receiverName": "超限", "phone": "13800138888",
            "province": "省", "city": "市", "district": "区",
            "detail": "第十一条详细地址信息哦"
        })
        auth_client.assert_fail(resp, expected_code=400, message_contains="最多")

    # ---- 新增: 异常ID操作 ----

    @pytest.mark.regression
    @pytest.mark.p1
    def test_update_nonexistent_address(self, auth_client):
        """TC-A-B01: 修改不存在的地址"""
        resp = auth_client.put("/addresses/99999", data={
            "receiverName": "张三", "phone": "13800138001",
            "province": "广东", "city": "深圳", "district": "南山",
            "detail": "科技园路1号"
        })
        auth_client.assert_fail(resp, expected_code=404)

    @pytest.mark.full
    @pytest.mark.p1
    def test_delete_other_user_address(self, auth_client):
        """TC-A-008: 删除不存在的地址(模拟其他用户地址/已删除地址)"""
        resp = auth_client.delete("/addresses/99999")
        auth_client.assert_fail(resp, expected_code=404)
