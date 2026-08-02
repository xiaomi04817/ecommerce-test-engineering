"""测试数据生成器 — 为测试用例提供随机合法数据"""

import random
import string
import uuid


class DataGenerator:
    """生成合法的测试数据"""

    @staticmethod
    def random_username() -> str:
        """生成随机用户名: 字母开头，3-20位"""
        prefix = random.choice(string.ascii_letters)
        suffix_len = random.randint(2, 19)
        suffix = ''.join(random.choices(string.ascii_letters + string.digits + "_", k=suffix_len))
        return prefix + suffix

    @staticmethod
    def random_password(min_len=8, max_len=15) -> str:
        """生成随机密码（含字母+数字）"""
        letters = ''.join(random.choices(string.ascii_letters, k=random.randint(min_len - 2, max_len - 2)))
        digits = ''.join(random.choices(string.digits, k=2))
        return letters + digits

    @staticmethod
    def random_email() -> str:
        """生成随机邮箱"""
        return f"test_{uuid.uuid4().hex[:8]}@example.com"

    @staticmethod
    def random_phone() -> str:
        """生成随机中国大陆手机号"""
        prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                    "150", "151", "152", "153", "155", "156", "157", "158", "159",
                    "180", "181", "182", "183", "184", "185", "186", "187", "188", "189"]
        return random.choice(prefixes) + ''.join(random.choices(string.digits, k=8))

    @staticmethod
    def random_receiver_name() -> str:
        """生成随机收件人姓名"""
        surnames = ["张", "李", "王", "赵", "陈", "杨", "黄", "周", "吴", "徐", "刘", "林"]
        return random.choice(surnames) + random.choice(["明", "华", "强", "丽", "伟", "芳", "敏", "静", "勇", "军"])

    @staticmethod
    def random_address_detail() -> str:
        """生成随机详细地址"""
        roads = ["科技园路", "人民路", "中山路", "建设路", "解放路", "长安街", "南京路"]
        districts = ["A座", "B座", "C座", "1栋", "2栋"]
        return f"{random.choice(roads)}{random.randint(1,999)}号{random.choice(districts)}{random.randint(101, 9999)}室"

    @staticmethod
    def random_order_remark() -> str:
        """生成随机订单备注"""
        remarks = ["请尽快发货", "发顺丰", "工作日配送", "周末配送", "放快递柜", ""]
        return random.choice(remarks)

    @staticmethod
    def unique_test_user() -> dict:
        """生成唯一的测试用户数据"""
        return {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": f"Test@{random.randint(100000, 999999)}",
            "email": DataGenerator.random_email()
        }
