# AIT-Next-Gen: Cognitive Assembly Lab

LLMを「テキスト生成器」ではなく **「認知スタックマシンのCPU」** として駆動する実験的プロジェクト。  
自然言語プロンプトを一切使わず、4文字パケットのテープで直接命令する。

---

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: AIT-Lisp  (.lisp)                                     │
│                                                                 │
│  (if (s 4 x 9)          ← S式で書く。人間が読める。            │
│    (do (s 4 f 7)                                                │
│        (link 4 creates 9))                                      │
│    (n 5 p 9))                                                   │
└───────────────────┬─────────────────────────────────────────────┘
                    │  python -m toa.transpiler
                    │  compile_program()
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: TOA Tape  (.tape)                                     │
│                                                                 │
│  s4x9                    ← 4文字パケット。プロンプト不要。      │
│  ?b02                      LLMには「このテープを実行せよ」      │
│  s4f7                      という極小命令を1つ渡すだけ。        │
│  #04 =>creates=> #09                                            │
│  !001                                                           │
│  n5p9                                                           │
└───────────────────┬─────────────────────────────────────────────┘
                    │  TOAMachine.run()
                    │  + MachineHooks
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Stack Machine + CPL Graph                             │
│                                                                 │
│  stack: [1, 0, 1, ...]   ctx: {#4: ..., #9: ...}               │
│                                                                 │
│  CPL Graph:                                                     │
│    #01 ==creates==> #03   ← typed edges between #ctx registers  │
│    #03 ==requires==> #01    conflict検知・cycle検出・            │
│    #02 ==violates==> #03 ⚡  watchdog自動発火                   │
└───────────────────┬─────────────────────────────────────────────┘
                    │  CPOSBridge (MachineHooks)
                    │  optional — PYTHONPATH設定で有効化
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: CPOS ContextStore  (context-pointer-os)               │
│                                                                 │
│  toa:01  status=active       trust=1.00  data=...               │
│  toa:02  status=invalidated  trust=0.90  data=...  ← violates   │
│  toa:03  status=active       trust=1.00  deps=[toa:01]          │
│                                                                 │
│  TOAのCPLエッジが自動でCPOSのセマンティクスに反映される:        │
│    creates  → parent設定          requires → dependencies追加   │
│    violates → invalidate()        cancels  → status復元         │
│    conflict → watchdog auto-invalidate                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## LLM バックエンド

| `TOA_BACKEND` | 動作 | 必要なもの |
|---------------|------|-----------|
| `claude_cli` | `claude` CLI をサブプロセスで実行（**デフォルト**） | Claude Code インストール済み |
| `anthropic_api` | Anthropic SDK を直接呼び出す | `ANTHROPIC_API_KEY` 環境変数 |
| `mock` | LLM なしのオフラインモック | なし |

> **認証情報について**: `ANTHROPIC_API_KEY` はコードにハードコードしないこと。  
> 環境変数または Vault (`vault kv get -field=api_key secret/anthropic`) から取得する。

---

## クイックスタート

### 1. REPL を起動する

```bash
python -m toa
```

```
╔══════════════════════════════════════════════════╗
║  TOA v0.2  ·  Tape-Oriented Assembly for LLMs   ║
╚══════════════════════════════════════════════════╝
> s4x9
[IP:000] EXEC  domain=s ctx=#4 action=x priority=9
  → XSS scan on ctx #4: no payload present, surface is clean at priority 9.
[DONE] ip=1  stack=[1]

> graph
  (no edges)
> #01 =>creates=> #03
  → graph: #01 ==creates==> #03
> graph
  #01 ==creates==> #03
  nodes=2 edges=1
```

### 2. テープファイルを実行する

```bash
# モックバックエンド（LLM不要）
TOA_BACKEND=mock python -m toa
> file toa/demo_neurostate.tape

# Claude CLI バックエンド（デフォルト）
python -m toa
> file toa/demo_neurostate.tape
```

### 3. AIT-Lisp をコンパイルして実行する

```bash
# コンパイルのみ（テープを stdout に出力）
python -m toa.transpiler toa/demo_neurostate.lisp

# コンパイル → 即時実行
python -m toa.transpiler toa/demo_neurostate.lisp --run

# バックエンド指定
python -m toa.transpiler toa/demo_neurostate.lisp --run --backend mock

# ファイルに保存
python -m toa.transpiler toa/demo_neurostate.lisp -o out.tape
```

### 4. CPOS ContextStore と統合する

```bash
PYTHONPATH=/path/to/context-pointer-os/src python3 - <<'EOF'
from toa import TOAMachine
from toa.bridge import CPOSBridge
from toa.transpiler import compile_program

bridge = CPOSBridge(verbose=True)
machine = TOAMachine(hooks=bridge)
tape = compile_program(open("toa/demo_neurostate.lisp").read())
machine.run(tape)

print(bridge.dump())
EOF
```

---

## デモ: AIT-Lisp → TOA → Claude 実行

```bash
python -m toa.transpiler toa/demo_neurostate.lisp --run
```

### Step 1: AIT-Lisp ソース（抜粋）

```lisp
; NeuroStateアトラクター遷移をCPLグラフで表現する
(def domain n neuro)
(def action p probe)

(do
  (n 1 p 7) (push 1)   ; curiosity → #01
  (n 2 p 5) (push 2)   ; sorrow    → #02
  (n 3 p 8) (push 3))  ; openness  → #03

(link 1 creates  3)    ; curiosity が openness を生み出す
(link 2 violates 3)    ; sorrow が openness に矛盾する
(link 2 requires 3)    ; → requires + violates で conflict 発生

(if (n 5 p 9)          ; watchdog probe
  (do (push 5) (link 5 cancels 2))   ; conflict → Genetic Shield 起動
  (n 5 z 0))                         ; no conflict → 待機
```

### Step 2: コンパイル済み TOA テープ

```
def:[d:n:neuro]    def:[a:p:probe]    ...
n1p7    >>01       n2p5    >>02       n3p8    >>03
#01 =>creates=> #03
#02 ==violates=> #03
#02 ==requires=> #03    ← conflict trigger
n5p9
?b03                    ← JIF: watchdog 結果で分岐
>>05
#05 ==cancels=> #02
!001
n5z0
```

### Step 3: Claude が TOA を実行した出力

```
[IP:004] EXEC  domain=n ctx=#1 action=p priority=7
  → Neuro probe on register #1 returned an active signal at 87% strength.

[IP:013] LINK  #02 ==violates==> #03
  → graph: #02 ==violates==> #03

[IP:014] LINK  #02 ==requires==> #03
  → graph: #02 ==requires==> #03
  ⚡ [CONFLICT] #02 ==requires==> #03  ×  #02 ==violates==> #03  (requires ⟂ violates)

[IP:015] EXEC  domain=n ctx=#5 action=p priority=9
  → Register #5 probed at maximum priority — neuro domain reports active
    associative node with 3 deep links and near-peak signal strength.

[IP:016] JIF   +3          ← watchdog 成功 → then 節へ進む
[IP:017] CTX_PUSH  #5
[IP:018] LINK  #05 ==cancels==> #02
  → graph: #05 ==cancels==> #02    ← Genetic Shield 発動

[IP:021] EXEC  domain=n ctx=#3 action=t priority=8
  → Context register #3 successfully transitioned to active state
    with high-priority neuro signal at transition vector 1.

FINAL: stack=[1, 1, 1, 1, 0, 0]
```

**Claude は「プロンプトを読んで回答する」のではなく、  
4文字命令を左から右に処理する CPU として動作している。**

---

## パケット仕様

### EXEC パケット（4文字）

```
s  4  x  9
│  │  │  └─ priority   0-9
│  │  └──── action     (辞書参照)
│  └─────── ctx id     0-9, a-f → #0 〜 #15
└────────── domain     (辞書参照)
```

デフォルト辞書:

| 記号 | ドメイン | 記号 | アクション |
|------|---------|------|-----------|
| `s` | security | `x` | xss |
| `m` | memory | `i` | inject |
| `n` | neural | `f` | fix |
| `v` | validate | `r` | read |
| `a` | agent | `w` | write |
| `g` | genetic | `c` | check |
| `c` | core | `e` | emit |
| | | `k` | kill |
| | | `z` | zero |

### 特殊オペコード

| パケット | オペコード | 動作 |
|---------|-----------|------|
| `?bNN` | JIF | スタック top == 0 なら +NN パケット先へジャンプ |
| `!NNN` | JMP | 無条件 +NNN ジャンプ |
| `##NN` | CTX_LOAD | #NN をアクティブコンテキストにセット |
| `>>NN` | CTX_PUSH | スタック top を #NN へ保存 |
| `def:[d:X:name]` | DEF | ドメイン `X` を動的追加 (SED-Tape) |
| `def:[a:X:name]` | DEF | アクション `X` を動的追加 (SED-Tape) |

### CPL リンク構文（行全体）

```
#01 =>creates=> #03     # 生成・継承系
#03 ==requires=> #01    # 依存・状態系
#02 ==violates=> #03    # 矛盾 → 即時 conflict 検知 ⚡
#05 ==cancels=> #02     # 無効化の取り消し
```

矛盾ペア: `requires ⟂ violates`, `creates ⟂ cancels`

### AIT-Lisp 構文

```lisp
(s 4 x 9)                   ; → s4x9  (EXEC)
(load 4)                     ; → ##04  (CTX_LOAD)
(push 4)                     ; → >>04  (CTX_PUSH)
(link 1 creates 3)           ; → #01 =>creates=> #03
(link 2 violates 3)          ; → #02 ==violates=> #03
(def domain n neuro)         ; → def:[d:n:neuro]
(def action f fix)           ; → def:[a:f:fix]
(do e1 e2 ...)               ; 順次実行
(if cond then)               ; 条件分岐（JIF オフセット自動計算）
(if cond then else)          ; then/else 分岐
(repeat 3 (s 4 x 9))        ; コンパイル時ループ展開
```

---

## ファイル構成

```
ait-next-gen/
├── ait_eval.py              # AIT-Lisp 評価器 v0.1（コンテンツハッシュ + 代数的エフェクト）
└── toa/
    ├── dictionary.py        # ドメイン/アクション辞書（SED-Tape 動的拡張対応）
    ├── packet.py            # 4文字パーサー + CPL リンク行パーサー
    ├── machine.py           # スタックマシン + MachineHooks インターフェース
    ├── graph.py             # CPL GraphStore（矛盾検知・サイクル検出）
    ├── runtime.py           # LLM バックエンド選択（claude_cli / anthropic_api / mock）
    ├── transpiler.py        # AIT-Lisp → TOA テープ コンパイラ
    ├── __main__.py          # REPL
    ├── demo.tape            # 基本デモテープ
    ├── demo_neurostate.tape # NeuroState × CPL デモテープ
    ├── demo_neurostate.lisp # 同デモの AIT-Lisp ソース
    └── bridge/
        ├── __init__.py
        └── cpos_bridge.py   # CPOS ContextStore アダプター（MachineHooks 実装）
```

---

## 関連プロジェクト

- [ai-instruction-tape](https://github.com/kagioneko/ai-instruction-tape) — AIT コア仕様
- [context-pointer-os](https://github.com/kagioneko/context-pointer-os) — CPOS カーネル
