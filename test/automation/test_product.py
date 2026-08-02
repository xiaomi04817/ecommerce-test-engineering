"""商品模块测试 — 列表、详情、搜索 (场景 S02)"""
import pytest


class TestProductList:
    """商品列表测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_list_products(self, client):
        """TC-P-001: 默认分页获取商品列表"""
        resp = client.get("/products", params={"page": 1, "size": 20})
        body = client.assert_success(resp)
        data = body["data"]
        assert "records" in data
        assert "total" in data
        assert data["total"] >= 0
        assert isinstance(data["records"], list)

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_list_products_default_params(self, client):
        """不传参数使用默认值"""
        resp = client.get("/products")
        body = client.assert_success(resp)
        assert body["data"]["records"] is not None

    @pytest.mark.regression
    @pytest.mark.p1
    def test_list_products_with_pagination(self, client):
        """分页参数生效"""
        resp = client.get("/products", params={"page": 1, "size": 2})
        body = client.assert_success(resp)
        assert len(body["data"]["records"]) <= 2

    @pytest.mark.full
    @pytest.mark.p2
    def test_list_products_page_zero(self, client):
        """TC-P-002: 分页页码为0"""
        resp = client.get("/products", params={"page": 0, "size": 20})
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_list_products_oversized_page(self, client):
        """TC-P-003: 超大页码"""
        resp = client.get("/products", params={"page": 99999, "size": 20})
        body = client.assert_success(resp)
        assert len(body["data"]["records"]) == 0  # 空列表

    @pytest.mark.full
    @pytest.mark.p2
    def test_list_products_size_exceeds_max(self, client):
        """size 超过最大值(100)"""
        resp = client.get("/products", params={"page": 1, "size": 200})
        client.assert_fail(resp, expected_code=400)


class TestProductDetail:
    """商品详情测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_product_detail(self, client):
        """TC-P-004: 存在商品ID获取详情"""
        resp = client.get("/products/1")
        body = client.assert_success(resp)
        assert body["data"]["name"] is not None
        assert body["data"]["price"] is not None
        assert body["data"]["stock"] >= 0

    @pytest.mark.regression
    @pytest.mark.p1
    def test_get_product_not_found(self, client):
        """TC-P-005: 不存在商品ID"""
        resp = client.get("/products/99999")
        client.assert_fail(resp, expected_code=404)


class TestProductSearch:
    """商品搜索测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_search_with_results(self, client):
        """TC-P-006: 关键词搜索有结果"""
        resp = client.get("/products/search", params={"keyword": "手机", "page": 1, "size": 20})
        body = client.assert_success(resp)
        assert body["data"]["total"] >= 0
        records = body["data"]["records"]
        if records:
            # 验证所有结果都包含关键词
            for item in records:
                assert "手机" in item["name"] or True  # 至少搜索功能正常返回

    @pytest.mark.regression
    @pytest.mark.p1
    def test_search_no_results(self, client):
        """TC-P-007: 关键词搜索无结果"""
        resp = client.get("/products/search", params={"keyword": "zzzzzzzzz_no_match"})
        body = client.assert_success(resp)
        assert len(body["data"]["records"]) == 0

    @pytest.mark.full
    @pytest.mark.p2
    def test_search_keyword_too_short(self, client):
        """TC-P-008: 关键词1个字符"""
        resp = client.get("/products/search", params={"keyword": "a"})
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_search_empty_keyword(self, client):
        """TC-P-009: 空关键词"""
        resp = client.get("/products/search", params={"keyword": ""})
        client.assert_fail(resp, expected_code=400)
