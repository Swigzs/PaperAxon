# PaperAxon

基于多智能体架构的学术论文辅助系统：解读论文、相关检索、记忆存储、中文播客生成。

**运行环境**：WSL / Linux（开发与生产均在 Linux 环境下运行）。

## 技术栈

- **后端**：Python 3.10+、FastAPI、LangGraph、LangChain、Qwen API、SQLite、PyMuPDF、arXiv、阿里云 TTS（可选）
- **前端**：Vue 3、Vite、Element Plus

## 快速开始

### 1. 环境（WSL / Linux）

```bash
cd PaperAxon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

若当前镜像无法连接（如报 `Name or service not known`），可改用官方源：  
`pip install -r requirements.txt -i https://pypi.org/simple`  
或阿里云镜像：`pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`

复制 `.env.example` 为 `.env`，填写 `DASHSCOPE_API_KEY`（必填，用于解读与播客稿）。

### 2. 启动后端

```bash
# 需在项目根目录且已激活 venv，并设置 PYTHONPATH
export PYTHONPATH=.   # 或安装为包后省略
uvicorn backend.main:app --reload --port 18527

# 或
python -m backend.main
```

### 3. 启动前端（开发）

```bash
cd frontend
npm install
npm run dev
```

- **可复现安装**（已有 `package-lock.json` 时）：使用 `npm ci` 替代 `npm install`，会严格按 lock 文件安装且更快。
- **镜像不可用时**：可指定源，例如  
  `npm install --registry=https://registry.npmmirror.com`  
  或 `npm install --registry=https://registry.npmjs.org`。
- **EACCES 权限错误**：多为 `node_modules` 曾被 root 或其它用户创建。先改归属再重装：  
  `sudo chown -R $(whoami):$(whoami) .`，然后 `rm -rf node_modules`，再执行 `npm install`。勿使用 `sudo npm install`。

浏览器访问 http://localhost:15173，前端会代理 `/api` 到 18527。

### 4. 生产构建与运行

```bash
cd frontend && npm run build
# 后端托管 frontend/dist
export PYTHONPATH=.
uvicorn backend.main:app --host 0.0.0.0 --port 18527
```

访问 http://localhost:18527（或服务器 IP:18527）。

## Linux 服务器部署建议

- **工作目录**：在服务器上克隆或上传项目后，所有命令在项目根目录执行；数据与 SQLite 默认在项目下 `data/`，可通过环境变量 `DATA_DIR` 改为绝对路径（如 `/var/lib/paperaxon/data`）便于备份与权限管理。
- **端口**：默认 18527（五位数防冲突），可用 `PORT=18527` 覆盖；若使用 Nginx 反向代理，可代理到本机 18527。
- **进程常驻**：使用 systemd 或 supervisor 保持后端常驻；定时采集依赖后端进程内的 APScheduler，需保证单实例运行。
- **时区**：采集时间「HH:mm」按**服务器本地时区**执行，部署时注意服务器 `TZ` 或系统时区设置。
- **无鉴权**：V0.1 不提供登录，建议仅内网或配合 Nginx 做 IP/认证限制。
- **systemd 示例**：见 [docs/deploy-systemd.example](./docs/deploy-systemd.example)，可按需修改后放到 `/etc/systemd/system/` 并 `systemctl enable --now paperaxon`。
- **日志**：应用日志写入 `data/logs/app.log`（与数据目录一致，可通过 `DATA_DIR` 变更），同时输出到控制台；含启动/关闭、定时采集结果、解读与播客任务失败等。

## 功能概览

- **论文来源**：本地上传 PDF、arXiv 链接/ID
- **解读**：异步生成结构化中文解读（背景、方法、结果、创新点等）
- **播客**：将解读转为口语稿并合成语音（需配置阿里云 TTS；未配置时仅生成文稿占位）
- **相关论文**：基于 arXiv API 检索
- **设置**：每日自动采集开关与采集时间（默认 0:00，cat=physics.hist-ph）
- **知识图谱与热度**：轻量展示论文与作者节点、按更新时间热度

## 文档

- [需求说明文档 v0.1](./docs/需求说明文档v0.1.md)
- [详细设计文档 v0.1](./docs/详细设计文档v0.1.md)

## 预留扩展

- **MCP**：`mcp/` 目录预留 MCP 适配
- **Skill**：`skills/` 目录预留可插拔 Skill 模块
