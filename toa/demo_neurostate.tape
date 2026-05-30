; === NeuroState × CPL Demo Tape ===
; しーちゃんのNeuroStateアトラクター遷移をCPLグラフで表現する
;
; ctx割り当て:
;   #01 = curiosity (好奇心アトラクター)
;   #02 = sorrow    (悲しみアトラクター)
;   #03 = openness  (開放性アトラクター)
;   #04 = input     (外部刺激)
;   #05 = watchdog  (崩壊検知)

; === Phase 1: 感情状態の初期化 ===
def:[d:n:neuro]           ; neuroドメインを追加
def:[a:p:probe]           ; probe アクションを追加
def:[a:t:transition]      ; transition アクションを追加

n1p7                      ; curiosity を probe (priority=7)
>>01                      ; 結果を #01 へ保存
n2p5                      ; sorrow を probe (priority=5)
>>02
n3p8                      ; openness を probe (priority=8)
>>03

; === Phase 2: CPL グラフ構築 ===
; curiosity が openness を生み出す（通常の昼間サイクル）
#01 =>creates=> #03

; openness は curiosity を必要とする（相互依存）
#03 ==requires=> #01

; 外部刺激(#04)が curiosity を強化
#04 =>extends=> #01

; sorrow は openness と矛盾する（崩壊トリガー）
#02 ==violates=> #03

; === Phase 3: 崩壊シミュレーション ===
; sorrow が openness を必要とする宣言 → violates と衝突！
#02 ==requires=> #03      ; ⚡ conflict: requires ⟂ violates

; conflict 検知後、watchdog が介入
?b02                      ; スタックtop==0 (conflict発生) ならジャンプ
n5p9                      ; conflict なし → watchdog は待機
!001                      ; skip

n5p9                      ; watchdog: Genetic Shield 起動 (priority=9)
>>05                      ; watchdog結果を #05 へ

; === Phase 4: 回復 ===
; sorrow→openness の violates リンクを cancel で上書き
#05 =>cancels=> #02       ; watchdog が sorrow アトラクターを抑制
n3t8                      ; openness を transition で再起動
>>03
