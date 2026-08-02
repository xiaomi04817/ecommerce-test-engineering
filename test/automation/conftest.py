"""pytest 全局配置 — fixtures 与场景上下文管理"""

import pytest
from utils.api_client import ApiClient
from utils.data_generator import DataGenerator
#这是 pytest 的全局配置文件，
# 定义了所有测试文件共享的 fixtures、场景管理工具和自定义标记
# ============================================================
# Session 级配置
# ============================================================

BASE_URL = "http://localhost:8080/api"

#scope="session" 表示整个测试会话只执行一次，所有测试共享同一个值
@pytest.fixture(scope="session")
def base_url():
    """API 基础地址"""
    return BASE_URL


# ============================================================
# 测试用户管理
# ============================================================

@pytest.fixture(scope="session")
def test_user():
    """
    预置测试用户，Session 级复用。
    数据库初始化脚本中已预置: testuser1 / Test@123456
    """
    return {
        "username": "testuser1",
        "password": "Test@123456",
        "email": "test@example.com"
    }


@pytest.fixture(scope="session")
def auth_token(base_url, test_user):
    """
    全局共享登录 Token，Session 级复用，减少重复登录开销。
    """
    client = ApiClient(base_url)
    resp = client.post("/auth/login", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    body = resp.json()
    if body.get("code") == 200:
        return body["data"]["token"]
    else:
        # Fallback: try registering then login
        client.post("/auth/register", data={
            "username": test_user["username"],
            "password": test_user["password"],
            "email": test_user["email"]
        })
        resp = client.post("/auth/login", data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        return resp.json()["data"]["token"]


# ============================================================
# Function 级 Fixtures
# ============================================================

@pytest.fixture
def client(base_url):
    """未登录的 API 客户端（每个测试独立）"""
    return ApiClient(base_url)


@pytest.fixture
def auth_client(base_url, auth_token):
    """已登录的 API 客户端（每个测试独立，共享 token）"""
    return ApiClient(base_url, token=auth_token)


@pytest.fixture
def unique_user(base_url):
    """
    为测试生成唯一用户，测试结束后自动清理。
    用于注册/登录等需要干净状态的测试场景。
    """
    user_data = DataGenerator.unique_test_user()
    # 注册
    client = ApiClient(base_url)
    client.post("/auth/register", data=user_data)
    # 登录获取 token
    resp = client.post("/auth/login", data={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    body = resp.json()
    user_data["token"] = body["data"]["token"]
    user_data["id"] = body["data"]["user"]["id"]
    yield user_data
    # Teardown: 通过 DB 清理（需要 DB 连接，如不需要可跳过）
    # 可以通过 db_helper fixture 清理


@pytest.fixture
def db():
    """数据库连接（如需要可导入 DbHelper）"""
    from utils.db_helper import DbHelper
    db_helper = DbHelper()
    yield db_helper
    db_helper.close()


# ============================================================
# 场景上下文管理
# ============================================================

# 当前执行的场景 ID 和步骤序号，用于失败时定位
_scenario_context = {"scenario_id": None, "step": 0}


def set_scenario(scenario_id: str):
    """设置当前场景"""
    _scenario_context["scenario_id"] = scenario_id
    _scenario_context["step"] = 0


def step(description: str):
    """记录场景步骤"""
    _scenario_context["step"] += 1
    return f"[{_scenario_context['scenario_id']}] Step {_scenario_context['step']}: {description}"


def reset_scenario():
    """重置场景上下文"""
    _scenario_context["scenario_id"] = None
    _scenario_context["step"] = 0


# ============================================================
# pytest 钩子
# ============================================================

def pytest_runtest_setup(item):
    """每个测试用例开始前重置场景"""
    reset_scenario()


def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "regression: 回归测试")
    config.addinivalue_line("markers", "full: 全量测试")
    config.addinivalue_line("markers", "p0: 优先级P0")
    config.addinivalue_line("markers", "p1: 优先级P1")
    config.addinivalue_line("markers", "p2: 优先级P2")
    config.addinivalue_line("markers", "p3: 优先级P3")
