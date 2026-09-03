[English](README.md) | [한국어](README.ko.md) | 中文 | [日本語](README.ja.md) | [Español](README.es.md)

# sangse (상세)

<p align="center">
  <img src="assets/sangse-hero-01.png" alt="sangse" width="320">
</p>

> **把产品变成能卖货的详情页 — 一份经过验证的图片切图稿，而不是规格表。**

给它产品事实，拿回韩国电商真正在用的格式：12~20 张纵向堆叠的图片切图，文案直接排在图内，外加一段 HTML 法务信息块 — 每一条主张都能追溯到你的输入。

[快速开始](#快速开始) • [为什么选 sangse](#为什么选-sangse-이런-분을-위한-도구입니다) • [工作原理](#工作原理) • [功能](#功能) • [环境要求](#环境要求-요구사항)

在线示例（虚构的健康食品产品）：https://fivetaku.github.io/sangse/

---

## 快速开始

### 1. 添加市场（仅需一次）

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. 安装

```
/plugin install sangse
/plugin install pumasi          # 图片生成后端 (/pumasi:image)
```

安装后请重启 Claude Code。

### 3. 启用图片后端

```bash
codex features enable image_generation
```

### 4. 运行

```
/sangse <产品信息：文本、文件路径或 URL>
/sangse 카피만 <产品信息>        # 文案审批后停止，不生成图片
/sangse check sangse/<slug>          # 对已有文件夹重新运行验证关卡
```

或者直接说 — "상세페이지 만들어줘"、"给这个产品做一个详情页"。

---

## 为什么选 sangse？(이런 분을 위한 도구입니다)

- **你做出了产品，却没有销售页** — 独立创业者和 vibe-coder，需要的是能转化的详情页，而不是功能清单。
- **你在 Kurly、Coupang 或 Naver 智能商店（Smart Store）上销售** — 输出正是这些渠道实际使用的图片切图稿，尺寸已按上传要求设定（智能商店 860 px / 网页 720 px）。
- **你需要文案、图片和法务信息块一起通过验证** — 三道关卡在发布前拦下模板溢出、无法溯源的数字、违禁主张和缺失的强制标注。
- **你不接受凭空编造的主张** — 铁律：输入里没有的内容一律不写。空缺会变成 `[자료 필요: …]` 占位符和一张待办表。

---

## 工作原理

```
产品事实 (文本 / 文件 / URL)
        │
        ▼
Step 0  依赖检查                  check_deps.sh  (--install)
Step 1  产品访谈                  只问不确定的槽位 · ≤4 个问题 × 2 轮
Step 2  报价检查                  顾客得到什么 + 消除哪种顾虑 + 为什么是现在
Step 2½ 风格包                    访谈从 6 个风格包中选 1 个（预选推荐项）——决定切图顺序、配色策略、强调、视觉模式
Step 3  切图稿                    cuts.md (默认 14 张切图) + legal.md
Step 3½ 润色                      humanize_cuts.py — GPT（Codex CLI）重新读出每个切图的意图，像人一样重写文案；逐切图守卫保留数字、占位符和槽位上限
        │
        ├─ Gate 1  check_cuts.py       确定性检查: 槽位上限 · Q 覆盖 · 每个数字可溯源 · 违禁词 · 法务块
        ├─ Gate 2  4 个审阅代理        多疑的顾客 · 监管审查员 · CRO 审阅者 · 竞品营销人员
        └─ 文案审批
        │
Step 4  切图图片                  /pumasi:image — 先生成锚点切图，其余用 --ref 串联，检查文字与物理合理性
Step 5  HTML 组装                 assemble_html.py — 切图无缝堆叠，法务块置于下方
        │
        └─ Gate 3  render_check.py     Playwright 在 390 / 860 px 下渲染 + 首屏 5 秒测试
        │
        ▼
sangse/<slug>/  cuts.md · legal.md · images/ · index.html · qa/ · scorecard
```

切图遵循**顾客付款前默默自问的 8 个问题**：这是给我的吗 → 我能得到什么 → 为什么是这种方式 → 我做得到吗 → 有多难 → 我究竟会收到什么 → 失败了怎么办 → 为什么是现在。

---

## 功能

| 功能 | 说明 |
|---------|-------------|
| 图片切图稿格式 | 12~20 张切图，宽度 1000 px，文案渲染在图内；价格、电话号码、营养成分表和法务声明保留在 HTML 中 |
| 29 个实测切图模板 | 从真实页面拆解而来 — Kurly、Coupang、某品牌商城、三星、LG、Musinsa（时尚）、Kmong（服务） |
| 不确定性驱动的访谈 | 只问无法从输入推断的内容；最多 4 个问题 × 2 轮 |
| 写文案前先做报价检查 | 在写下第一行文案之前就标出薄弱的报价 |
| GPT 润色 | 第二个模型（Codex CLI）解读每个切图想说什么，并去掉 AI 痕迹（翻译腔、广告套话、节奏单一、含糊其辞 — 规则借自 humanize-korean）后重写；凡新增数字、丢失占位符、超出槽位或引入禁用词的切图，代码一律拒绝并保留原文 |
| 风格包 | 选择"怎样说服"：痛点场景故事型 / 要点清单型 / 证据数字优先型 / 图册型（图片为主、少文案）/ 规格橱窗型（功能、对比、参数表）/ 优惠构成促销型（促销落地页）。风格包决定切图顺序、字数上限、背景策略、强调方式、视觉模式和生图提示词风格——来自 17 个真实韩国详情页的拆解实测。包内不含任何品牌或站点名 |
| Gate 1 — 确定性检查器 | `check_cuts.py`：模板槽位上限、Q1~Q8 覆盖、每个数字可追溯到输入、品类违禁词、强制法务块、图片是否存在 |
| Gate 2 — 四个审阅代理 | 与撰写者分离；通过 = 顾客对 8 个问题全部回答"是"且零监管违规，最多 2 轮 |
| Gate 3 — 真实渲染 | `render_check.py`：Playwright 在 390 / 860 px 下渲染，外加首屏 5 秒测试 |
| 带检查的切图图片 | `/pumasi:image` 锚点 → `--ref` 串联；每张切图都检查文字准确性**以及**产品合理性（密封包装、数量、手指） |
| 合规过滤器 | `references/compliance.md`：食品和健康功能食品的详细规则（《食品标示与广告法》第 8 条、获批功能性主张、事前审查、强制标注），以及化妆品、医疗器械、金融、教育、房地产和电子产品的法规索引 — 这些品类的专用过滤器正在开发中 |
| 铁律 | 不编造案例、数字、评价、退款条款或截止日期 — 一律用占位符代替 |

以上内容均不构成法律建议；最终措辞以相关审查机构为准。

---

## 命令

| 命令 | 说明 |
|---------|-------------|
| `/sangse <产品信息>` | 完整运行：访谈 → 切图稿 → 关卡 → 图片 → HTML → 记分卡 |
| `/sangse 카피만 <产品信息>` | 仅文案 — 在文案审批关卡后停止 |
| `/sangse 스마트스토어 <产品信息>` | 预设平台（也可用 `웹`、`크몽`），跳过对应的访谈问题 |
| `/sangse check <dir>` | 只对已有的 `sangse/<slug>` 文件夹运行验证关卡 |
| `/sangse humanize <dir>` | 仅对现有文件夹运行 GPT 润色，并显示采用与拒绝明细 |
| `/sangse --style <pack> <产品信息>` | 跳过风格提问，直接指定风格包（`story-first`、`checkpoint`、`proof-first`、`lookbook`、`spec-showcase`、`offer-first`） |

### 自然语言触发

- "상세페이지 만들어줘"、"스마트스토어 상세 만들어줘"、"세일즈 페이지 써줘"、"이 제품 소개 페이지 써줘"
- "做一个详情页"、"产品页文案"、"销售页文案"、"落地页文案"

---

## 组件 (구성요소)

| 路径 | 作用 |
|---|---|
| `commands/sangse.md` | 单一入口（`/sangse`），参数路由 |
| `skills/sangse/SKILL.md` | 工作流（Step 0 → 访谈 → 报价检查 → 切图稿 → 3 道关卡 → 图片 → HTML → 报告）、铁律、红旗信号 |
| `skills/sangse/references/` | `framework.md`（8 个问题）、`cut-sheet.md`、`reference-patterns.md`（拆解 7 个真实页面，29 个模板）、`interview.md`、`humanize.md`（GPT 重写提示词 + 守卫）、`style-packs.md`（6 个风格包、推荐规则、通用语法）、`compliance.md`、`verification.md`、`evidence.md`、`image-briefs.md`、`reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`、`humanize_cuts.py`、`check_cuts.py`、`check_copy.py`、`assemble_html.py`、`render_check.py`、`capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`、`banned-words.json`、`humanize-schema.json`、`style-packs/*.json`（6 个风格包 + 模式）、`template.html` |
| `setup/` | 首次运行设置（gptaku 标准） |
| `tests/test-gates.sh` | 回归测试：三个示例通过关卡 1、组装器冒烟测试、润色守卫、依赖检查、frontmatter 契约 |
| `examples/` | 三个虚构产品，附完整产物链和 `qa/` 结果 |

---

## 环境要求 (요구사항)

- 已添加 gptaku-plugins 市场的 [Claude Code](https://docs.anthropic.com/claude-code) CLI
- 用于生成切图图片的 `pumasi` 插件（可选 — 没有它，运行会停在文案 + HTML 占位符）
- 已登录且启用了 `image_generation` 的 [Codex CLI](https://github.com/openai/codex)（图片后端）
- python3 — 关卡和组装器仅使用标准库
- （可选）Node + Playwright 用于关卡 3 的渲染检查；会自动使用 `~/.insane-search/node/node_modules`
- `bash skills/sangse/scripts/check_deps.sh --install` 可检查并安装上述依赖

---

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)。发布流程（版本号提升 → GitHub release → 市场子模块指针 → 缓存）遵循 [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md)；每次提升版本前必须通过 `tests/test-gates.sh`。

---

## 许可证 (라이선스)

MIT — 见 [LICENSE](LICENSE) 和 [DISCLAIMER.md](DISCLAIMER.md)。

---

<div align="center">

**输入产品事实。输出一个能卖货的详情页 — 没有任何编造。**

</div>
