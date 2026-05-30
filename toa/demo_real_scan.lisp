; === Real Data Security Scanner ===
; #01 = 検査対象コード（外部から注入）
; #02 = XSSスキャン結果
; #03 = SQLiスキャン結果
; #04 = 修正後コード
; #09 = 最終判定レジスタ

; Phase 1: XSS チェック
(s 1 x 9)        ; #01のコードにXSSスキャン（priority=9）
(push 2)         ; 結果を #02 へ

(if (v 2 c 8)
  (do
    (s 1 f 9)    ; XSS検出 → 自動修正
    (push 4))    ; 修正後コードを #04 へ
  (push 1))      ; クリーン → #01 をそのまま使う

; Phase 2: SQLi チェック
(s 1 i 9)        ; #01のコードにSQLiスキャン
(push 3)

(if (v 3 c 8)
  (do
    (s 1 f 8)    ; SQLi検出 → 自動修正
    (push 4))
  (push 1))

; Phase 3: 最終バリデーション
(v 1 c 9)        ; 修正済みコードを最終チェック
(push 9)
