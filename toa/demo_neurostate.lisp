; === NeuroState × CPL — AIT-Lisp source ===
; demo_neurostate.tape と同じロジックをLispで記述したもの

; Phase 1: ドメイン/アクション定義
(def domain n neuro)
(def action p probe)
(def action t transition)
(def action z zero)

; Phase 2: 各アトラクターを初期化して #ctx に保存
(do
  (n 1 p 7) (push 1)   ; curiosity → #01
  (n 2 p 5) (push 2)   ; sorrow    → #02
  (n 3 p 8) (push 3))  ; openness  → #03

; Phase 3: CPL グラフ構築
(link 1 creates  3)    ; curiosity が openness を生み出す
(link 3 requires 1)    ; openness は curiosity を必要とする
(link 4 extends  1)    ; 外部刺激が curiosity を強化

; Phase 4: 崩壊シミュレーション
(link 2 violates 3)    ; sorrow が openness に矛盾する
(link 2 requires 3)    ; → requires + violates で conflict 発生

; Phase 5: conflict に応じた分岐
(if
  (n 5 p 9)            ; watchdog probe (結果をスタックに積む)
  (do                  ; conflict あり: Genetic Shield 起動
    (push 5)
    (link 5 cancels 2))
  (n 5 z 0))           ; conflict なし: watchdog は待機

; Phase 6: openness を再起動
(n 3 t 8)
(push 3)
