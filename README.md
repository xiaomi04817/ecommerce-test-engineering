# 电商测试工程项目

> 🎯 软件测试能力证明项目 — 从需求到自动化测试的完整测试体系

---

## 项目定位

本项目是一个**测试工程（Test Engineering）项目**，核心目标不是"做一个电商系统"，而是**构建完整的软件测试体系**，用于软件测试岗位的能力证明。

### 第一个项目 vs 第二个项目

| 维度 | 第一个项目 | 本项目 |
|------|----------|--------|
| 性质 | 流程练手 | 能力证明 |
| 重点 | 开发实现 | 测试体系 |
| 测试 | 学习型测试 | 工程级测试 |
| 目标 | 完成结课 | 简历 + 面试 |

---

## 项目结构

```
E_commerce_testing_project/
├── docs/                          # 📄 文档
│   ├── requirements.md            #   需求规格说明书
│   ├── test-design.md             #   测试设计文档
│   ├── rtm.md                     #   三向追踪矩阵 (REQ↔TC↔BUG)
│   ├── api-spec.yaml              #   OpenAPI 3.0 接口规范
│   └── bug-reports/               #   缺陷报告
├── backend/                       # 🖥️ Spring Boot 后端
├── frontend/                      # 🎨 Vue3 + Element Plus 前端
├── test/                          # 🧪 测试
│   ├── postman/                   #   Postman 接口测试集合
│   └── automation/                #   pytest 自动化测试框架
└── README.md
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Spring Boot 3.2 + MyBatis-Plus + MySQL + JWT |
| 前端 | Vue3 + Vite + Element Plus + Axios |
| 接口测试 | Postman Collection |
| 自动化测试 | Python + pytest + requests |
| API 规范 | OpenAPI 3.0 |

---

## 快速启动

### 1. 数据库
```sql
CREATE DATABASE ecommerce DEFAULT CHARACTER SET utf8mb4;
-- 启动后端后 schema.sql 自动初始化（需配置 spring.sql.init.mode）
```

### 2. 后端
```bash
cd backend
./mvnw spring-boot:run
# 服务启动在 http://localhost:8080
```

### 3. 前端
```bash
cd frontend
npm install
npm run dev
# 服务启动在 http://localhost:3000
```

### 4. 运行测试

**冒烟测试** (每次提交):
```bash
cd test/automation
pytest -m smoke --html=reports/smoke-report.html
```

**回归测试** (每日构建):
```bash
pytest -m "smoke or regression" --html=reports/regression-report.html
```

**全量测试** (发版前):
```bash
pytest -v --html=reports/full-report.html --self-contained-html
```

---

## 测试分层

| 层级 | 触发条件 | 用例数 | 耗时 | 通过标准 |
|------|---------|--------|------|---------|
| L1 Smoke | 每次提交 | ~18 | ≤5 min | 100% |
| L2 Regression | 每日构建 | ~60 | ≤30 min | 100% |
| L3 Full | 发版前 | ~120+ | ≥60 min | ≥98% |

---

## 核心业务场景

| 场景 | 描述 | 测试重点 |
|------|------|---------|
| S01 | 用户注册登录 | 参数校验、Token机制 |
| S02 | 商品浏览与搜索 | 分页、模糊搜索 |
| S03 | 购物车管理 | 权限隔离、数量边界 |
| S04 | 地址管理 | 格式校验、数量上限 |
| S05 | 完整下单链路 | 端到端流程 |
| S06 | 订单状态流转（正常） | 状态机合法路径 |
| S07 | 订单状态流转（异常） | 非法状态跳转拦截 |
| S08 | 未登录权限拦截 | 接口鉴权 |
| S09 | 参数校验边界值 | 边界值覆盖 |
| S10 | 并发场景 | 库存竞态、重复下单 |
