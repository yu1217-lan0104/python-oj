# 新手 Python 算法练习 Coding

面向 Python 算法入门者的轻量本地刷题工具：只支持 Python 3，题目分「入门 / 基础」两级，
每题配循序渐进的思路提示，提交后在本机解释器上自动判题，并把错题、解题笔记、专题进度和刷题报告沉淀下来。

> 按策划书的安全约定，**本系统只在本机 `127.0.0.1` 运行，禁止部署到公网**。

![首页](docs/screenshots/02-home.png)

---

## 一、功能清单

### 一期：核心刷题闭环（已完成）

| 策划书需求 | 实现情况 |
| --- | --- |
| 注册 / 登录 / 个人主页 | ✅ 账号密码注册登录（哈希存储）、个人中心展示进度 |
| 题库分难度、算法标签 | ✅ 16 题：入门 8 + 基础 8，9 个标签可筛选 |
| 题干、样例、思路提示 | ✅ 轻量 Markdown 题干、样例一键复制、提示默认折叠防剧透 |
| 仅支持 Python3、自动判题 | ✅ AC / WA / TLE / RE / CE 五种结果，子进程隔离 + 超时控制 |
| 新手可读的报错 | ✅ 定位行号 + 异常类型 + 修改建议（如「下标越界」） |
| 提交记录 | ✅ 按题目 / 结果筛选、分页、逐测试点对比 |
| 错题一键标记 | ✅ 结果页 / 题目页一键加入，错题本里写复盘 |
| 刷题数据统计 | ✅ 完成量、通过率、难度进度、专题完成度 |

### 二期：学习沉淀（已完成）

| 需求 | 实现情况 |
| --- | --- |
| 自定义解题笔记 | ✅ 任意题目都能写笔记（独立于错题本），`/notes` 汇总管理，题目页就地编辑 |
| 专题训练套题 | ✅ 8 个专题、16 题次，有顺序、有进度、有「继续训练」入口 |
| Python 语法知识点卡片 | ✅ 21 张卡片，5 个分类，支持搜索与折叠展开 |
| 代码草稿自动保存 | ✅ 按题目存在浏览器 localStorage，切页面 / 关浏览器不丢，可一键清空 |

### 三期：可视化与报告（已完成两项，闯关未做）

| 需求 | 实现情况 |
| --- | --- |
| 刷题可视化图表 | ✅ 提交结果环形图、近 14 天提交趋势、各专题完成度条形图（纯服务端 SVG，离线可用） |
| 个人学习报告导出 | ✅ `/report` 一键导出 Markdown、下载自带图表的独立 HTML、浏览器打印成 PDF |
| 专题闯关模式 | ⛔ 暂未实现（专题已有顺序和进度，可在此基础上做关卡化） |

---

## 二、界面预览

| 题库列表 | 做题页（编辑器 / 提示 / 解题笔记） |
| --- | --- |
| ![题库](docs/screenshots/03-problems.png) | ![做题](docs/screenshots/04-problem.png) |

| 专题训练 | 语法卡片 |
| --- | --- |
| ![专题](docs/screenshots/09-topics.png) | ![卡片](docs/screenshots/11-cards.png) |

| 判题结果 | 学习报告 |
| --- | --- |
| ![结果](docs/screenshots/05-submission-ac.png) | ![报告](docs/screenshots/13-report.png) |

导出的独立 HTML 报告（图表内嵌，可直接打印成 PDF）：

![导出的报告](docs/screenshots/14-report-export.png)

其他页面：个人中心 `docs/screenshots/07-profile.png`、错题本 `06-mistakes.png`、
解题笔记 `12-notes.png`、专题详情 `10-topic-detail.png`、注册页 `08-register.png`。
示例导出文件在 `docs/exports/`（`学习报告_示例.md`、`学习报告_示例.html`）。

---

## 三、快速开始（Windows）

环境要求：**Python 3.10 及以上**（开发验证使用 3.11 / 3.13），Windows 10/11。

```bat
:: 1. 进入项目目录并创建虚拟环境
cd python-oj
py -3.13 -m venv .venv

:: 2. 安装依赖（国内网络建议加清华镜像）
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 3. 建表 + 导入题库 / 专题 / 卡片
.venv\Scripts\python.exe manage.py init

:: 4.（可选）创建演示账号并生成演示数据
.venv\Scripts\python.exe manage.py demo
.venv\Scripts\python.exe tools\seed_demo_activity.py

:: 5. 启动
.venv\Scripts\python.exe app.py
```

浏览器打开 <http://127.0.0.1:5000>。演示账号：`demo / demo123456`（也可以自己注册）。
也可以直接双击 `start.bat` 启动（前提是依赖已装好）。

---

## 四、数据库：默认 SQLite，可一键切 MySQL

策划书的技术选型是 MySQL，因此项目**默认支持 MySQL 8**，同时保留 SQLite 作为零配置方案：

- 默认（不配置任何东西）：使用项目目录下的 `pyoj.db`，开箱即用，适合自己刷题、答辩演示；
- 切换 MySQL：复制 `.env.example` 为 `.env`，填写连接串后重新初始化：

```ini
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/pyoj?charset=utf8mb4
```

```bat
:: 方式 A：让程序自动建库建表并导入数据
.venv\Scripts\python.exe manage.py init

:: 方式 B：先手动执行建表脚本（答辩时展示 DDL 用），再导入数据
mysql -u root -p < schema.sql
.venv\Scripts\python.exe manage.py seed
.venv\Scripts\python.exe manage.py topics
.venv\Scripts\python.exe manage.py cards
```

表结构（详见 [`schema.sql`](schema.sql)）：

| 表 | 作用 | 期次 |
| --- | --- | --- |
| `user` | 用户 | 一期 |
| `problem` | 题目，含 `tests_json` 测试点 | 一期 |
| `submit` | 提交记录，含 `detail_json` 逐测试点结果 | 一期 |
| `mistake_note` | 错题本 | 一期 |
| `problem_note` | 解题笔记 | 二期 |
| `topic` / `topic_problem` | 专题套题与题目顺序 | 二期 |
| `card` | Python 语法卡片 | 二期 |

> **本机当前状态**：已按策划书接上本机 MySQL 8.0（`schema.sql` 已实测建出 8 张表，
> 页面页脚显示 `数据库：mysql / pyoj`）。连接串只写在 `.env` 里，该文件已在 `.gitignore` 中，
> 提交代码时不会带出密码。SQLite 的 `pyoj.db` 仍保留，删掉 `.env` 即可零配置回退。

---

## 五、评测模块怎么工作

`judge.py` 是整份工程的核心，流程如下：

1. **编译期检查**：用 `ast.parse` 检查语法错误（CE），并拦截 `os / subprocess / socket` 等敏感模块；
2. **逐测试点运行**：每个测试点单独起一个子进程
   `python -I judge_runner.py <输出上限> main.py`，测试输入从 stdin 喂入；
3. **超时控制**：默认 2000 ms，超时立即结束进程并返回 TLE（提示多半是死循环）；
4. **输出比对**：逐行去掉行尾空白、忽略末尾空行后比较，避免「多一个空格」被判错；
5. **错误翻译**：把 traceback 翻译成「第 N 行 + IndexError：下标越界……」这类新手能看懂的话；
6. **输出限流**：`judge_runner.py` 把 stdout 限制在 256 KB，防止 `while True: print(...)` 把内存吃满。

判题性能参考：16 道题的参考解共 70 个测试点，全部跑完约 4 秒（含解释器启动开销）。

**安全边界**：这是「本地判题器」，不是安全沙箱。子进程会继承当前用户权限，能读写本机文件。
因此系统按策划书要求只监听 `127.0.0.1`，不要部署到公网、不要开放给不信任的人使用。

---

## 六、专题训练 / 语法卡片 / 学习报告

**专题训练**（`/topics`）：`topics_data.py` 里配置 8 个专题（哈希、字符串、数组与模拟、递归、排序与区间、二分、数学、栈），
每个专题有固定顺序和一句话说明。页面按提交记录自动算进度，已完成的专题会给出「回看题目」，
未完成的直接给「继续训练 / 开始训练」，点进去就是下一道没过的题。

**语法卡片**（`/cards`）：`cards_data.py` 维护 21 张卡片，分 5 类（基础语法、容器与字符串、常用技巧、算法套路、易错点），
支持分类筛选和关键词搜索；卡片内容是轻量 Markdown，可以写代码块。

**学习报告**（`/report`）：把提交结果分布、近 14 天趋势、专题完成度画成图（服务端生成的 SVG，不依赖任何 JS/CDN），
同时给出自动生成的学习建议。三种导出方式：

- **导出 Markdown**：拿到 `学习报告_YYYYMMDD.md`，可直接粘进周记或课程报告；
- **下载 HTML 报告**：单个自包含 HTML，图表内嵌，双击即可看，也能用浏览器打印成 PDF；
- **打印 / 另存为 PDF**：直接调浏览器打印，页面已写好打印样式（隐藏导航、避免图表分页）。

**草稿自动保存**：做题页的代码会按题目存进 `localStorage`（键名 `pyoj:draft:<题目 id>`），
刷新或关掉浏览器再回来会自动恢复，编辑器下方会显示「草稿已保存 时间」，也能一键清空。

---

## 七、题库与演示数据维护

- 题库正文在 [`seed_data.py`](seed_data.py)：题干、提示、样例、测试点，以及仅供开发期校验的参考解；
- 专题在 [`topics_data.py`](topics_data.py)，按**题目标题**关联，改题名时要同步；
- 卡片在 [`cards_data.py`](cards_data.py)；
- 导入 / 更新命令：

```bat
.venv\Scripts\python.exe manage.py seed      :: 题库
.venv\Scripts\python.exe manage.py topics    :: 专题
.venv\Scripts\python.exe manage.py cards     :: 卡片
```

校验数据是否正确：

```bat
.venv\Scripts\python.exe tools\verify_seed.py
```

它会把 16 道题的参考解逐个跑过全部测试点，并检查专题引用的题目是否存在、卡片标题是否重复。

---

## 八、自测与截图

```bat
:: 端到端冒烟测试：注册登录 → 浏览 → 五种判题 → 错题本 → 统计 → 专题 → 卡片 → 笔记 → 报告导出
.venv\Scripts\python.exe tools\smoke_test.py

:: 浏览器端自检：用无头 Chrome 验证「草稿自动保存 / 刷新恢复 / 清空草稿」
.venv\Scripts\python.exe tools\browser_check.py

:: 生成一份示例学习报告到 docs/exports/
.venv\Scripts\python.exe tools\export_report.py

:: 重新生成 docs/screenshots 下的演示截图（需要先启动站点）
.venv\Scripts\python.exe tools\make_screenshots.py
```

`tools/browser_check.py` 通过 Chrome DevTools Protocol 驱动无头 Chrome（依赖 `websocket-client`，
仅开发期使用，不在 `requirements.txt` 里）：注入登录 cookie → 在编辑器输入代码 → 检查 localStorage →
刷新页面确认草稿被恢复 → 点击清空。这样浏览器端的交互也有自动化验证。

`make_screenshots.py` 用 Flask 的会话签名器构造 demo 账号 cookie，再通过本机代理注入到无头 Chrome 的请求里，
因此不需要人工登录就能截到登录后的页面。

---

## 九、目录结构

```text
python-oj/
├─ app.py                  # 应用工厂：蓝图注册、CSRF、错误页、模板过滤器
├─ config.py               # 配置（.env / 环境变量 / 默认 SQLite）
├─ extensions.py           # db、login_manager
├─ models.py               # user / problem / submit / mistake_note / problem_note / topic / card
├─ stats.py                # 刷题统计（完成量、难度进度、专题进度、通过率）
├─ charts.py               # 服务端 SVG 图表：环形图、折线图、条形图
├─ judge.py                # 本地评测：语法检查、子进程运行、输出比对、错误翻译
├─ judge_runner.py         # 评测子进程入口：限制用户程序输出体积
├─ seed_data.py            # 16 道题的题干、提示、样例、测试点、参考解
├─ topics_data.py          # 8 个专题套题配置
├─ cards_data.py           # 21 张语法卡片
├─ manage.py               # 命令行：init / seed / topics / cards / demo / reset-user / db-check
├─ schema.sql              # MySQL 8 建表脚本（与 models 保持一致）
├─ views/
│  ├─ auth.py              # 注册、登录、退出
│  ├─ main.py              # 首页
│  ├─ problems.py          # 题库列表、题目详情、提交判题
│  ├─ topics.py            # 专题训练
│  ├─ cards.py             # 语法卡片
│  ├─ records.py           # 提交记录、结果详情、错题本、解题笔记
│  ├─ report.py            # 学习报告与导出
│  └─ profile.py           # 个人中心
├─ templates/              # Jinja2 模板（Bootstrap 5，本地静态资源）
├─ static/
│  ├─ css/app.css          # 自定义视觉样式（含打印样式）
│  ├─ js/app.js            # 复制样例、Tab 缩进、Ctrl+Enter 提交、草稿自动保存
│  └─ vendor/              # 本地 Bootstrap，无外网也能正常显示
├─ tools/
│  ├─ verify_seed.py       # 参考解 + 专题 + 卡片数据自检
│  ├─ smoke_test.py        # 端到端冒烟测试
│  ├─ browser_check.py     # 无头 Chrome 验证草稿自动保存（CDP）
│  ├─ export_report.py     # 生成示例学习报告
│  ├─ seed_demo_activity.py# 给 demo 账号造演示数据（提交、错题、笔记）
│  ├─ build_manual.js      # 生成《使用说明书》Word 文档
│  └─ make_screenshots.py  # 生成演示截图
└─ docs/
   ├─ 使用说明书.docx / .pdf  # 用户手册（24 页，含 13 张截图）
   ├─ screenshots/         # 演示截图
   └─ exports/             # 示例学习报告（md + html）
```

---

## 十、后续计划

- 三期剩余：专题闯关模式（在现有专题顺序上加关卡、徽章、通关动画）；
- 学习报告：支持按周 / 按月区间导出，增加与上一周期的对比；
- 工程向：评测放进独立进程池、接入 `resource` 限制内存（Linux）、支持多测试点并行。

---

## 十一、版本管理

项目已用 Git 管理，`main` 分支当前对应交付版本 `v1.0.0`（一期 + 二期 + 三期图表/报告）。

```bat
git log --oneline      :: 提交历史
git tag -n             :: 版本标签
git status             :: 工作区状态
```

`.gitignore` 已排除 `.venv/`、`pyoj.db`、`.env`、`.shotcache/`：虚拟环境、数据库文件、数据库密码都不会进仓库，
换一台机器按「数据库」一节重新配置即可跑起来。

配套文档：[使用说明书（Word）](docs/使用说明书.docx) / [PDF 版](docs/使用说明书.pdf)，
共 24 页，包含环境安装、功能操作、学习建议、FAQ 与题库清单，可直接打印或随课程设计提交。

---

## 十二、常见问题

**1. 端口 5000 被占用？**
修改 `.env` 里的 `PORT=5001`，或结束占用进程后重启。

**2. MySQL 报 `Access denied for user 'root'@'localhost'`？**
密码不对。先确认能用 `mysql -u root -p` 登录，再把正确密码写进 `.env` 的 `DATABASE_URL`。

**3. 判题一直是 TLE？**
先用样例在本地跑一遍；检查 `while` 条件、`input()` 是否读完导致死循环，或算法复杂度过高。

**4. 代码草稿存在哪里？会同步吗？**
存在浏览器 `localStorage`，只在本机当前浏览器有效，清空浏览器数据后草稿会丢。

**5. 导出的 Markdown / HTML 打开乱码？**
两个文件都是 UTF-8 编码；用 VS Code、Typora、Edge/Chrome 打开即可，记事本请选 UTF-8。

**6. 打印成 PDF 时图表被截断？**
打印对话框里把「边距」设为「默认」、勾选「背景图形」，页面已按 A4 做了防分页处理。
