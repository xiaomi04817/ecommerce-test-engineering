import requests

# 1.登录成功
def test_success_login(base_url):
    resp = requests.post(f"{base_url}/api/auth/login",
    json = {"username":"testuser1","password":"Test@123456"},
    timeout = 10
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200 ,f"错误信息{body.get('message')}"
    assert body["data"]["token"] != None,f"错误信息{body.get('message')}"


# 2.登录失败---密码错误
def test_fail_login(base_url):
    resp = requests.post(f"{base_url}/api/auth/login",
    json = {"username":"testuser1","password":"wrongpassword"},timeout = 10)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 401, f"错误信息{body.get('message')}"
    assert body["data"] is None, f"错误信息{body.get('message')}"

# 3.获取商品列表
def test_requires_goods(base_url):
    resp = requests.get(f"{base_url}/api/products",timeout=10)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) > 0,"商品列表不应为空"

# 4.未登录访问用户信息
def test_unlogin_user_info(base_url):
    resp = requests.get(f"{base_url}/api/users/me",timeout=10)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 401,f"错误信息{body.get('message')}"

# 5.带token查看用户信息
def test_login_user_info(base_url,auth_headers):
    resp = requests.get(f"{base_url}/api/users/me",headers = auth_headers,timeout=10)
    assert resp.status_code == 200
    body = resp.json()
    assert body['code'] == 200,f"错误信息{body.get('message')}"
    assert body['data']['id'] is not None,f"错误信息{body.get('message')}"
    assert "password" not in body['data']

# 6.搜索商品
def test_search_goods(base_url):
    resp = requests.get(f"{base_url}/api/products/search?keyword=手机&page=1&size=20",timeout=10)
    assert resp.status_code == 200
    body = resp.json()
    assert body['data']['records'] is not None,f"错误信息{body.get('message')}"
    assert body['data']['total'] > 0,f"错误信息{body.get('message')}"

#7.查看商品详情
def test_requires_goods_info(base_url):
    resp = requests.get(f"{base_url}/api/products/1",timeout=10)
    assert resp.status_code == 200
    body = resp.json()
    required_fields = ["id", "name", "price", "stock", "description"]
    for field in required_fields:
        assert field in body['data'], f"缺少字段: {field}"
    assert body['data']['price'] > 0,"价格应该大于零"
    assert body['data']['stock'] >= 0,"数量应该大于等于零"

#8.注册 — 用户名已存在
def test_repeat_login(base_url):
    resp = requests.post(f"{base_url}/api/auth/register",
    json = {"username":"testuser1","password":"Test@123456","email":"123@qq.com"},
    timeout = 10
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] != 200 ,"重复用户名不应该注册成功"

#9.查看订单列表（需登录）
def test_requires_oeders_info(base_url,auth_headers):
    resp = requests.get(f"{base_url}/api/orders?page=1&size=20",
    headers = auth_headers,timeout=10)
    assert resp.status_code == 200
    body = resp.json()
    assert body['code'] == 200,f"错误信息{body.get('message')}"

#10.加购 — 数量为负
def test_add_items(base_url,auth_headers):
    resp = requests.post(f"{base_url}/api/cart/items",
    headers=auth_headers,
    json={"productId":1,"quantity":-1},
    timeout=10)
    assert resp.status_code == 200
    body = resp.json()
    assert body['code'] != 200,"负数不应该添加成功"
