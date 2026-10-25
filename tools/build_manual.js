/**
 * 生成《新手 Python 算法练习场 使用说明书》.docx
 *
 * 用法（在项目根目录）：
 *   $env:NODE_PATH="C:\Users\36187\AppData\Roaming\npm\node_modules"
 *   node tools/build_manual.js
 *
 * 依赖：npm 全局包 docx（v9）。产物：docs/使用说明书.docx
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
  TableOfContents, LevelFormat, NumberFormat, TabStopType, TabStopPosition,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const SHOTS = path.join(ROOT, "docs", "screenshots");
const OUT = path.join(ROOT, "docs", "使用说明书.docx");

const CONTENT_W = 9638; // A4 - 2 × 2cm 页边距（DXA）
const FONT_BODY = { ascii: "Times New Roman", eastAsia: "宋体", hAnsi: "Times New Roman", cs: "Times New Roman" };
const FONT_HEAD = { ascii: "Arial", eastAsia: "微软雅黑", hAnsi: "Arial", cs: "Arial" };

/* ------------------------------------------------------------------ */
/* 基础排版工具                                                        */
/* ------------------------------------------------------------------ */

function pngSize(file) {
  const buf = fs.readFileSync(file);
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

const px = (cm) => Math.round((cm / 2.54) * 96);

function rich(text, opts = {}) {
  const runs = [];
  const parts = String(text).split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  for (const part of parts) {
    if (!part) continue;
    if (part.startsWith("**") && part.endsWith("**")) {
      runs.push(new TextRun({ text: part.slice(2, -2), bold: true, ...opts }));
    } else if (part.startsWith("`") && part.endsWith("`")) {
      runs.push(new TextRun({ text: part.slice(1, -1), font: "Consolas", size: (opts.size || 21) - 1, color: "1F4E79", ...opts }));
    } else {
      runs.push(new TextRun({ text: part, ...opts }));
    }
  }
  return runs;
}

const body = (text, opts = {}) =>
  new Paragraph({ spacing: { after: 120, line: 330 }, children: rich(text, opts) });

const lead = (text) =>
  new Paragraph({ spacing: { after: 120, line: 330 }, keepNext: true, children: rich(text) });

const bullet = (text) =>
  new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 70 }, children: rich(text) });

let numSeq = 0;
const numList = (items) => {
  numSeq += 1;
  const ref = "n" + numSeq;
  return items.map(
    (text) => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 90 }, children: rich(text) })
  );
};

const h1 = (text, opts = {}) =>
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: opts.newPage !== false, keepNext: true, children: [new TextRun(text)] });

const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun(text)] });

const spacer = (h = 12) => new Paragraph({ spacing: { after: h * 20 }, children: [] });

function code(lines) {
  const out = [];
  lines.forEach((line, index) => {
    out.push(
      new Paragraph({
        shading: { type: ShadingType.CLEAR, fill: "F4F6FA" },
        spacing: { before: index === 0 ? 100 : 0, after: 0, line: 250 },
        indent: { left: 220, right: 160 },
        alignment: AlignmentType.LEFT,
        children: [new TextRun({ text: line || " ", font: "Consolas", size: 18, color: "1F2937" })],
      })
    );
  });
  out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return out;
}

function callout(text) {
  return new Paragraph({
    shading: { type: ShadingType.CLEAR, fill: "FFF8E6" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: "F0A020", space: 8 } },
    spacing: { before: 120, after: 160 },
    indent: { left: 180, right: 120 },
    children: rich(text, { size: 20 }),
  });
}

function figure(file, cmWide, maxCmHigh, caption) {
  const full = path.join(SHOTS, file);
  const { width, height } = pngSize(full);
  let w = cmWide;
  let h = (cmWide * height) / width;
  if (h > maxCmHigh) {
    h = maxCmHigh;
    w = (maxCmHigh * width) / height;
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 60 },
      keepNext: true,
      children: [
        new ImageRun({
          type: "png",
          data: fs.readFileSync(full),
          transformation: { width: px(w), height: px(h) },
          altText: { title: caption, description: caption, name: file },
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 180 },
      children: [new TextRun({ text: caption, size: 18, color: "6B7A90", font: FONT_BODY })],
    }),
  ];
}

function table(headers, rows, widths) {
  const edge = { style: BorderStyle.SINGLE, size: 4, color: "D0D8E4" };
  const borders = { top: edge, bottom: edge, left: edge, right: edge };
  const margins = { top: 70, bottom: 70, left: 110, right: 110 };
  const head = new TableRow({
    tableHeader: true,
    children: headers.map((text, index) =>
      new TableCell({
        width: { size: widths[index], type: WidthType.DXA },
        borders,
        margins,
        verticalAlign: VerticalAlign.CENTER,
        shading: { type: ShadingType.CLEAR, fill: "E6EEFB" },
        children: [
          new Paragraph({ keepNext: true, children: [new TextRun({ text, bold: true, size: 19, font: FONT_HEAD })] }),
        ],
      })
    ),
  });
  const bodyRows = rows.map((cells, rowIndex) =>
    new TableRow({
      cantSplit: true,
      children: cells.map((text, index) =>
        new TableCell({
          width: { size: widths[index], type: WidthType.DXA },
          borders,
          margins,
          children: [
            new Paragraph({
              spacing: { line: 260 },
              keepNext: rowIndex < rows.length - 1,
              children: rich(text, { size: 19 }),
            }),
          ],
        })
      ),
    })
  );
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    rows: [head, ...bodyRows],
  });
}

const gap = () => new Paragraph({ spacing: { after: 160 }, children: [] });

/* ------------------------------------------------------------------ */
/* 封面                                                                */
/* ------------------------------------------------------------------ */

const cover = [
  spacer(18),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 700, after: 200 },
    children: [new TextRun({ text: "新手 Python 算法练习场", size: 40, bold: true, color: "1E3A8A", font: FONT_HEAD })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text: "使 用 说 明 书", size: 64, bold: true, color: "101828", font: FONT_HEAD })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: "2F6BFF", space: 10 } },
    children: [new TextRun({ text: "面向算法入门的本地刷题系统", size: 24, color: "475467", font: FONT_HEAD })],
  }),
  spacer(6),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 900 },
    children: [new TextRun({ text: "一期（刷题闭环）· 二期（笔记 / 专题 / 卡片 / 草稿）· 三期（图表 / 报告导出）", size: 18, color: "6B7A90" })],
  }),
  table(
    ["文档版本", "适用程序", "编写", "日期"],
    [["v1.0.0", "python-oj 1.0.0", "胡宇", "2026 年 10 月"]],
    [2200, 2800, 2000, 2638]
  ),
  spacer(10),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 300 },
    children: [new TextRun({ text: "项目地址：github.com/yu1217-lan0104/python-oj", size: 17, color: "6B7A90", font: "Consolas" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "本系统仅限本机使用，请勿部署到公网", size: 17, color: "B42318" })],
  }),
];

/* ------------------------------------------------------------------ */
/* 目录                                                                */
/* ------------------------------------------------------------------ */

const toc = [
  new TableOfContents("目　录", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
];

/* ------------------------------------------------------------------ */
/* 第 1 章                                                             */
/* ------------------------------------------------------------------ */

const ch1 = [
  h1("第 1 章　系统概述", { newPage: false }),
  h2("1.1　这是什么"),
  body(
    "新手 Python 算法练习场是一个**只在本机运行的轻量刷题工具**，专门给刚学完 Python 基础语法、准备接触算法的同学使用。" +
      "它只支持 Python 3，题库按「入门 / 基础」两级编排，每道题都配了循序渐进的思路提示，提交代码后由本机的 Python 解释器自动判题。"
  ),
  body(
    "与主流在线判题平台不同，它不追求 C++ 竞赛场景，也不做社区和排行榜；重点放在**看得懂、做得下去、能复盘**三件事上：" +
      "提示只给方向不给代码，判题报错会翻译成中文，做错的题可以一键进错题本，再配合解题笔记、专题训练和学习报告形成闭环。"
  ),
  h2("1.2　适合谁用"),
  bullet("掌握 Python 基础语法（变量、循环、函数、列表、字典），第一次系统练算法的新手。"),
  bullet("准备蓝桥杯 Python 组入门、或需要做课程设计 / 科创项目演示的同学。"),
  bullet("想给自己留一份可回看的刷题记录：做过哪些题、卡在哪里、后来怎么想通的。"),
  callout(
    "**注意**：本系统没有做安全沙箱，判题会以当前用户身份运行你提交的代码。因此只在自己电脑上使用，" +
      "默认只监听 127.0.0.1，**不要部署到公网**、也不要开放给不信任的人。"
  ),
  h2("1.3　功能一览"),
  table(
    ["模块", "主要能力", "期次"],
    [
      ["用户", "注册、登录、记住我、个人中心", "一期"],
      ["题库", "16 道题，入门 8 + 基础 8，按难度 / 专题 / 进度筛选、关键词搜索", "一期"],
      ["做题与判题", "Python3 在线编辑、样例复制、思路提示折叠、AC/WA/TLE/RE/CE 五态判题", "一期"],
      ["复盘", "提交记录、逐测试点对比、错题本、解题笔记", "一期 / 二期"],
      ["训练", "8 个专题套题、21 张语法卡片、代码草稿自动保存", "二期"],
      ["统计与导出", "提交分布、14 天趋势、专题完成度、学习报告（Markdown / HTML / PDF）", "三期"],
    ],
    [1500, 6600, 1538]
  ),
  gap(),
  h2("1.4　界面总览"),
  body("登录后首页如下图所示，顶部是全局导航，中间是学习路线与进度，右侧是最近提交。"),
  ...figure("02-home.png", 14.4, 18.2, "图 1-1　登录后的首页"),
  body("顶部导航共有 7 个入口，作用如下："),
  table(
    ["导航项", "说明"],
    [
      ["题库", "全部题目，可按难度、进度、专题筛选"],
      ["专题训练", "8 组套题，按顺序练习并自动记录进度"],
      ["语法卡片", "21 张 Python 语法 / 算法套路卡片，可搜索"],
      ["提交记录", "历次提交与判题详情，支持按结果筛选"],
      ["错题本", "手动标记的题目与复盘笔记"],
      ["学习报告", "图表统计、学习建议与报告导出"],
      ["右上角头像", "个人中心：完成量、通过率、专题进度"],
    ],
    [1800, 7838]
  ),
  gap(),
  h2("1.5　一次完整的刷题流程"),
  ...numList([
    "在**题库**里挑一道题，或从**专题训练**进入指定套题。",
    "读题干和样例，自己先想 5–10 分钟，再看**思路提示**。",
    "在右侧编辑器里写代码，按 `Ctrl + Enter` 或点「提交判题」。",
    "看判题结果：AC 通过；WA/TLE/RE/CE 会给出中文原因和改进建议。",
    "没过的题点「加入错题本」，写下错在哪、正确思路是什么。",
    "周末打开**学习报告**，看专题完成度和 14 天趋势，决定下周练什么。",
  ]),
];

/* ------------------------------------------------------------------ */
/* 第 2 章                                                             */
/* ------------------------------------------------------------------ */

const ch2 = [
  h1("第 2 章　安装与启动"),
  h2("2.1　运行环境"),
  table(
    ["项目", "要求"],
    [
      ["操作系统", "Windows 10 / 11（开发与验证环境为 Windows 11）"],
      ["Python", "3.10 及以上，开发使用 3.11 与 3.13"],
      ["数据库", "MySQL 8.0（可选）；不配置时自动使用 SQLite，开箱即用"],
      ["浏览器", "Chrome / Edge 等现代浏览器"],
      ["网络", "不需要联网：Bootstrap 等静态资源已放在 static/vendor 下"],
    ],
    [2200, 7438]
  ),
  gap(),
  h2("2.2　安装（五步）"),
  body("打开 PowerShell，进入项目目录后依次执行："),
  ...code([
    "cd \"D:\\deep seek工作流\\python-oj\"",
    "py -3.13 -m venv .venv",
  ]),
  body("第二步安装依赖。国内网络建议加清华镜像，能快很多："),
  ...code([
    ".venv\\Scripts\\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple",
  ]),
  body("第三步初始化数据库。这条命令会自动建库建表，并导入 16 道题、8 个专题和 21 张语法卡片："),
  ...code([".venv\\Scripts\\python.exe manage.py init"]),
  body("第四步（可选）创建演示账号并生成演示数据，方便直接看效果："),
  ...code([
    ".venv\\Scripts\\python.exe manage.py demo",
    ".venv\\Scripts\\python.exe tools\\seed_demo_activity.py",
  ]),
  body("第五步启动服务："),
  ...code([".venv\\Scripts\\python.exe app.py"]),
  body("看到 `Running on http://127.0.0.1:5000` 就说明启动成功，浏览器打开该地址即可。"),
  callout("已经装过一次依赖的话，以后只要双击项目根目录的 **start.bat** 就能启动，不必再敲命令。"),
  h2("2.3　演示账号"),
  table(
    ["账号", "密码", "说明"],
    [["demo", "demo123456", "自带 8 条提交、2 条错题笔记、3 篇解题笔记，适合直接演示"]],
    [2200, 2600, 4838]
  ),
  gap(),
  h2("2.4　停止与再次启动"),
  bullet("在运行窗口按 `Ctrl + C` 停止服务；直接关闭窗口也可以。"),
  bullet("下次启动：双击 `start.bat`，或再次执行 `.venv\\Scripts\\python.exe app.py`。"),
  bullet("数据保存在数据库里，重启不会丢失。"),
  h2("2.5　使用 MySQL（可选）"),
  body("默认使用 SQLite，零配置即可运行；如果想要和课程设计的技术选型保持一致，切换到 MySQL 8 只需要两步："),
  body("1）复制 `.env.example` 为 `.env`，填入连接串（密码请填自己的）："),
  ...code(["DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/pyoj?charset=utf8mb4"]),
  body("2）重新初始化（会自动建库建表并导入数据）："),
  ...code([".venv\\Scripts\\python.exe manage.py init"]),
  body("也可以先执行建表脚本 `schema.sql`（方便演示 DDL），再导入数据："),
  ...code([
    "mysql -u root -p < schema.sql",
    ".venv\\Scripts\\python.exe manage.py seed",
    ".venv\\Scripts\\python.exe manage.py topics",
    ".venv\\Scripts\\python.exe manage.py cards",
  ]),
  callout("`.env` 已在 `.gitignore` 中，不会把数据库密码提交到仓库；页面页脚会显示当前实际使用的数据库。"),
  h2("2.6　数据与备份"),
  bullet("SQLite：整个库就是项目根目录下的 `pyoj.db` 文件，复制这个文件即可备份。"),
  bullet("MySQL：用 `mysqldump -u root -p pyoj > backup.sql` 导出，恢复时 `mysql -u root -p pyoj < backup.sql`。"),
  bullet("题库、专题、卡片都是代码里的数据（`seed_data.py` / `topics_data.py` / `cards_data.py`），重新 `init` 即可恢复。"),
];

/* ------------------------------------------------------------------ */
/* 第 3 章                                                             */
/* ------------------------------------------------------------------ */

const ch3 = [
  h1("第 3 章　快速上手：10 分钟做完第一题"),
  h2("3.1　注册与登录"),
  body("打开首页后点右上角「免费注册」，账号要求 3–20 位字母、数字或下划线，密码至少 6 位；昵称可以留空，默认显示账号名。"),
  ...figure("08-register-crop.png", 8.8, 13.5, "图 3-1　注册页面"),
  body("已经有账号就点「登录」，勾选「记住我」后下次打开无需重新登录。"),
  h2("3.2　挑选题目"),
  body("进入「题库」可以看到全部 16 道题。每行显示题号、标题、标签、测试点数量、难度和当前进度；右侧「做题」按钮直接进入答题页。"),
  ...figure("03-problems.png", 14.4, 18.2, "图 3-2　题库列表与筛选"),
  body("顶部筛选条有三个维度，可以组合使用："),
  bullet("**难度**：全部 / 入门 / 基础。"),
  bullet("**进度**：已通过 / 尝试中 / 未开始，用来快速找到没做完的题。"),
  bullet("**专题**：哈希、枚举、二分、排序等标签；右上角搜索框支持按关键词搜题。"),
  h2("3.3　读题与思路提示"),
  body("题目页左侧是题干、样例和提示。样例框右上角的「复制」会把输入直接放进剪贴板，方便本地调试。"),
  ...figure("04-problem.png", 14.4, 18.2, "图 3-3　题目页：左边读题，右边写代码"),
  body("「思路提示」默认折叠，展开前可以先自己想。提示按「先给方向、再给方法、最后暗示数据结构」三步写，不会直接给代码。"),
  h2("3.4　编写并提交代码"),
  body("右侧编辑器支持以下操作："),
  table(
    ["操作", "效果"],
    [
      ["`Tab` / `Shift + Tab`", "缩进 / 回退缩进 4 个空格"],
      ["`Ctrl + Enter`", "直接提交，无需点按钮"],
      ["停止输入约 0.6 秒", "草稿自动保存到浏览器，刷新或关掉再回来会自动恢复"],
      ["编辑器下方「清空草稿」", "丢弃当前草稿，恢复默认模板"],
    ],
    [2600, 7038]
  ),
  gap(),
  h2("3.5　看懂判题结果"),
  body("提交后会跳到判题详情页，顶部是用颜色区分的结果横幅，下面是逐测试点的情况和你的代码。"),
  ...figure("05-submission-ac.png", 14.4, 18.2, "图 3-4　AC（通过）的判题详情"),
  body("五种判题结果的含义和处理方式："),
  table(
    ["结果", "含义", "常见原因", "建议"],
    [
      ["AC", "全部测试点通过", "—", "可以去看下一题，或把思路写进解题笔记"],
      ["WA", "输出与标准答案不一致", "格式不对、边界没考虑、逻辑漏洞", "拿样例先自测，注意空格、换行、大小写"],
      ["TLE", "运行超过时间限制", "死循环、算法复杂度过高", "看数据范围，想想能不能降到 O(n log n)"],
      ["RE", "运行出错", "下标越界、除零、读输入越界", "看报错行号和中文提示，先修异常"],
      ["CE", "代码无法运行", "语法错误、用了禁止的模块", "按提示改语法；判题只允许标准库"],
    ],
    [900, 2700, 3200, 2838]
  ),
  gap(),
  body("RE 的提示会被翻译成新手能看懂的话，例如下标越界会显示："),
  ...code([
    "第 5 行，IndexError：list index out of range",
    "提示：下标越界：访问了列表中不存在的位置。索引从 0 开始，长度为 n 的列表最大下标是 n-1。",
  ]),
  h2("3.6　把题加入错题本"),
  body("没做出来的题，在题目页或判题详情页点「加入错题本」，之后到「错题本」里补一句复盘：卡在哪、正确思路是什么。写下来比再做十道新题有用。"),
];

/* ------------------------------------------------------------------ */
/* 第 4 章                                                             */
/* ------------------------------------------------------------------ */

const ch4 = [
  h1("第 4 章　功能详解"),
  h2("4.1　题库与筛选"),
  body("题库支持难度、进度、专题三个维度的组合筛选，右上角还有关键词搜索。"),
  bullet("题号前面的数字在通过后会变成绿色，一眼能看出做了多少。"),
  bullet("列表显示每道题的测试点数量，方便预估判题时间。"),
  bullet("未登录也能浏览题目，但提交代码需要先登录。"),
  h2("4.2　做题页与草稿"),
  body("做题页由左右两栏组成：左栏固定为题面，右栏是提交面板（编辑器、判题按钮、错题本、解题笔记、最近提交）。"),
  body("**草稿自动保存**：编辑器内容会按题目存进浏览器本地存储，键名为 `pyoj:draft:<题目 id>`。刷新页面、切到别的题再回来，内容都会自动恢复；" +
    "编辑器下方会显示「草稿已保存 时间」或「已恢复上次草稿」。换浏览器或清除浏览器数据后草稿会丢。"),
  body("**解题笔记**：右栏底部的「解题笔记」可以随时展开写思路，保存后可在「个人中心 → 解题笔记」里统一查看。"),
  h2("4.3　判题详情"),
  body("判题详情页包含四部分：结果横幅（题目、测试点通过数、最大用时、提交时间）、判题信息（逐测试点结果）、提交的代码（带行号、可复制）、以及同题的历史提交。"),
  bullet("测试点表格里点「查看对比」，可以看到该测试点的输入、期望输出和实际输出。"),
  bullet("WA 通常只跑到第一个失败测试点就停下，先把这一处改对再提交，比反复猜更高效。"),
  bullet("CE / RE 的提示框会给出问题行号和修改建议。"),
  h2("4.4　提交记录"),
  body("「提交记录」按时间倒序列出你的全部提交，可按 AC / WA / TLE / RE / CE 筛选，也可以从题目页点「我的提交」只看某道题。每页 12 条，支持翻页。"),
  h2("4.5　错题本"),
  ...figure("06-mistakes.png", 13.6, 14.5, "图 4-1　错题本与复盘笔记"),
  body("错题本记录你主动标记的题目，每题可以写一段复盘笔记，并显示这道题最近一次的判题结果。做完题后如果通过了，可以让它留在错题本里当复习清单，也可以一键移除。"),
  h2("4.6　解题笔记"),
  ...figure("12-notes.png", 13.6, 14.5, "图 4-2　解题笔记列表"),
  body("解题笔记和错题本的区别：错题本针对「做错过的题」，解题笔记针对「任何想记录的题」——包括一次做对但思路巧妙的题。两处内容独立保存，互不覆盖。"),
  h2("4.7　专题训练"),
  body("「专题训练」把 16 道题编成 8 个有顺序的套题，每个专题有固定主题和一句话说明。页面会按提交记录自动算进度，并给出「开始训练 / 继续训练」入口，点进去就是下一道还没通过的题。"),
  ...figure("09-topics.png", 14.4, 18.2, "图 4-3　专题训练总览"),
  ...figure("10-topic-detail.png", 13.6, 14, "图 4-4　专题详情：按顺序做题、进度自动更新"),
  body("建议按专题顺序推进：同一组题会把同一个套路反复练，比东做一题西做一题更容易形成手感。"),
  h2("4.8　语法卡片"),
  body("「语法卡片」共 21 张，分 5 类：基础语法、容器与字符串、常用技巧、算法套路、易错点。支持分类筛选和关键词搜索，卡片默认折叠，点开才显示代码示例。"),
  ...figure("11-cards.png", 14.4, 18.2, "图 4-5　语法卡片（折叠状态）"),
  h2("4.9　个人中心"),
  ...figure("07-profile.png", 13.8, 18.2, "图 4-6　个人中心"),
  body("个人中心汇总四类数据：已完成题量与完成度、提交次数、通过率、错题本数量；下面还有难度进度、各专题完成情况、最近提交和「接下来练这些」推荐。"),
  h2("4.10　学习报告与导出"),
  body("「学习报告」把刷题数据画成三张图，并自动生成学习建议："),
  bullet("**提交结果分布**（环形图）：看清 AC / WA / TLE / RE / CE 各占多少。"),
  bullet("**最近 14 天提交趋势**（折线图）：直观看出练习节奏有没有断。"),
  bullet("**各专题完成度**（条形图 + 明细表）：找出还没开始的专题。"),
  ...figure("13-report.png", 11.8, 21, "图 4-7　学习报告"),
  lead("右上角提供三种导出方式："),
  table(
    ["方式", "产物", "适用场景"],
    [
      ["导出 Markdown", "学习报告_YYYYMMDD.md", "粘进课程报告、周记或 GitHub Issue"],
      ["下载 HTML 报告", "学习报告_YYYYMMDD.html", "单个文件自带图表，双击即可看，也能打印成 PDF"],
      ["打印 / 另存为 PDF", "浏览器打印对话框", "交作业、贴进答辩材料"],
    ],
    [2200, 3200, 4238]
  ),
  gap(),
  ...figure("14-report-export.png", 10.8, 16, "图 4-8　导出的独立 HTML 报告（图表已内嵌）"),
];

/* ------------------------------------------------------------------ */
/* 第 5 章                                                             */
/* ------------------------------------------------------------------ */

const ch5 = [
  h1("第 5 章　学习建议"),
  h2("5.1　推荐顺序"),
  body("整个题库的难度是递增的，建议按「入门 → 基础」的顺序推进，同时用专题把同类题串起来："),
  ...numList([
    "**入门 1–5 题**：两数之和、判断素数、回文字符串、斐波那契数列、字符统计，先把判题流程和基本套路跑顺。",
    "**入门 6–8 题**：最大值与下标、凯撒密码、求阶乘，练习边界处理和字符串遍历。",
    "**基础 9–12 题**：二分查找、第 k 小的数、括号匹配、区间合并，开始接触经典算法结构。",
    "**基础 13–16 题**：阶乘末尾零、爬楼梯、日期差、砍树（二分答案），补数学与二分答案。",
  ]),
  callout("如果某道题 30 分钟仍没有思路，先看提示的第一条；照着第一条能推进就继续，推不动再点「加入错题本」，第二天再看。"),
  h2("5.2　七周节奏参考"),
  table(
    ["周次", "目标", "用到的功能"],
    [
      ["第 1 周", "装好环境，做完入门前 3 题", "题库筛选、判题详情"],
      ["第 2 周", "完成全部入门题，建立错题本习惯", "错题本、解题笔记"],
      ["第 3 周", "专攻二分与排序两个专题", "专题训练、语法卡片"],
      ["第 4 周", "完成基础题中的字符串 / 模拟类", "题库、提交记录"],
      ["第 5 周", "补递归、数学专题，整理笔记", "解题笔记、卡片"],
      ["第 6 周", "重做错题，写复盘", "错题本、学习报告"],
      ["第 7 周", "导出报告，准备答辩材料", "学习报告导出、截图"],
    ],
    [1100, 4800, 3738]
  ),
  gap(),
  h2("5.3　复盘三步法"),
  ...numList([
    "**当天**：没过的题写一句「错在哪」，例如「忘了题目要求下标从 1 开始」。",
    "**第二天**：只做错题本里的题，不看旧代码，重新写一遍。",
    "**周末**：看学习报告里的专题完成度和 14 天趋势，决定下周先补哪个专题。",
  ]),
  body("判题结果的具体处理方式见 3.5 节的表格；核心原则只有一条：**先定位问题，再改代码**，不要靠反复提交碰运气。"),
];

/* ------------------------------------------------------------------ */
/* 第 6 章                                                             */
/* ------------------------------------------------------------------ */

const qa = (q, a) => [new Paragraph({ spacing: { before: 140, after: 40 }, children: [new TextRun({ text: q, bold: true, size: 21, font: FONT_HEAD })] }), body(a)];

const ch6 = [
  h1("第 6 章　常见问题"),
  ...qa("Q1　启动时提示端口 5000 被占用怎么办？", "改 `.env` 里的 `PORT=5001` 后重启；或者用 `netstat -ano | findstr :5000` 找到占用进程并结束它。"),
  ...qa("Q2　依赖装不上 / 一直卡在下载？", "加国内镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`。如果之前失败过，删掉 `.venv` 重新创建再装。"),
  ...qa("Q3　MySQL 报 `Access denied for user 'root'@'localhost'`？", "密码不对。先用 `mysql -u root -p` 确认能登录，再把正确密码填进 `.env` 的 `DATABASE_URL`，然后重新 `manage.py init`。"),
  ...qa("Q4　判题一直是 TLE？", "先用样例在本地跑一遍；检查 `while` 条件、输入是否读完，或算法复杂度过高。题目里的「数据范围」就是判断复杂度的依据。"),
  ...qa("Q5　提示「代码使用了禁止的模块」？", "判题环境只允许 Python 标准库中的算法相关模块，`os / subprocess / socket / urllib` 等会被拦截，正常解题用不到。"),
  ...qa("Q6　草稿存在哪里？换电脑能看到吗？", "存在浏览器的 localStorage，按题目 ID 保存，只在本机当前浏览器有效；清除浏览器数据或换浏览器后草稿会丢。"),
  ...qa("Q7　导出的报告打开是乱码？", "文件是 UTF-8 编码，用 VS Code、Typora 或 Edge / Chrome 打开即可；Windows 记事本请选择 UTF-8 编码。"),
  ...qa("Q8　打印成 PDF 时图表被截断？", "打印对话框里把边距设为「默认」、勾选「背景图形」；页面已按 A4 做了防分页处理。"),
];

/* ------------------------------------------------------------------ */
/* 第 7 章                                                             */
/* ------------------------------------------------------------------ */

const ch7 = [
  h1("第 7 章　附录"),
  h2("附录 A　目录结构"),
  ...code([
    "python-oj/",
    "├─ app.py              # 应用工厂：蓝图、CSRF、错误页",
    "├─ judge.py            # 本地判题：语法检查、子进程、输出比对、报错翻译",
    "├─ judge_runner.py     # 判题子进程入口：限制用户程序输出体积",
    "├─ models.py           # 8 张表的数据模型",
    "├─ stats.py            # 刷题统计",
    "├─ charts.py           # 服务端 SVG 图表（环形 / 折线 / 条形）",
    "├─ seed_data.py        # 16 道题的题干、提示、测试点、参考解",
    "├─ topics_data.py      # 8 个专题配置",
    "├─ cards_data.py       # 21 张语法卡片",
    "├─ manage.py           # init / seed / topics / cards / demo / db-check",
    "├─ schema.sql          # MySQL 8 建表脚本",
    "├─ views/              # 路由：auth / problems / topics / cards / records / report",
    "├─ templates/          # Jinja2 模板",
    "├─ static/             # 自定义样式、脚本、本地 Bootstrap",
    "├─ tools/              # 自检、演示数据、截图、报告导出脚本",
    "└─ docs/               # 截图、示例报告、本说明书",
  ]),
  h2("附录 B　常用命令速查"),
  table(
    ["命令", "作用"],
    [
      ["`.venv\\Scripts\\python.exe app.py`", "启动站点（默认 http://127.0.0.1:5000）"],
      ["`manage.py init`", "建库建表 + 导入题库 / 专题 / 卡片"],
      ["`manage.py seed` / `topics` / `cards`", "只重新导入对应数据"],
      ["`manage.py demo`", "创建演示账号 demo / demo123456"],
      ["`manage.py db-check`", "查看当前数据库与数据量"],
      ["`tools\\verify_seed.py`", "用参考解校验全部测试点，并检查专题 / 卡片数据"],
      ["`tools\\smoke_test.py`", "端到端冒烟测试（注册、判题、笔记、报告导出等）"],
      ["`tools\\seed_demo_activity.py`", "给 demo 账号生成提交、错题与笔记"],
    ],
    [3600, 6038]
  ),
  gap(),
  h2("附录 C　题库清单"),
  table(
    ["#", "题目", "难度", "标签", "所属专题"],
    [
      ["1", "两数之和", "入门", "哈希、枚举", "哈希表入门"],
      ["2", "判断素数", "入门", "枚举、数学", "数学与枚举"],
      ["3", "回文字符串", "入门", "字符串、模拟", "字符串处理"],
      ["4", "斐波那契数列", "入门", "递归、数学", "递归与递推"],
      ["5", "字符出现次数统计", "入门", "哈希、字符串", "哈希表入门"],
      ["6", "最大值与它的位置", "入门", "模拟、枚举", "数组与模拟"],
      ["7", "凯撒密码", "入门", "字符串、模拟", "字符串处理"],
      ["8", "求阶乘", "入门", "递归、数学", "递归与递推"],
      ["9", "二分查找", "基础", "二分", "二分专题"],
      ["10", "第 k 小的数", "基础", "排序", "排序与区间"],
      ["11", "括号匹配", "基础", "栈、字符串", "栈的应用"],
      ["12", "区间合并", "基础", "排序、模拟", "排序与区间"],
      ["13", "阶乘末尾零的个数", "基础", "数学、模拟", "数学与枚举"],
      ["14", "爬楼梯", "基础", "递归、数学", "递归与递推"],
      ["15", "日期差", "基础", "模拟、数学", "数组与模拟"],
      ["16", "砍树（二分答案）", "基础", "二分、贪心", "二分专题"],
    ],
    [700, 3000, 900, 2300, 2738]
  ),
  gap(),
  body("全文完。若在使用中发现问题，欢迎在 GitHub 仓库提 Issue：github.com/yu1217-lan0104/python-oj"),
];

/* ------------------------------------------------------------------ */
/* 文档组装                                                            */
/* ------------------------------------------------------------------ */

const header = new Header({
  children: [
    new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "D9E2EF", space: 4 } },
      children: [new TextRun({ text: "新手 Python 算法练习场 · 使用说明书", size: 16, color: "7A869A", font: FONT_HEAD })],
    }),
  ],
});

const footer = new Footer({
  children: [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ text: "第 ", size: 16, color: "7A869A" }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "7A869A" }),
        new TextRun({ text: " 页", size: 16, color: "7A869A" }),
      ],
    }),
  ],
});

const doc = new Document({
  creator: "python-oj",
  title: "新手 Python 算法练习场 使用说明书",
  description: "本地刷题系统的用户手册",
  styles: {
    default: {
      document: { run: { font: FONT_BODY, size: 21, color: "101828" }, paragraph: { spacing: { line: 330 } } },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: FONT_HEAD, color: "1E3A8A" },
        paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 25, bold: true, font: FONT_HEAD, color: "1F2937" },
        paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 },
      },
      {
        id: "TOCHeading",
        name: "TOC Heading",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 34, bold: true, font: FONT_HEAD, color: "1E3A8A" },
        paragraph: { spacing: { after: 260 }, alignment: AlignmentType.CENTER },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bul",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 700, hanging: 320 } }, run: { size: 21 } },
          },
        ],
      },
      ...["n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8"].map((reference) => ({
        reference,
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 700, hanging: 320 } }, run: { size: 21 } },
          },
        ],
      })),
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1134, bottom: 1440, left: 1134 },
        },
      },
      children: [...cover, new Paragraph({ children: [new PageBreak()] })],
    },
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1134, bottom: 1440, left: 1134 },
          pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN },
        },
      },
      headers: { default: header },
      footers: { default: footer },
      children: [...toc],
    },
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1134, bottom: 1440, left: 1134 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL },
        },
      },
      headers: { default: header },
      footers: { default: footer },
      children: [...ch1, ...ch2, ...ch3, ...ch4, ...ch5, ...ch6, ...ch7],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(OUT, buffer);
  console.log(`written: ${OUT} (${(buffer.length / 1024).toFixed(1)} KB)`);
});



