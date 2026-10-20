# 图书漂流管理系统

用户之间互相借阅图书的平台：用户发布自己的书，管理员审核后上架；其他用户申请借阅，发布人同意或拒绝；借书人申请归还，发布人确认或拒绝。整个借阅、归还流程是一个完整的闭环，每次流转都留有记录。

- 后端：Python 3.13 · FastAPI · SQLAlchemy 2 · MySQL 8（开发时可用 SQLite）· JWT · bcrypt
- 前端：Vue 3 · Vite · Element Plus · Pinia · Vue Router · Axios

## 功能

**普通用户**
- 注册（用户名不能重复、两次密码必须一致，默认是普通用户）、登录（下发 JWT）
- 发布图书：填写书名、作者、分类、新旧程度、简介，上传封面，提交后进入【待审核】
- 编辑、下架自己发布的图书；不能操作别人的书
- 首页只展示【待漂流】的图书，可以按书名、作者模糊搜索，也可以按分类筛选
- 图书详情：查看完整信息，查看和发表评论
- 借阅：提交借阅申请；发布人同意后图书变为【已借出】，拒绝则图书状态不变
- 归还：借书人提交归还申请；发布人确认后图书回到【待漂流】，拒绝则保持【已借出】
- 个人中心：基本信息、我发布的图书、我的借阅申请（可展开查看每次借还的完整时间线）、收到的借阅申请、收到的归还申请、我的归还记录

**管理员**（需要管理员 Token）
- 用户管理：查看全部用户，禁用或启用账号
- 图书审核：通过（变为待漂流）、驳回（变为已下架，可填写原因）、删除违规图书
- 分类管理：新增、修改、删除
- 查看全部借阅记录和归还记录

**通用**
- 未登录访问受保护接口返回 401；普通用户访问管理接口返回 403；操作别人的图书、申请返回 403
- 所有接口返回 `{code, msg, data}`，前端统一弹窗提示成功或失败

## 原需求没写清楚、这里补上的规则

| 场景 | 处理方式 |
|---|---|
| 评论 | 原文只有"查看评论"，补充了登录用户发表评论 |
| 多人同时申请同一本书 | 同意其中一条后，其余待处理申请自动变为【已失效】；同意操作用条件更新 `UPDATE ... WHERE status='AVAILABLE'`，并发时只会成功一次 |
| 借自己的书、重复申请 | 都不允许；同一用户对同一本书只能有一条待处理申请 |
| 过审后再改内容 | 编辑后重新进入【待审核】，被驳回或下架的书也能通过编辑重新提交 |
| 已借出的书 | 不能编辑，也不能下架 |
| 下架、重新审核、删除时已有的申请 | 待处理的借阅申请变为【已失效】 |
| 归还被拒 | 借书人可以再次提交，每次借阅同一时间最多只有一条待处理的归还申请 |
| 禁用用户 | 每次请求都查库确认账号状态，禁用后旧 Token 立即失效；管理员账号不能被禁用 |
| 删除违规图书 | 软删除，借还历史保留；已借出的书仍可以走完归还流程 |
| 删除分类 | 分类下还有图书时拒绝删除 |

## 图书状态流转

```
发布 → 待审核 ──管理员通过──→ 待漂流 ──发布人同意借阅──→ 已借出
        │  ↑                    │  ↑                        │
  管理员驳回  编辑        下架/编辑   └──── 发布人确认归还 ←──┘
        ↓  │                    ↓                 （拒绝归还：保持已借出）
        已下架 ←────────────────┘
```

## 本地运行

### 后端

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env            # 按需修改；不改则使用 SQLite 文件 library.db
.venv/bin/uvicorn app.main:app --reload --port 8000
```

首次启动会自动建表，并创建管理员账号和默认分类。接口文档：http://localhost:8000/docs

使用 MySQL 时，先建库（`CREATE DATABASE library DEFAULT CHARSET utf8mb4;`），再把 `.env` 里的 `DATABASE_URL` 改成 `mysql+pymysql://用户:密码@127.0.0.1:3306/library?charset=utf8mb4`。

### 前端

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173，/api 和 /uploads 代理到 8000 端口
```

### 默认管理员

用户名 `admin`，密码 `admin123`（由 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 控制，只在账号不存在时创建）。**部署前务必修改密码和 `JWT_SECRET`。**

## Docker 部署

```bash
cp .env.example .env             # 必须设置 JWT_SECRET
docker compose up -d --build
```

访问 http://localhost:8080 。会启动 MySQL 8.4、后端和 Nginx（托管前端，并把 `/api`、`/uploads` 转发给后端）三个容器；数据库数据和上传的封面保存在 Docker 卷里。

## 测试

```bash
cd backend
.venv/bin/python -m pytest              # 默认使用内存 SQLite
# 针对 MySQL 跑同一套测试（会删表重建，请使用单独的测试库）
TEST_DATABASE_URL="mysql+pymysql://root:密码@127.0.0.1:3306/library_test?charset=utf8mb4" .venv/bin/python -m pytest
```

测试覆盖：注册登录校验、禁用后 Token 失效、未登录/非管理员/越权操作的权限矩阵、完整借还闭环（含拒绝归还后再次提交）、并发同意时的条件更新、编辑后重新审核、软删除后历史保留、封面上传的文件类型校验。

## 目录结构

```
backend/
  app/
    main.py              应用入口：路由、异常处理、静态文件、启动时建表和初始化数据
    config.py            配置（读取环境变量 / .env）
    models.py            数据表和状态枚举
    schemas.py           请求、响应模型和参数校验
    core/                统一返回、异常处理、JWT、鉴权依赖、分页
    services/            图书状态流转、借阅归还状态机
    routers/             接口
  tests/
frontend/
  src/
    api/                 Axios 封装（带 Token、统一弹窗）和接口定义
    router/              路由和登录 / 管理员守卫
    stores/              登录状态
    views/               页面：首页、详情、发布编辑、个人中心、管理后台
docker-compose.yml
```

## 主要接口

所有接口前缀为 `/api`。

| 模块 | 接口 |
|---|---|
| 认证 | `POST /auth/register` `POST /auth/login` `GET /users/me` |
| 图书 | `GET /books` `GET /books/{id}` `POST /books` `PUT /books/{id}` `POST /books/{id}/off-shelf` `GET /users/me/books` `GET /categories` |
| 评论 | `GET /books/{id}/comments` `POST /books/{id}/comments` |
| 上传 | `POST /uploads/cover`（JPG/PNG/WEBP，≤2MB，按文件头校验） |
| 借阅 | `POST /borrows` `GET /borrows/mine` `GET /borrows/received` `POST /borrows/{id}/approve` `POST /borrows/{id}/reject` |
| 归还 | `POST /returns` `GET /returns/mine` `GET /returns/received` `POST /returns/{id}/confirm` `POST /returns/{id}/reject` |
| 管理员 | `GET /admin/users` `PUT /admin/users/{id}/status` `GET /admin/books` `POST /admin/books/{id}/approve` `POST /admin/books/{id}/reject` `DELETE /admin/books/{id}` `POST/PUT/DELETE /admin/categories` `GET /admin/borrows` `GET /admin/returns` |
