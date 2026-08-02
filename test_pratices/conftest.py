import pytest
import requests
# 共享 Fixtures：base_url、登录token、requests session
# 导入pytest测试框架、http请求库requests
# 全局常量：接口服务地址、测试账号
#
BASE_URL = 'http://localhost:8080'
TEST_USER = {
    "username":"testuser1",
    "password":"Test@123456"
}
# API 基础地址
# fixture 返回基础url，其他夹具/测试用例直接注入使用
@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

# 登录一次，拿到 token，整个测试会话复用
# 调用登录接口
# json格式传账号密码
# 第一层断言：校验HTTP状态码，网络/网关异常在这里拦截
# # 将返回的json字符串解析为python字典
@pytest.fixture(scope="session")
def auth_token(base_url):
    resp = requests.post(f"{base_url}/api/auth/login",
        json = TEST_USER,
        timeout=10)
    # 请求超时时间10秒
    assert resp.status_code == 200, f"错误信息：{resp.text}"
    token = resp.json()['data']['token']
    return token

@pytest.fixture
def auth_headers(auth_token):
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }




