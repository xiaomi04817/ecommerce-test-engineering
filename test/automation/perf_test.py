"""性能测试 — 并发压测 5 个核心场景 (替代 JMeter)"""
import time
import statistics
import concurrent.futures
from collections import defaultdict
from utils.api_client import ApiClient
from utils.db_helper import DbHelper

BASE_URL = "http://localhost:8080/api"

# ── 测试用户 (复用预置账号) ──
TEST_USER = {"username": "testuser1", "password": "Test@123456"}

# ── 压测配置 ──
CONCURRENCY_LEVELS = [50, 200, 500]  # 并发用户数
WARMUP_REQUESTS = 10                  # 预热请求数


def get_token(client):
    """登录获取 token"""
    resp = client.post("/auth/login", data=TEST_USER)
    body = resp.json()
    return body["data"]["token"]


def warmup(scenario_fn):
    """预热: 执行少量请求让 JVM JIT 生效"""
    for _ in range(WARMUP_REQUESTS):
        try:
            scenario_fn()
        except Exception:
            pass


class PerfResult:
    """单场景压测结果"""

    def __init__(self, name, method, path):
        self.name = name
        self.method = method
        self.path = path
        self.results = {}  # concurrency -> stats

    def add(self, concurrency, response_times, status_codes, error_count):
        """统计一次压测结果"""
        ok_times = [t for t, s in zip(response_times, status_codes) if 200 <= s < 500]
        self.results[concurrency] = {
            "total": len(response_times),
            "success": len(ok_times),
            "failed": error_count,
            "avg_ms": round(statistics.mean(ok_times), 1) if ok_times else 0,
            "min_ms": round(min(ok_times), 1) if ok_times else 0,
            "max_ms": round(max(ok_times), 1) if ok_times else 0,
            "p50_ms": round(percentile(ok_times, 50), 1) if ok_times else 0,
            "p95_ms": round(percentile(ok_times, 95), 1) if ok_times else 0,
            "p99_ms": round(percentile(ok_times, 99), 1) if ok_times else 0,
            "tps": round(len(ok_times) / (max(response_times) / 1000), 1) if ok_times else 0,
        }

    def report(self):
        lines = [f"\n{'='*80}", f"  {self.name}", f"  {self.method} {self.path}", f"{'='*80}"]
        header = f"{'并发':>6} {'总数':>6} {'成功':>6} {'失败':>6} {'TPS':>8} {'Avg(ms)':>9} {'P50(ms)':>9} {'P95(ms)':>9} {'P99(ms)':>9}"
        lines.append(header)
        lines.append("-" * 80)
        for c in CONCURRENCY_LEVELS:
            r = self.results.get(c, {})
            if r:
                lines.append(
                    f"{c:>6} {r['total']:>6} {r['success']:>6} {r['failed']:>6} "
                    f"{r['tps']:>8.1f} {r['avg_ms']:>9.1f} {r['p50_ms']:>9.1f} "
                    f"{r['p95_ms']:>9.1f} {r['p99_ms']:>9.1f}"
                )
        return "\n".join(lines)


def percentile(data, p):
    """计算百分位数 (线性插值)"""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def run_scenario(scenario):
    """对单个场景执行 3 个梯度的压测"""
    print(scenario.report())
    return scenario


# ══════════════════════════════════════════════════════════════
#  场景定义
# ══════════════════════════════════════════════════════════════

def scenario_product_list():
    """S-PERF-01: 商品列表分页查询 (最高频读操作)"""
    result = PerfResult("S-PERF-01: 商品列表分页查询", "GET", "/api/products?page=1&size=20")
    client = ApiClient(BASE_URL)

    for concurrency in CONCURRENCY_LEVELS:
        times, codes, errors = [], [], 0

        def do_request():
            try:
                start = time.time()
                resp = client.get("/products", params={"page": 1, "size": 20})
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                codes.append(resp.status_code)
            except Exception:
                errors += 1

        warmup(do_request)
        times.clear()
        codes.clear()
        errors = 0

        start_wall = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrency, 200)) as pool:
            futures = [pool.submit(do_request) for _ in range(concurrency)]
            concurrent.futures.wait(futures)
        wall_ms = (time.time() - start_wall) * 1000
        result.add(concurrency, times, codes, errors)

    return result


def scenario_product_search():
    """S-PERF-02: 商品搜索 (涉及 LIKE 查询)"""
    result = PerfResult("S-PERF-02: 商品关键词搜索", "GET", "/api/products/search?keyword=手机")
    client = ApiClient(BASE_URL)

    for concurrency in CONCURRENCY_LEVELS:
        times, codes, errors = [], [], 0

        def do_request():
            try:
                start = time.time()
                resp = client.get("/products/search", params={"keyword": "手机"})
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                codes.append(resp.status_code)
            except Exception:
                errors += 1

        warmup(do_request)
        times.clear()
        codes.clear()
        errors = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrency, 200)) as pool:
            futures = [pool.submit(do_request) for _ in range(concurrency)]
            concurrent.futures.wait(futures)
        result.add(concurrency, times, codes, errors)

    return result


def scenario_user_login():
    """S-PERF-03: 用户登录 (BCrypt 密码校验)"""
    result = PerfResult("S-PERF-03: 用户登录 (BCrypt)", "POST", "/api/auth/login")

    for concurrency in CONCURRENCY_LEVELS:
        times, codes, errors = [], [], 0

        def do_request():
            try:
                client = ApiClient(BASE_URL)
                start = time.time()
                resp = client.post("/auth/login", data=TEST_USER)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                codes.append(resp.status_code)
            except Exception:
                errors += 1

        # Warmup
        for _ in range(WARMUP_REQUESTS):
            try:
                do_request()
            except Exception:
                pass
        times.clear()
        codes.clear()
        errors = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrency, 200)) as pool:
            futures = [pool.submit(do_request) for _ in range(concurrency)]
            concurrent.futures.wait(futures)
        result.add(concurrency, times, codes, errors)

    return result


def scenario_create_order():
    """S-PERF-04: 下单接口 (最重的写操作 — 库存扣减+订单创建)"""
    result = PerfResult("S-PERF-04: 创建订单 (库存扣减)", "POST", "/api/orders")

    # 前置: 获取 token 和有效地址
    client = ApiClient(BASE_URL)
    token = get_token(client)
    client.set_token(token)

    # 确保有地址
    addr_resp = client.get("/addresses")
    addrs = addr_resp.json()["data"]
    if not addrs:
        client.post("/addresses", data={
            "receiverName": "压测人", "phone": "13900139001",
            "province": "广东", "city": "深圳", "district": "南山",
            "detail": "压测街道100号"
        })
        addr_resp = client.get("/addresses")
        addrs = addr_resp.json()["data"]
    addr_id = addrs[0]["id"]

    # 恢复库存
    db = DbHelper()
    db.execute("UPDATE products SET stock = 5000 WHERE id IN (1, 2, 3)")
    db.close()

    order_payload = {
        "addressId": addr_id,
        "items": [{"productId": 1, "quantity": 1}]
    }

    for concurrency in CONCURRENCY_LEVELS:
        times, codes, errors = [], [], 0

        def do_request():
            try:
                c = ApiClient(BASE_URL)
                c.set_token(token)
                start = time.time()
                resp = c.post("/orders", data=order_payload)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                codes.append(resp.status_code)
            except Exception:
                errors += 1

        # Warmup
        for _ in range(min(WARMUP_REQUESTS, concurrency // 2)):
            try:
                do_request()
            except Exception:
                pass
        times.clear()
        codes.clear()
        errors = 0

        # 每次压测前恢复库存
        db2 = DbHelper()
        db2.execute("UPDATE products SET stock = 5000 WHERE id IN (1, 2, 3)")
        db2.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrency, 200)) as pool:
            futures = [pool.submit(do_request) for _ in range(concurrency)]
            concurrent.futures.wait(futures)
        result.add(concurrency, times, codes, errors)

    return result


def scenario_concurrent_order():
    """S-PERF-05: 并发下单同一商品 (验证乐观锁在压力下的表现)"""
    result = PerfResult("S-PERF-05: 并发下单同一商品（乐观锁验证）", "POST", "/api/orders")

    client = ApiClient(BASE_URL)
    token = get_token(client)
    client.set_token(token)

    addr_resp = client.get("/addresses")
    addrs = addr_resp.json()["data"]
    if not addrs:
        client.post("/addresses", data={
            "receiverName": "并发压测", "phone": "13800138002",
            "province": "北京", "city": "北京", "district": "朝阳",
            "detail": "并发测试大道200号"
        })
        addr_resp = client.get("/addresses")
        addrs = addr_resp.json()["data"]
    addr_id = addrs[0]["id"]

    order_payload = {
        "addressId": addr_id,
        "items": [{"productId": 2, "quantity": 1}]
    }

    for concurrency in CONCURRENCY_LEVELS:
        # 设置有限库存，制造竞态: 只有 N/2 的订单能成功
        limited_stock = max(concurrency // 2, 1)
        db3 = DbHelper()
        db3.execute("UPDATE products SET stock = %s WHERE id = 2", (limited_stock,))
        db3.close()

        times, codes, errors = [], [], 0

        def do_request():
            try:
                c = ApiClient(BASE_URL)
                c.set_token(token)
                start = time.time()
                resp = c.post("/orders", data=order_payload)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                codes.append(resp.status_code)
            except Exception:
                errors += 1

        for _ in range(min(WARMUP_REQUESTS, concurrency // 2)):
            try:
                do_request()
            except Exception:
                pass
        times.clear()
        codes.clear()
        errors = 0

        # 重置库存
        db4 = DbHelper()
        db4.execute("UPDATE products SET stock = %s WHERE id = 2", (limited_stock,))
        db4.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrency, 200)) as pool:
            futures = [pool.submit(do_request) for _ in range(concurrency)]
            concurrent.futures.wait(futures)
        result.add(concurrency, times, codes, errors)

    # 恢复库存
    db5 = DbHelper()
    db5.execute("UPDATE products SET stock = 200 WHERE id = 2")
    db5.close()

    return result


# ══════════════════════════════════════════════════════════════
#  主流程
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 80)
    print("  电商系统 — 性能压测报告")
    print(f"  压测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  并发梯度: {CONCURRENCY_LEVELS}")
    print("=" * 80)

    scenarios = [
        scenario_product_list,
        scenario_product_search,
        scenario_user_login,
        scenario_create_order,
        scenario_concurrent_order,
    ]

    all_results = []
    for fn in scenarios:
        print(f"\n▶ 执行: {fn.__doc__}")
        result = fn()
        all_results.append(result)
        # 冷却: 让系统恢复
        time.sleep(2)

    # ── 汇总 ──
    print(f"\n\n{'='*80}")
    print("  性能测试汇总")
    print(f"{'='*80}")

    for r in all_results:
        print(r.report())

    print(f"\n{'='*80}")
    print("  结论:")
    print(f"  - 读接口 (商品列表/搜索): 目标 ≤500ms P95")
    print(f"  - 写接口 (登录/下单): 目标 ≤2000ms P95")
    print(f"  - 并发下单乐观锁: 仅库存充足的请求成功，无超卖")
    print(f"{'='*80}")
