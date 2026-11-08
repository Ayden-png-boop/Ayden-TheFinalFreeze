# 冰川信使：斑头雁的2040 · Glacier Messenger 2040

> 改编自 Ayden 参赛作品《冰川信使：斑头雁的2040》的手机端 **H5 剧情互动游戏**。
> 玩家扮演斑头雁「雪翼」，在冰川加速消融的 2040 年带领雁群完成最后一次迁徙。

四语（中 / 英 / 日 / 法）界面与全程 AI 配音 · 八章剧情 · 三种结局 · 27 段实拍／生成视频素材 · 零外部 CDN 依赖。

---

## 玩法

- **八章线性推进**：每章播放一段剧情视频，旁白逐句播放并高亮，玩家在关键节点做出选择。
- **状态系统**：`协作 / 激进度 / 体能` 三项数值随选择浮动，并决定分支走向与结局。
- **证据链与隐藏状态**：拍到采矿机照片、安装监测仪、获取冰芯数据等行为会解锁后续选项。
- **限时选择（QTE）**：部分节点有时间压力，超时按保守分支处理。
- **三种结局**：`黎明 hope` / `他乡 adaptation` / `末路 doom`。
- **催选机制**：旁白读完、视频播完仍未选择时，自动弹出底部选择抽屉，避免玩家卡住。
- **无障碍与容错**：旁白默认只显示当前一句，可一键展开全文；自动播放被浏览器拦截时提供「轻触播放」兜底。

## 技术栈

| 层 | 选型 |
|---|---|
| 构建 | Vite 7 |
| UI | React 19（函数组件 + Hooks，无路由库） |
| 样式 | Tailwind CSS v4（`@tailwindcss/vite`） |
| 图标 | lucide-react |
| 音频 | edge-tts 预生成 MP3（460 段，四语） |
| 视频 | 原生 `<video>` + 自研元素池 |
| 统计后端 | Node 内置模块，零第三方依赖 |
| 后台前端 | React + 自研 SVG 图表 |

## 目录结构

```
glacier-messenger-h5/        游戏本体（Vite 工程）
├── src/
│   ├── App.jsx              主流程：章节推进、状态结算、浮层与结局
│   ├── story/
│   │   ├── story.js         剧情数据：章节 / 选项 / 效果 / 条件 / 结局
│   │   ├── engine.js        结算与条件求值
│   │   └── vo-runtime.json  配音时间轴（逐句 duration，用于高亮同步）
│   ├── components/
│   │   ├── Chrome.jsx       标题、语言切换
│   │   ├── StatusPanel.jsx  三项状态环
│   │   ├── Narration.jsx    旁白折叠 / 展开 / 逐句高亮
│   │   ├── ChoicePrompt.jsx 选项按钮与催选抽屉
│   │   ├── PooledVideo.jsx  池化视频元素（WebP/JPG 封面兜底、手势兜底）
│   │   ├── QteOverlay.jsx   限时选择层
│   │   ├── Overlays.jsx     结局 / 提示浮层
│   │   └── LiveTicker.jsx   实时在线人数播报
│   ├── hooks/
│   │   ├── useVideoPool.js  预取、LRU 复用、播放门闸
│   │   ├── useVoiceOver.js  配音调度与结束回调
│   │   └── useStats.js      匿名统计上报
│   └── i18n/ui.js           四语界面文案
├── public/
│   ├── videos/              27 段剧情视频（H.264 Main，faststart）
│   ├── posters/             封面图 WebP + JPG 双份
│   ├── voice/{zh,en,ja,fr}/ 四语配音 MP3
│   └── diag.html            单文件真机自检页（内核/CSS/编解码/实测播放）
├── admin/                   访问统计后台前端
└── index.html

admin-backend/               统计后端（Node，零依赖）
├── server.js                HTTP 服务、登录会话、静态托管、埋点接口
├── store.js                 数据落盘与聚合
└── config.example.json      账号配置模板
```

## 本地运行

```bash
# 游戏
cd glacier-messenger-h5
npm install
npm run dev          # 默认 http://localhost:5173
npm run build        # 产物在 dist/

# 后台（另开终端）
cd admin-backend
cp config.example.json config.json   # 首次：把 adminPass 改成自己的密码，启动时自动转为加盐哈希
node server.js       # 默认 127.0.0.1:8787，访问 /Ayden-BHG/admin/
```

后台前端需要先构建：`cd glacier-messenger-h5 && npx vite build -c vite.config.admin.js`。

## 部署要点

- 线上地址：<https://redspiderbc.cn/Ayden-TheFinalFreeze/>（旧路径 `/Ayden-BHG/national/` 仍在线）。
- 站点以子路径方式托管，构建时必须带对应的 `--base`（如 `--base=/Ayden-TheFinalFreeze/`），否则资源全 404。
  媒体路径由 `import.meta.env.BASE_URL` 拼接、统计接口用相对 `./api`，因此换路径时需同时配好静态目录与 `/api/` 反代。
- Linux 文件系统大小写敏感：素材文件名必须与代码引用**逐字符一致**，建议一次 `grep -o "videos/[a-z0-9_]*\.mp4"` 与 `ls public/videos` 做交叉核对。
- 视频 `/posters` 与 `/voice` 体积较大（约 58 MB），建议与代码分两次发布，并开启 `gzip_static` 与长缓存。
- 老内核 CSS 兜底：Tailwind v4 产出的 `oklch()` / `color-mix()` / `@layer` / `in oklab` 在旧 WebView 上会整块失效，仓库内的构建流程对此做了后处理，替换为等价的 hex / rgba 与展平后的规则。

## 浏览器与兼容性

目标基线：Chrome / Edge 111+、Safari 16.4+、微信内置浏览器（X5 / XWeb）、Firefox 128+。

已在无头 Chrome 中对六种 UA 做过回归，重点保障：

- `100dvh` 兼容（用 CSS 变量 + `vh` 兜底）、`env(safe-area-inset-*)` 安全区（`max(1rem, env(...))` 写法，老内核整条作废时退回固定内边距）。
- `aspect-ratio` 以 `padding-bottom` 百分比兜底。
- `<picture>` + `image/webp`，缺 WebP 时回落到 JPG。
- 移动端自动播放限制：`play()` 被拒时静音重试，仍失败才显示「轻触播放」，并在 `pause` 事件补播。
- iOS Safari 预取：游离的 `display:none` 视频不会被取数，需挂到隐藏宿主节点。

真机自检：打开 `public/diag.html`，一次点击即可输出内核判定、CSS 支持项、编解码能力与实测播放结果。

## 素材与版权

- 剧情、分镜与原始视频素材来自 Ayden 的参赛作品《冰川信使：斑头雁的2040》。
- 配音由 edge-tts 预生成（四语），仅用于本作品。
- 代码以 MIT 协议开源；**视频、配音与美术素材不在 MIT 授权范围内**，转载或二次使用请联系原作者。

## 未入库内容

`.gitignore` 已排除：`node_modules/`、各类 `dist*/`、视频高画质备份、素材解包目录、部署脚本与服务器私钥、后台账号配置与用户统计数据。
如需在服务器上复现部署，请自行按上文「部署要点」准备。
