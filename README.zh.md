[English](README.md) | [한국어](README.ko.md) | 中文 | [日本語](README.ja.md) | [Español](README.es.md)

# sangse (상세) — 韩国电商详情页生成器

<p align="center">
  <img src="assets/sangse-hero.png" alt="sangse — example anchor cut (fictional product)" width="320">
</p>

这是一个 Claude Code 插件，把产品信息转化为**经过验证的图片切片稿**——也就是韩国电商详情页（Kurly、Coupang、Naver 智能商店(Smart Store)、品牌自营商城）真正在用的格式：12~20 张纵向排列的图片切片，文案直接渲染在图片内，再加上一段 HTML 法规信息块。

在线示例（虚构的健康食品）：https://fivetaku.github.io/sangse/

## 功能说明

1. **依赖检查**——确认 gptaku-plugins 市场、`pumasi`（`/pumasi:image`，Codex 图片生成）、Playwright 和 python3 是否就位；可用 `--install` 一键安装。
2. **产品访谈**——只针对确实不明确的信息槽提问（目标客群、平台、流量来源、证据、退款政策、受监管品类），最多 4 个问题 × 2 轮。
3. **写文案前先检查 offer**——offer 是指客户能得到什么 + 消除了哪种顾虑 + 为什么现在买。offer 太弱会在动笔写文案之前就被标记出来。
4. **切片稿**（`cuts.md` + `legal.md`）——默认 14 张切片，按客户付款前默默自问的 8 个问题排序（这适合我吗 → 我能得到什么 → 为什么是这种方式 → 我做得到吗 → 有多难 → 具体是什么 → 万一失败怎么办 → 为什么是现在）。每张切片只传达一个信息：标题 ≤17 字，正文 ≤3 行，附背景色和视觉说明。29 个切片模板均从真实页面（健康食品、时尚、服务）实测提炼。价格、电话号码、营养成分表和法规声明一律保留在 HTML 中。
5. **验证，三道关卡**
   - 关卡 1 `check_cuts.py`——确定性检查：模板槽位上限、8 问覆盖度、**每个数字都能追溯到输入**、品类禁用词、法规信息块、图片是否存在。
   - 关卡 2——四个独立的评审代理（持怀疑态度的目标客户、监管审查员、CRO 评审、竞品营销人员）。通过标准 = 客户对全部 8 个问题都回答"是"，且监管违规为零；最多 2 轮。
   - 关卡 3 `render_check.py`——用 Playwright 在 390/860 px 下真实渲染，并对首屏做 5 秒测试。
6. **切片图片**通过 `/pumasi:image` 生成——先生成锚点切片，其余切片用 `--ref` 串联，每张都会检查文字准确性**以及**产品合理性（包装是否密封、数量、手指等）。
7. **HTML 组装**——切片无缝上下拼接，法规信息块置于下方，智能商店 860 px / 网页 720 px。

**铁律**：输入里没有的内容一律不得编造——不虚构案例、数字、评价、退款条款或截止日期。缺失的部分以 `[자료 필요: …]` 占位符留空，并在报告中列出。

## 适合谁用 (이런 분을 위한 도구입니다)

- 已经做出产品、现在需要一页能卖货而不是像规格表的详情页的独立创业者和 vibe coder。
- 希望文案、图片和法规信息块一起生成、一起验证的智能商店 / Coupang / Kmong 卖家。
- 任何需要把功能清单式的产品页改写成客户语言、又不能凭空添加主张的人。

## 环境要求 (요구사항)

- 已添加 gptaku-plugins 市场的 Claude Code；生成图片切片需要 `pumasi` 插件（可选——没有它，技能会在文案 + HTML 占位符处停止）
- 已登录且启用了 `image_generation` 的 Codex CLI（图片后端）
- python3（关卡脚本和组装器仅使用标准库）
- Node + Playwright，用于关卡 3 的渲染检查（可选；会自动识别 `~/.insane-search/node/node_modules`）
- `bash skills/sangse/scripts/check_deps.sh --install` 可检查并安装以上依赖

## 安装

```bash
claude plugin marketplace add fivetaku/gptaku_plugins
claude plugin install sangse@gptaku-plugins
claude plugin install pumasi@gptaku-plugins     # image generation backend
codex features enable image_generation
```

安装完成后请重启 Claude Code 会话。然后：

```
/sangse <product info as text, a file path, or a URL>
/sangse 카피만 …        # stop after copy approval, no images
```

或者直接说"상세페이지 만들어줘"——技能会自动触发。

## 组件 (구성요소)

| 路径 | 作用 |
|---|---|
| `commands/sangse.md` | 唯一入口（`/sangse`），参数路由 |
| `skills/sangse/SKILL.md` | 工作流（Step 0 依赖检查 → 访谈 → offer 检查 → 切片稿 → 3 道关卡 → 图片 → HTML → 报告）、铁律、红旗信号 |
| `skills/sangse/references/` | `framework.md`（8 个问题）、`cut-sheet.md`、`reference-patterns.md`（拆解 7 个真实页面，29 个模板）、`interview.md`、`compliance.md`、`verification.md`、`evidence.md`、`image-briefs.md`、`reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`、`check_cuts.py`、`check_copy.py`、`assemble_html.py`、`render_check.py`、`capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`、`banned-words.json`、`template.html` |
| `setup/` | 首次运行设置（gptaku 标准） |
| `examples/` | 三个虚构产品，包含完整的产物链和 `qa/` 结果 |

## 合规

`references/compliance.md` 收录了针对**食品和健康功能食品**的详细过滤规则（《食品标示与广告法》第 8 条、已批准的功能性表述用语、事前审查、强制标示、一般食品的功能性表述规则），以及化妆品、医疗器械、金融、教育、房地产和电子产品的法规索引。这些品类的专项过滤规则正在完善中。此处内容均不构成法律建议；最终用语以相关审查机构的意见为准。

## 参考页面拆解

该格式来源于在有界面的浏览器中抓取真实详情页并逐张切片拆解：Kurly、Coupang 和一家品牌商城（同一款健康食品在三个渠道的页面）、Samsung.com、LG.com、Musinsa（时尚）以及 Kmong（服务）。发现、测量数据和 29 个模板收录在 `references/reference-patterns.md`；抓取流程和各渠道的坑（智能商店登录墙、Coupang 反爬拦截）记录在 `references/reference-capture.md`，配套脚本为 `scripts/capture_reference.js`。

## 更新日志

参见 [CHANGELOG.md](CHANGELOG.md)。发布流程（版本号提升 → GitHub release → 市场子模块指针 → 缓存）遵循 [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md)；每次提升版本前 `tests/test-gates.sh` 必须通过。

## 许可证 (라이선스)

MIT——参见 [LICENSE](LICENSE) 和 [DISCLAIMER.md](DISCLAIMER.md)。
