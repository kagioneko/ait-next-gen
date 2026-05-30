# AIT-Next-Gen: Cognitive Assembly Lab

AIT (AI Instruction Tape) と CPOS (Context Pointer OS) の思想を発展させた実験的プロジェクト。  
LLMを「テキスト生成器」ではなく「認知スタックマシンの CPU」として駆動することを目指す。

---

## 収録モジュール

### `toa/` — TOA (Tape-Oriented Assembly) v0.2

LLMにプロンプトを読ませずに、**4文字パケットのテープで直接命令する**スタックマシン。

```
s4x9   ; Security domain / ctx#4 / action:xss / priority:9
v0c5   ; Validate domain / ctx#0 / action:check / priority:5
?b02   ; JIF: スタックtop==0 なら +2 スキップ
def:[d:n:neuro]  ; SED-Tape: 辞書に 'n=neuro' ドメインを追加
```

#### パケット構造

| 位置 | 意味 | 値の例 |
|------|------|--------|
| 1文字目 | ドメイン | `s`=security, `m`=memory, `n`=neural, `v`=validate, `a`=agent, `g`=genetic |
| 2文字目 | ctx番号 (hex) | `0`〜`f` → #0〜#15 |
| 3文字目 | アクション | `x`=xss, `f`=fix, `r`=read, `w`=write, `c`=check, `e`=emit |
| 4文字目 | 優先度 | `0`〜`9` |

#### 特殊オペコード

| パケット | オペコード | 動作 |
|---------|-----------|------|
| `?bNN` | JIF | スタックtop==0 なら +NN パケット先へジャンプ |
| `!NNN` | JMP | 無条件 +NNN ジャンプ |
| `##NN` | CTX_LOAD | #NN をアクティブコンテキストにセット |
| `>>NN` | CTX_PUSH | スタックtop を #NN へ保存 |
| `def:[d:X:name]` | DEF | 辞書にドメイン `X` を動的追加 (SED-Tape) |
| `def:[a:X:name]` | DEF | 辞書にアクション `X` を動的追加 (SED-Tape) |

#### クイックスタート

```bash
# REPL 起動
python -m toa

# テープファイル実行
python -m toa
> file toa/demo.tape
```

#### バックエンド設定

環境変数 `TOA_BACKEND` で LLM バックエンドを選択できる。

| 値 | 動作 | 必要なもの |
|----|------|-----------|
| `claude_cli` | `claude` CLI をサブプロセスで実行（デフォルト） | Claude Code インストール済み |
| `anthropic_api` | Anthropic SDK を直接呼び出す | `ANTHROPIC_API_KEY` 環境変数 |
| `mock` | LLM なしのオフラインモック | なし |

```bash
# Claude CLI バックエンド（デフォルト）
python -m toa

# Anthropic API バックエンド
export ANTHROPIC_API_KEY=sk-ant-...   # Vault から取得すること
TOA_BACKEND=anthropic_api python -m toa

# オフラインモック
TOA_BACKEND=mock python -m toa
```

> **注意**: `ANTHROPIC_API_KEY` はコードやファイルにハードコードしないこと。  
> 環境変数または Vault (`vault kv get -field=api_key secret/anthropic`) から取得する。

---

### `ait_eval.py` — AIT-Lisp Evaluator v0.1

AIT テープを S 式として評価する Lisp スタイルの評価器。  
Unison 流のコンテンツハッシュアドレッシング + Koka 流の代数的エフェクトを実験的に実装。

---

## ロードマップ

- [x] TOA v0.2 コア（パーサー / スタックマシン / SED-Tape）
- [x] Claude CLI バックエンド
- [x] Anthropic API バックエンド
- [ ] CPL (Context-Pointer Language) — グラフ層
- [ ] CPOS `ContextStore` との統合
- [ ] AIT-Lisp → TOA トランスパイラ

---

## 関連プロジェクト

- [ai-instruction-tape](https://github.com/kagioneko/ai-instruction-tape) — AIT コア仕様
- [context-pointer-os](https://github.com/kagioneko/context-pointer-os) — CPOS カーネル
