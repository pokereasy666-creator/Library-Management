# Windows 部署指南（本机开发 / 答辩演示）

适用于 Windows 10 / 11 64 位。默认使用 SQLite 文件数据库，不需要安装数据库软件。

## 1. 需要安装的软件

| 软件 | 版本 | 用途 | 是否必需 |
|---|---|---|---|
| Python | **3.13.x 64 位**（3.14 也可以） | 运行后端 | 必需 |
| Node.js | **22 LTS**（至少 22.12；24 LTS 也可以） | 运行前端 | 必需 |
| Git for Windows | 最新版 | 下载代码 | 可选，也可以下载 ZIP |
| MySQL | 8.4 LTS | 数据库 | 可选，见第 5 节 |

- **不要安装 Python 3.15。** 后端依赖里的 PyYAML 还没有 Python 3.15 的 Windows 安装包，安装会失败。python.org 首页推荐的可能是最新版，请在 [Windows 下载页](https://www.python.org/downloads/windows/) 里找 3.13 的 **Windows installer (64-bit)**。
- 安装 Python 时勾选 **Add python.exe to PATH**，安装程序会同时装好 `py` 启动器。
- **不需要** Visual Studio 或 C++ 编译工具：在 Python 3.13 / 3.14 下，后端所有依赖都有 Windows 64 位预编译包。
- PowerShell 用 Windows 自带的 5.1 即可，不用另外安装。

其余依赖由脚本自动安装：
- 后端（`backend/requirements.txt`）：FastAPI、Uvicorn、SQLAlchemy、Pydantic、PyJWT、bcrypt、python-multipart、PyMySQL、cryptography
- 前端（`frontend/package.json`）：Vue 3、Vue Router、Pinia、Axios、Element Plus、Vite

## 2. 获取代码

```powershell
git clone https://github.com/pokereasy666-creator/Library-Management.git
cd Library-Management
git checkout claude/keen-fermi-1ksh5u
```

代码合并到 main 分支之前，需要切换到 `claude/keen-fermi-1ksh5u` 分支。不用 Git 的话，在 GitHub 上切换到这个分支后点 **Code → Download ZIP**，解压即可。

## 3. 一键安装和启动（推荐）

### 第一次：双击 `setup.bat`

它会依次完成以下工作：
1. 检查 Python 3.13 / 3.14（64 位）和 Node.js 版本，不满足时提示去哪里下载
2. 创建后端虚拟环境 `backend\.venv`，安装后端依赖
3. 从 `backend\.env.example` 生成 `backend\.env`，并写入随机的 `JWT_SECRET`。已有 `.env` 时不会覆盖
4. 安装前端依赖（`npm ci`）

依赖下载很慢或超时时，改用国内镜像源。在项目目录的地址栏输入 `cmd` 回车，然后运行：

```bat
setup.bat -Mirror
```

`-Mirror` 会让 pip 使用清华源、npm 使用 npmmirror。中途失败可以重复运行，已经完成的步骤会跳过或很快完成。

### 每次使用：双击 `start.bat`

- 会弹出两个窗口：**图书漂流 - 后端**、**图书漂流 - 前端**。
- 两边都就绪后自动打开浏览器访问 http://localhost:5173 。
- 管理员账号：`admin` / `admin123`。想换初始密码，请在**第一次启动前**修改 `backend\.env` 里的 `ADMIN_PASSWORD`。
- 接口文档：http://127.0.0.1:8000/docs
- **停止系统**：关闭那两个窗口。

需要时可以在命令行加参数（打开方式同上）：

- `start.bat -BackendPort 8001`：8000 端口被占用或被系统保留时，后端换端口
- `start.bat -Lan`：允许同一局域网的其他电脑访问，见第 6 节

## 4. 手动安装和启动（不用脚本时）

在 PowerShell 中执行。

**后端（第一个窗口）**

```powershell
cd backend
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
notepad .env          # 至少把 JWT_SECRET 改成一串随机字符
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

- 必须在 `backend` 目录下启动：数据库文件 `library.db` 和上传目录 `uploads\` 都会建在当前目录下。
- `--reload` 会在修改代码后自动重启，适合开发。演示时可以去掉。

**前端（第二个窗口）**

```powershell
cd frontend
npm ci
npm run dev
```

**说明**
- `.env` 请用复制模板再编辑的方式创建，**不要**用 `echo ... > .env`：Windows 自带的 PowerShell 5.1 会把它存成 UTF-16 编码，后端读取时会出错。
- 如果 PowerShell 提示 `无法加载文件 ...\npm.ps1，因为在此系统上禁止运行脚本`，执行一次下面的命令后重开窗口；也可以把 `npm` 换成 `npm.cmd`：

  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```

## 5. 改用 MySQL 8.4（可选）

1. 下载 MySQL Community Server **8.4 LTS** 的 Windows MSI 安装包。安装完成后，用自带的 MySQL Configurator 设置 root 密码，并保持 3306 端口。
2. 打开开始菜单里的 **MySQL 8.4 Command Line Client**，输入 root 密码后建库：

   ```sql
   CREATE DATABASE library DEFAULT CHARACTER SET utf8mb4;
   ```

3. 修改 `backend\.env`：

   ```
   DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/library?charset=utf8mb4
   ```

   密码中的特殊字符要转义：`@` 写成 `%40`，`:` 写成 `%3A`，`/` 写成 `%2F`。

4. 重新启动后端，数据表和管理员账号会自动创建。

## 6. 局域网演示

1. 用 `start.bat -Lan` 启动；手动启动时改用 `npm run dev -- --host`。
2. 在"图书漂流 - 前端"窗口里找到 `Network: http://192.168.x.x:5173/` 这一行，其他电脑用这个地址访问。
3. Windows 防火墙弹窗询问时，允许 Node.js 访问**专用网络**。

只需要开放 5173 端口：前端会把接口请求转发给本机的后端，后端不对外暴露。

## 7. 数据存放、备份与重置

| 内容 | 位置 |
|---|---|
| 数据库（SQLite） | `backend\library.db` |
| 上传的封面图片 | `backend\uploads\` |
| 配置 | `backend\.env` |

- **备份**：关闭两个窗口后，复制上面三项。
- **重置为空系统**：关闭两个窗口，删除 `library.db` 和 `uploads` 文件夹，再次启动时会重新建表、创建管理员和默认分类。

## 8. 运行测试

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
```

测试使用内存数据库，不会影响 `library.db`。想针对 MySQL 跑测试，必须使用单独的测试库，因为测试会删表重建：

```powershell
$env:TEST_DATABASE_URL = "mysql+pymysql://root:密码@127.0.0.1:3306/library_test?charset=utf8mb4"
.venv\Scripts\python.exe -m pytest
Remove-Item Env:TEST_DATABASE_URL
```

## 9. 常见问题

| 现象 | 原因和解决 |
|---|---|
| `setup.bat` 提示没有找到 Python 3.13 / 3.14 | 没装、装成了 32 位，或只装了 3.15。安装 3.13 64 位后重新打开窗口 |
| `pip install` 提示需要编译或需要 Rust | 用的是 Python 3.15，原因同上 |
| `setup.bat` 提示已有的 `backend\.venv` 版本不对 | 删除 `backend\.venv` 文件夹后重新运行 |
| 后端窗口报 `[WinError 10013]` 或 `address already in use` | 8000 端口被占用，或被 Hyper-V / WSL 保留（可用 `netsh interface ipv4 show excludedportrange protocol=tcp` 查看）。改用 `start.bat -BackendPort 8001` |
| `start.bat` 提示端口已被占用 | 系统可能已经在运行，先关闭之前的两个窗口 |
| `npm.ps1` 或 `Activate.ps1` 被禁止运行 | 见第 4 节的执行策略说明；一键脚本不受影响 |
| pip / npm 下载慢或超时 | 运行 `setup.bat -Mirror` |
| 后端启动时报 `.env` 编码错误 | `.env` 被存成了 UTF-16。删除后重新运行 `setup.bat`，或用记事本另存为 UTF-8 |
| 修改 `ADMIN_PASSWORD` 后登录不了 | 管理员账号只在数据库里还没有 admin 时创建一次。开发环境可以按第 7 节重置 |
| 页面提示"网络错误" | 后端窗口被关了或报错了，查看"图书漂流 - 后端"窗口 |

## Docker 部署

如果装了 Docker Desktop（需要 WSL2），也可以用一条命令启动 MySQL、后端和 Nginx，见 [README 的 Docker 部署一节](../README.md#docker-部署)。
