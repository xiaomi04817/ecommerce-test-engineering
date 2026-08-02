"""用户模块测试 — 注册、登录、获取用户信息 (场景 S01)"""
import pytest
import uuid


class TestUserRegister:
    """用户注册测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_register_success(self, client):
        """TC-U-001: 有效输入注册成功"""
        resp = client.post("/auth/register", data={
            "username": f"regtest_{uuid.uuid4().hex[:6]}",
            "password": "Pass@123",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com"
        })
        body = client.assert_success(resp)
        assert body["data"]["username"] is not None
        # 密码不应返回
        assert "password" not in str(body["data"])

    @pytest.mark.regression
    @pytest.mark.p1
    def test_register_duplicate_username(self, client, test_user):
        """TC-U-005: 重复用户名注册"""
        resp = client.post("/auth/register", data={
            "username": test_user["username"],
            "password": "Pass@123",
            "email": "another@example.com"
        })
        client.assert_fail(resp, expected_code=400, message_contains="用户名已存在")

    @pytest.mark.regression
    @pytest.mark.p1
    def test_register_empty_username(self, client):
        """TC-U-002: 用户名为空"""
        resp = client.post("/auth/register", data={
            "username": "",
            "password": "Pass@123",
            "email": "test@example.com"
        })
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_register_short_username(self, client):
        """TC-U-003: 用户名长度不足(2位)"""
        resp = client.post("/auth/register", data={
            "username": "ab",
            "password": "Pass@123",
            "email": "test@example.com"
        })
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_register_username_starts_with_number(self, client):
        """TC-U-004: 用户名数字开头"""
        resp = client.post("/auth/register", data={
            "username": "1abcde",
            "password": "Pass@123456",
            "email": "num@example.com"
        })
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_register_weak_password(self, client):
        """TC-U-007: 纯数字密码"""
        resp = client.post("/auth/register", data={
            "username": f"weak_{uuid.uuid4().hex[:6]}",
            "password": "12345678",
            "email": "test@example.com"
        })
        # 应返回失败（密码需含字母+数字）
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p2
    def test_register_invalid_email(self, client):
        """TC-U-008: 非法邮箱格式"""
        resp = client.post("/auth/register", data={
            "username": f"emailtest_{uuid.uuid4().hex[:6]}",
            "password": "Pass@123",
            "email": "invalid-email"
        })
        client.assert_fail(resp, expected_code=400)

    # ---- 新增: 密码边界值 & 用户名格式扩展 ----

    @pytest.mark.full
    @pytest.mark.p2
    def test_register_password_7_chars(self, client):
        """TC-U-B01: 密码仅7位字符(边界值, 最小8位)"""
        resp = client.post("/auth/register", data={
            "username": f"pw7_{uuid.uuid4().hex[:6]}",
            "password": "Abc@123",
            "email": "test@example.com"
        })
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.full
    @pytest.mark.p2
    def test_register_password_exactly_8_chars(self, client):
        """TC-U-B02: 密码恰好8位(边界值, 有效)"""
        resp = client.post("/auth/register", data={
            "username": f"pw8_{uuid.uuid4().hex[:6]}",
            "password": "Abc@1234",
            "email": "test@example.com"
        })
        client.assert_success(resp)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_register_username_with_symbols(self, client):
        """TC-U-B03: 用户名包含@/#/空格等特殊字符"""
        resp = client.post("/auth/register", data={
            "username": "user@name",
            "password": "Pass@123",
            "email": "test@example.com"
        })
        client.assert_fail(resp, expected_code=400)

    @pytest.mark.regression
    @pytest.mark.p2
    def test_register_password_all_letters(self, client):
        """TC-U-B04: 密码纯字母(不含数字, 必须含字母+数字)"""
        resp = client.post("/auth/register", data={
            "username": f"allalpha_{uuid.uuid4().hex[:6]}",
            "password": "Abcdefgh",
            "email": "test@example.com"
        })
        client.assert_fail(resp, expected_code=400)


class TestUserLogin:
    """用户登录测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_login_success(self, client, test_user):
        """TC-U-009: 正确用户名密码登录"""
        resp = client.post("/auth/login", data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        body = client.assert_success(resp)
        assert "token" in body["data"]
        assert body["data"]["user"]["username"] == test_user["username"]

    @pytest.mark.regression
    @pytest.mark.p1
    def test_login_wrong_password(self, client, test_user):
        """TC-U-010: 错误密码登录"""
        resp = client.post("/auth/login", data={
            "username": test_user["username"],
            "password": "WrongPass999"
        })
        client.assert_fail(resp, expected_code=401)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_login_nonexistent_user(self, client):
        """TC-U-011: 不存在用户登录"""
        resp = client.post("/auth/login", data={
            "username": f"noexist_{uuid.uuid4().hex[:6]}",
            "password": "Pass@123"
        })
        client.assert_fail(resp, expected_code=401)

    @pytest.mark.full
    @pytest.mark.p2
    def test_login_empty_fields(self, client):
        """TC-U-012: 空用户名密码"""
        resp = client.post("/auth/login", data={"username": "", "password": ""})
        client.assert_fail(resp, expected_code=401)


class TestGetUserInfo:
    """获取当前用户信息测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_get_user_info(self, auth_client, test_user):
        """TC-U-013: 有效Token获取信息"""
        resp = auth_client.get("/users/me")
        body = auth_client.assert_success(resp)
        assert body["data"]["username"] == test_user["username"]

    @pytest.mark.regression
    @pytest.mark.p0
    def test_get_user_info_no_token(self, client):
        """TC-U-014: 无效Token"""
        resp = client.get("/users/me")
        client.assert_fail(resp, expected_code=401)

    @pytest.mark.regression
    @pytest.mark.p1
    def test_get_user_info_invalid_token(self, client):
        """无效Token字符串"""
        client.set_token("invalid.token.here")
        resp = client.get("/users/me")
        client.assert_fail(resp, expected_code=401)
