"""数据库辅助工具 — 直接查询数据库验证数据状态"""

import pymysql
from typing import Optional


class DbHelper:
    """MySQL 数据库连接辅助类，用于测试数据验证"""

    def __init__(self, host="localhost", port=3306, user="root",
                 password="root", database="ecommerce"):
        self.conn = pymysql.connect(
            host=host, port=port, user=user,
            password=password, database=database,
            charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def query_one(self, sql: str, params=None) -> Optional[dict]:
        """查询单条记录"""
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def query_all(self, sql: str, params=None) -> list:
        """查询多条记录"""
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute(self, sql: str, params=None) -> int:
        """执行写操作，返回影响行数"""
        with self.conn.cursor() as cursor:
            rows = cursor.execute(sql, params)
            self.conn.commit()
            return rows

    # ---- 便捷查询方法 ----

    def get_user_by_username(self, username: str) -> Optional[dict]:
        return self.query_one("SELECT * FROM users WHERE username = %s", (username,))

    def get_product_stock(self, product_id: int) -> Optional[int]:
        row = self.query_one("SELECT stock FROM products WHERE id = %s", (product_id,))
        return row["stock"] if row else None

    def get_order_by_no(self, order_no: str) -> Optional[dict]:
        return self.query_one("SELECT * FROM orders WHERE order_no = %s", (order_no,))

    def get_cart_items(self, user_id: int) -> list:
        return self.query_all("SELECT * FROM cart_items WHERE user_id = %s", (user_id,))

    def count_addresses(self, user_id: int) -> int:
        row = self.query_one(
            "SELECT COUNT(*) as cnt FROM addresses WHERE user_id = %s AND deleted = 0",
            (user_id,))
        return row["cnt"] if row else 0

    # ---- 测试数据清理 ----

    def cleanup_user(self, username: str):
        """清理测试用户及相关数据"""
        user = self.get_user_by_username(username)
        if not user:
            return
        uid = user["id"]
        self.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE user_id = %s)", (uid,))
        self.execute("DELETE FROM orders WHERE user_id = %s", (uid,))
        self.execute("DELETE FROM cart_items WHERE user_id = %s", (uid,))
        self.execute("DELETE FROM addresses WHERE user_id = %s", (uid,))
        self.execute("DELETE FROM users WHERE id = %s", (uid,))

    def reset_product_stock(self, product_id: int, stock: int):
        """恢复商品库存"""
        self.execute("UPDATE products SET stock = %s, version = version + 1 WHERE id = %s",
                     (stock, product_id))

    def close(self):
        self.conn.close()
