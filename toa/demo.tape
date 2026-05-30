; === TOA Demo Tape v0.2 ===
; Scenario: 入力データ(#4)のXSSチェック → 問題あれば修正 → 結果を#9に保存

##04          ; #4をアクティブコンテキストにセット
s4x9          ; Security domain: ctx#4 に XSSチェック (priority=9)
?b02          ; スタックtop==0(失敗)なら2パケット先へジャンプ
s4f7          ; XSS検出 → fix実行 (priority=7)
>>09          ; 結果を#9へPUSH

; === SED-Tape デモ: 辞書を動的に拡張 ===
def:[d:n:neuro]   ; 新ドメイン n=neuro を追加
def:[a:f:fix]     ; action f=fix を追加（既存上書き確認）
n4f5              ; neuroドメインで fix (priority=5) を実行
