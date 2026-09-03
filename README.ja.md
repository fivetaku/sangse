[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | 日本語 | [Español](README.es.md)

# sangse (상세)

<p align="center">
  <img src="assets/sangse-hero-01.png" alt="sangse" width="320">
</p>

> **商品を「売れる」詳細ページに — スペック表ではなく、検証済みの画像カットシートを。**

商品の事実を渡すだけで、韓国コマースが実際に使っている形式が返ってきます。コピーを画像の中に入れた 12~20 枚の縦積みイメージカットに、HTML の法定表示ブロックを添えて。すべての主張は入力に遡って裏づけられます。

[クイックスタート](#クイックスタート) • [なぜ sangse なのか](#なぜ-sangse-なのか-이런-분을-위한-도구입니다) • [仕組み](#仕組み) • [機能](#機能) • [動作要件](#動作要件-요구사항)

実例（架空の健康食品）: https://fivetaku.github.io/sangse/

---

## クイックスタート

### 1. マーケットプレイスを追加（初回のみ）

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. インストール

```
/plugin install sangse
/plugin install pumasi          # 画像生成バックエンド (/pumasi:image)
```

インストール後、Claude Code を再起動してください。

### 3. 画像バックエンドを有効化

```bash
codex features enable image_generation
```

### 4. 実行

```
/sangse <商品情報をテキスト、ファイルパス、または URL で>
/sangse 카피만 <商品情報>        # コピー承認後に停止、画像は生成しない
/sangse check sangse/<slug>          # 既存フォルダに対して検証ゲートを再実行
```

あるいは、そのまま話しかけるだけでも動きます — 「상세페이지 만들어줘」「この商品の詳細ページを作って」。

---

## なぜ sangse なのか (이런 분을 위한 도구입니다)

- **作ったのは商品であって、販売ページではない** — 機能一覧ではなく、成約につながる詳細ページが必要なソロファウンダーやバイブコーダーのために。
- **Kurly、Coupang、Naver スマートストアで販売している** — 出力は各チャネルが実際に使う画像カットシートで、アップロード用にサイズ済み（スマートストア 860 px / ウェブ 720 px）。
- **コピー・画像・法定表示ブロックをまとめて検証したい** — 3 つのゲートが、公開前にテンプレートの溢れ、根拠のない数字、禁止表現、必須表示の欠落を捕捉します。
- **でっち上げの主張は受け入れない** — 鉄の掟: 入力にないものは書かない。不足分は `[자료 필요: …]` プレースホルダーと ToDo 表になります。

---

## 仕組み

```
商品の事実 (テキスト / ファイル / URL)
        │
        ▼
Step 0  依存関係チェック          check_deps.sh  (--install)
Step 1  商品インタビュー          不確かなスロットのみ · 最大4問 × 2ラウンド
Step 2  オファーチェック          顧客が得るもの + 取り除く不安 + なぜ今なのか
Step 2½ スタイルパック          インタビューで 6 パックから 1 つを選択（推奨を事前表示）— カット順序・配色戦略・強調・ビジュアルモードを決定
Step 3  カットシート              cuts.md (デフォルト14カット) + legal.md
Step 3½ 推敲                     humanize_cuts.py — GPT（Codex CLI）が各カットの意図を読み取り、人が書いたように書き直す。カット単位のガードで数値・プレースホルダー・スロット上限を保持
        │
        ├─ Gate 1  check_cuts.py       決定論的: スロット上限 · Q カバレッジ · 全数字の根拠 · 禁止語 · 法定ブロック
        ├─ Gate 2  4体のレビュアーエージェント   懐疑的な顧客 · 規制審査官 · CRO レビュアー · 競合マーケター
        └─ コピー承認
        │
Step 4  カット画像                /pumasi:image — アンカーカットを先に、残りは --ref で連鎖、テキストと物理的な妥当性を検査
Step 5  HTML 組み立て             assemble_html.py — カットを隙間なく縦積み、法定ブロックはその下
        │
        └─ Gate 3  render_check.py     Playwright で 390 / 860 px にレンダリング + ファーストビューの5秒テスト
        │
        ▼
sangse/<slug>/  cuts.md · legal.md · images/ · index.html · qa/ · scorecard
```

カットは **顧客が支払う前に心の中で問う 8 つの質問** に沿って並びます: これは自分向けか → 何が得られるか → なぜこのやり方か → 自分にできるか → どれくらい難しいか → 具体的に何を受け取るか → 失敗したらどうなるか → なぜ今か。

---

## 機能

| 機能 | 説明 |
|---------|-------------|
| 画像カットシート形式 | 12~20 カット、幅 1000 px、コピーは画像内に描画。価格・電話番号・栄養成分表・法定表示は HTML に残す |
| 実測済み 29 種のカットテンプレート | 実際のページを解剖 — Kurly、Coupang、ブランドモール、Samsung、LG、Musinsa（ファッション）、Kmong（サービス） |
| 不確実性駆動のインタビュー | 入力から推測できないことだけを質問。最大 4 問 × 2 ラウンド |
| コピー前のオファーチェック | 弱いオファーは、コピーを 1 行も書く前に指摘 |
| GPT 推敲パス | 別モデル（Codex CLI）が各カットの言いたいことを解釈し、AI 臭（翻訳調、広告の常套句、単調なリズム、ぼかし表現 — humanize-korean の規則を借用）を除いて書き直す。数値の追加、プレースホルダーの欠落、スロット超過、禁止語の混入があるカットはコードが拒否して原文を保持 |
| スタイルパック | 「どう説得するか」を選ぶ: 悩みシーンのストーリー型 / 要点チェックリスト型 / 根拠・数値優先型 / ルックブック型 / スペックショーケース型 / 特典・構成プロモーション型。パックがカット順序・タイポ上限・背景戦略・強調・ビジュアルモード・画像プロンプトのスタイルを決める（国内の商品詳細 17 ページを解剖して実測）。パック内にブランド名・サイト名は一切なし |
| Gate 1 — 決定論的チェッカー | `check_cuts.py`: テンプレートのスロット上限、Q1~Q8 カバレッジ、全数字の入力への遡及、カテゴリ別禁止語、必須法定ブロック、画像の存在 |
| Gate 2 — 4 体のレビュアーエージェント | 執筆者とは別。合格 = 顧客が 8 問すべてに「はい」と答え、規制違反ゼロ。最大 2 ラウンド |
| Gate 3 — 実レンダリング | `render_check.py`: Playwright で 390 / 860 px にレンダリングし、ファーストビューの 5 秒テスト |
| 検査付きカット画像 | `/pumasi:image` アンカー → `--ref` 連鎖。全カットでテキストの正確さ **と** 商品の妥当性（密封包装、個数、指）を確認 |
| コンプライアンスフィルター | `references/compliance.md`: 食品・健康機能食品の詳細ルール（食品表示・広告法 第 8 条、認可された機能性表示、事前審査、必須表示）と、化粧品・医療機器・金融・教育・不動産・電子機器の法令インデックス — これらのカテゴリ別フィルターは整備中 |
| 鉄の掟 | 事例・数字・レビュー・返金条件・期限のでっち上げ禁止 — 代わりにプレースホルダー |

ここに書かれた内容は法的助言ではありません。最終的な文言は該当する審査機関の判断に従います。

---

## コマンド

| コマンド | 説明 |
|---------|-------------|
| `/sangse <商品情報>` | フル実行: インタビュー → カットシート → ゲート → 画像 → HTML → スコアカード |
| `/sangse 카피만 <商品情報>` | コピーのみ — コピー承認ゲートで停止 |
| `/sangse 스마트스토어 <商品情報>` | プラットフォームを事前指定（`웹`、`크몽` も可）、該当するインタビュー質問をスキップ |
| `/sangse check <dir>` | 既存の `sangse/<slug>` フォルダに対して検証ゲートのみ実行 |
| `/sangse humanize <dir>` | 既存フォルダに GPT 推敲パスだけを実行し、採用・拒否の内訳を表示 |
| `/sangse --style <pack> <商品情報>` | スタイルの質問を省き、パックを指定（`story-first`、`checkpoint`、`proof-first`、`lookbook`、`spec-showcase`、`offer-first`） |

### 自然言語トリガー

- 「상세페이지 만들어줘」「스마트스토어 상세 만들어줘」「세일즈 페이지 써줘」「이 제품 소개 페이지 써줘」
- 「詳細ページを作って」「商品ページのコピー」「セールスページのコピー」「ランディングページのコピー」

---

## 構成要素 (구성요소)

| パス | 役割 |
|---|---|
| `commands/sangse.md` | 単一エントリーポイント（`/sangse`）、引数ルーティング |
| `skills/sangse/SKILL.md` | ワークフロー（Step 0 → インタビュー → オファーチェック → カットシート → 3 ゲート → 画像 → HTML → レポート）、鉄の掟、レッドフラグ |
| `skills/sangse/references/` | `framework.md`（8 つの質問）、`cut-sheet.md`、`reference-patterns.md`（実ページ 7 件の解剖、29 テンプレート）、`interview.md`、`humanize.md`（GPT 書き直しプロンプト + ガード）、`style-packs.md`（6 パック・推奨ルール・共通文法）、`compliance.md`、`verification.md`、`evidence.md`、`image-briefs.md`、`reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`、`humanize_cuts.py`、`check_cuts.py`、`check_copy.py`、`assemble_html.py`、`render_check.py`、`capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`、`banned-words.json`、`humanize-schema.json`、`style-packs/*.json`（6 パック + スキーマ）、`template.html` |
| `setup/` | 初回セットアップ（gptaku 標準） |
| `tests/test-gates.sh` | リグレッション: 3 つの例で Gate 1 PASS、アセンブラーのスモーク、推敲ガード、依存関係チェック、フロントマター契約 |
| `examples/` | 架空の商品 3 点。成果物の全履歴と `qa/` 結果つき |

---

## 動作要件 (요구사항)

- gptaku-plugins マーケットプレイスを追加した [Claude Code](https://docs.anthropic.com/claude-code) CLI
- カット画像用の `pumasi` プラグイン（任意 — なければ実行はコピー + HTML プレースホルダーで停止）
- ログイン済みで `image_generation` を有効にした [Codex CLI](https://github.com/openai/codex)（画像バックエンド）
- python3 — ゲートとアセンブラーは標準ライブラリのみ使用
- （任意）Gate 3 のレンダリングチェック用の Node + Playwright。`~/.insane-search/node/node_modules` は自動的に検出
- `bash skills/sangse/scripts/check_deps.sh --install` で上記を確認・インストール

---

## 変更履歴

[CHANGELOG.md](CHANGELOG.md) を参照してください。リリース手順（バージョンアップ → GitHub リリース → マーケットプレイスのサブモジュールポインター → キャッシュ）は [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md) に従います。バージョンを上げる前には必ず `tests/test-gates.sh` を通過させてください。

---

## ライセンス (라이선스)

MIT — [LICENSE](LICENSE) と [DISCLAIMER.md](DISCLAIMER.md) を参照してください。

---

<div align="center">

**商品の事実を入れる。売れる詳細ページが出てくる — でっち上げは一切なし。**

</div>
