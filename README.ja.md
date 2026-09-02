[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | 日本語 | [Español](README.es.md)

# sangse (상세) — 韓国 EC 向け商品詳細ページビルダー

<p align="center">
  <img src="assets/sangse-hero.png" alt="sangse — example anchor cut (fictional product)" width="320">
</p>

商品の事実情報から、**検証済みの画像カットシート**を生成する Claude Code プラグインです。韓国のコマース詳細ページ（Kurly、Coupang、Naver スマートストア、ブランドモール）で実際に使われている形式、つまり縦に積み重ねた 12〜20 枚の画像カット（コピーは画像内に描き込み）と、HTML の法的表記ブロックを出力します。

ライブサンプル（架空の健康食品）: https://fivetaku.github.io/sangse/

## できること

1. **依存関係チェック** — gptaku-plugins マーケットプレイス、`pumasi`（`/pumasi:image`、Codex による画像生成）、Playwright、python3 の有無を確認し、`--install` を提案します。
2. **商品インタビュー** — 本当に不確かなスロット（ターゲット、プラットフォーム、流入経路、根拠、返金ポリシー、規制対象カテゴリ）だけを質問します。最大 4 問 × 2 ラウンド。
3. **コピーの前にオファーを確認** — オファーとは「顧客が受け取るもの + 取り除かれる不安 + なぜ今なのか」です。オファーが弱ければ、コピーを書く前にその旨を指摘します。
4. **カットシート**（`cuts.md` + `legal.md`）— 既定で 14 カット。顧客が支払う前に心の中で問う 8 つの質問（自分向きか → 何が得られるか → なぜこの方法か → 自分にもできるか → どれくらい大変か → 具体的には何か → 失敗したらどうなるか → なぜ今か）の順に並べます。1 カット = 1 メッセージ: 見出し 17 文字以内、本文 3 行以内、背景色、ビジュアル指示。実際のページから計測した 29 種類のカットテンプレート（健康食品、ファッション、サービス）を備えています。価格、電話番号、栄養成分表、法的表記は HTML 側に残します。
5. **3 段階の検証ゲート**
   - ゲート 1 `check_cuts.py` — 決定論的チェック: テンプレートのスロット上限、8 問のカバー率、**すべての数値が入力に遡れること**、カテゴリ別禁止語、法的表記ブロック、画像ファイルの存在。
   - ゲート 2 — 4 体の独立したレビュアーエージェント（疑り深いターゲット顧客、規制審査官、CRO レビュアー、競合マーケター）。合格条件は、顧客が 8 問すべてに「はい」と答え、規制違反がゼロであること。最大 2 ラウンド。
   - ゲート 3 `render_check.py` — Playwright による 390/860 px の実レンダリングと、ファーストビューの 5 秒テスト。
6. **カット画像**は `/pumasi:image` で生成 — まずアンカーカットを作り、残りは `--ref` で連鎖させます。すべてのカットについて、文字の正確さ**と**商品としての妥当性（密封パッケージ、個数、指の本数）を点検します。
7. **HTML 組み立て** — カットを隙間なく縦に積み、下に法的表記ブロックを配置。スマートストア向け 860 px / ウェブ向け 720 px。

**鉄の掟**: 入力にないものは一切創作しません — 事例、数値、レビュー、返金条件、期限のいずれも。不足している箇所は `[자료 필요: …]` プレースホルダーとして残し、レポートに一覧します。

## 対象ユーザー (이런 분을 위한 도구입니다)

- 製品を作り上げ、スペック表ではなく「売れる」詳細ページが必要になった個人創業者やバイブコーダー。
- コピー、画像、法的表記ブロックをまとめて生成し、まとめて検証したいスマートストア / Coupang / Kmong の出店者。
- 機能一覧のような商品ページを、根拠のない主張を足さずに顧客の言葉へ書き直さなければならない方。

## 動作要件 (요구사항)

- gptaku-plugins マーケットプレイスを追加した Claude Code。画像カットには `pumasi` プラグインが必要（任意 — ない場合はコピー + HTML プレースホルダーまでで停止します）
- `image_generation` を有効にしてログイン済みの Codex CLI（画像バックエンド）
- python3（ゲートと組み立てスクリプトは標準ライブラリのみ使用）
- ゲート 3 のレンダリング確認用に Node + Playwright（任意。`~/.insane-search/node/node_modules` があれば自動的に使われます）
- `bash skills/sangse/scripts/check_deps.sh --install` で上記の確認とインストールができます

## インストール

```bash
claude plugin marketplace add fivetaku/gptaku_plugins
claude plugin install sangse@gptaku-plugins
claude plugin install pumasi@gptaku-plugins     # image generation backend
codex features enable image_generation
```

インストール後は Claude Code のセッションを再起動してください。その後:

```
/sangse <product info as text, a file path, or a URL>
/sangse 카피만 …        # stop after copy approval, no images
```

あるいは「상세페이지 만들어줘」と話しかけるだけでも、スキルが自動的に起動します。

## 構成要素 (구성요소)

| パス | 役割 |
|---|---|
| `commands/sangse.md` | 単一のエントリーポイント（`/sangse`）、引数のルーティング |
| `skills/sangse/SKILL.md` | ワークフロー（Step 0 依存関係チェック → インタビュー → オファー確認 → カットシート → 3 ゲート → 画像 → HTML → レポート）、鉄の掟、レッドフラグ |
| `skills/sangse/references/` | `framework.md`（8 つの質問）、`cut-sheet.md`、`reference-patterns.md`（実ページ 7 件の解剖、29 テンプレート）、`interview.md`、`compliance.md`、`verification.md`、`evidence.md`、`image-briefs.md`、`reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`、`check_cuts.py`、`check_copy.py`、`assemble_html.py`、`render_check.py`、`capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`、`banned-words.json`、`template.html` |
| `setup/` | 初回セットアップ（gptaku 標準） |
| `examples/` | 架空の商品 3 件。成果物の全過程と `qa/` の結果を収録 |

## コンプライアンス

`references/compliance.md` には、**食品および健康機能食品**向けの詳細なフィルター（食品表示広告法第 8 条、認可された機能性表示の文言、事前審査、必須表示事項、一般食品の機能性表示ルール）と、化粧品、医療機器、金融、教育、不動産、電子機器の法令インデックスが収められています。これらのカテゴリ別フィルターは作成中です。ここに書かれた内容は法的助言ではなく、最終的な文言は該当する審査機関の判断に従います。

## リファレンスの解剖

この形式は、実際の詳細ページをヘッドフルブラウザでキャプチャし、カット単位で解剖して導き出しました。対象は Kurly、Coupang、ブランドモール（同じ健康食品を 3 チャネルで比較）、Samsung.com、LG.com、Musinsa（ファッション）、Kmong（サービス）です。発見事項、計測値、29 のテンプレートは `references/reference-patterns.md` に、キャプチャ手順とチャネル固有の落とし穴（スマートストアのログイン壁、Coupang のボットブロック）は `references/reference-capture.md` と `scripts/capture_reference.js` にまとめています。

## 変更履歴

[CHANGELOG.md](CHANGELOG.md) を参照してください。リリース手順（バージョンアップ → GitHub リリース → マーケットプレイスのサブモジュールポインタ → キャッシュ）は [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md) に従います。バージョンを上げる前に、必ず `tests/test-gates.sh` を通過させてください。

## ライセンス (라이선스)

MIT — [LICENSE](LICENSE) と [DISCLAIMER.md](DISCLAIMER.md) を参照してください。
