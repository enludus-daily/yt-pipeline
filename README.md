# yt-pipeline

海外向け YouTube Shorts を作るパイプライン。自作アプリの実際の画面を自動で録り、英語のナレーションと字幕を付けて、1080×1920 の縦型動画にする。

## シリーズ

| シリーズ | 中身 | 状態 |
|---|---|---|
| **AI ships an app a day** | enludus-daily で毎日作るアプリを 1 本ずつ紹介（困りごと → AI が 1 日で作った解決策） | 合成できる（`daily/`）。2026-11-10 夜のアプリから、CI がデモを録る |
| **Can you beat the bot?**（五十音マインスイーパー） | 英語 A〜Z 盤でボットと対戦。止めて「Pause & guess!」→ 答え | 試作できた（`gojuon/`） |

## 構成

```
gojuon/record.js      Web 版をブラウザで自動操作し、乱数を固定したボット対戦を 1080x1920 で録る（frames/ と times.json）
common/frames_to_video.py  録った frames を 30fps の mp4 にする
common/tts.sh         英語のナレーション（Piper、en_US-ryan-high。初回に声のモデルをダウンロード）
gojuon/compose.py     つかみ → プレイ → 一時停止（Pause & guess! → 3・2・1 の声と音）→ 答え → アプリの紹介、をゲームの BGM 付きで合成
gojuon/make_short.sh  上をまとめて 1 本作る
assets/gojuon-sounds/ アプリの BGM・効果音（アプリの scripts/sounds/make_sounds.py で一から合成したもの。権利の問題なし）
common/upload.py      YouTube Data API でアップロード（--auth で最初のサインイン、--dry-run で中身の確認）
examples/             投稿用のメタデータの例（.json は upload.py が読む）
docs/youtube-api-audit.md  API の審査の手順・Cloud Console のリンク・フォームの答えの下書き
```

画像生成（タイトルカード・サムネイル）は自宅 PC の Codex CLI で行う予定（ChatGPT のサブスクのログインを保つため）。

## 準備

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

五十音マインスイーパーの英語版 Web を `/en/` の下で配信する（ビルドは `/en/` を前提にしている）：

```bash
cd ../gojuon-minesweeper && npm ci && EXPO_PUBLIC_LOCALE=en npx expo export -p web --output-dir dist-en
mkdir -p /tmp/webroot && ln -sfn "$PWD/dist-en" /tmp/webroot/en && npx serve /tmp/webroot -l 8082 --symlinks
```

Playwright と Chromium が要る（クラウドのセッションには入っている）。

## 1 本作る

1. お題を探す：同じ seed なら同じお題・同じ展開になる。

   ```bash
   cd work && node ../gojuon/record.js 14
   ```

   最後に `Answer: ketchup` などが出る。面白いお題の seed を選ぶ（例：14 ketchup / 11 dread / 13 games / 15 survey）。

2. 録って合成する：

   ```bash
   gojuon/make_short.sh 14            # → output/gojuon-14-ketchup.mp4
   CLUES=3 gojuon/make_short.sh 14    # つかみを "from just 3 clues" にする（開いていたマスの数が分かるとき）
   ```

   - 答え・文字数・ジャンル（例：`7 letters · Condiments`）は対戦の結果から読む。ボットが勝たなかった seed は止まる
   - 時刻は録画中に自動で決める：`G0` = 盤面が出た時刻 + 0.2、`GF`（一時停止）= 決着の 0.45 秒前（ボットが最後に考えている場面）、`R1` = 決着 + 2.3
   - 決着の時刻は、ページの中の MutationObserver が「got it!」が出た瞬間を記録する（`MARK over_exact`）
   - 必ず `work/out/freeze.png` を開き、**答えが映っていない**ことを確かめる
   - 時刻を手で決めるとき：`gojuon/make_short.sh 14 3.5 10.4 13.2`

3. `output/` の mp4 と、`examples/*.json` に倣ったメタデータで投稿する：

   ```bash
   .venv/bin/python common/upload.py output/gojuon-14-ketchup.mp4 examples/gojuon-14-ketchup.json
   ```

## AI ships an app a day（`daily/`）

毎日のアプリは、CI（daily-actions の ios-ci、`demo-video: en`）が起動引数 `-demo` の再生を英語で録画し、artifact `demo-video` に置く（daily-app-template が 2026-11-10 から有効）。

```bash
daily/fetch_demo.sh app-20261111-xxxx        # → work/daily/<repo>/demo.mp4・icon.png・README.md（gh のサインインが要る）
common/tts.sh work/vo-d/hook.wav  "Snake, but your body is the billiard cushion."
common/tts.sh work/vo-d/demo.wav  "Day 24. An AI built this iPhone game in one day."
common/tts.sh work/vo-d/outro.wav "Follow along for tomorrow's app."
DAY=24 NAME="Rolling Snake" HOOK="Snake, but your body is the billiard cushion." TAGLINE="A physics puzzle for iPhone" \
  VO=work/vo-d .venv/bin/python daily/compose.py work/daily/<repo>/demo.mp4 work/daily/<repo>/icon.png work/daily-out
```

シリーズの日付は `daily/series.json`（Day 1 = タマヘビ、そのあとの毎日のアプリが Day 2, 3, …）。

構成：つかみ（DAY N と、困りごと／組み合わせの 1 行）3 秒 → デモ（上に「Day N: 名前」「Built by AI in ~1 day」）→ アプリの紹介（アイコン・名前・ストア・「Day N+1 は明日」）3 秒。HOOK・TAGLINE はアプリごとに README と daily-ideas の Issue から英語で書く（同じ文の使い回しをしない）。

## 見た目のきまり（2026-11-11 本人の指摘：「五十音マインスイーパーに引っ張られすぎ」）

- 動画の背景・色・音楽は、**そのアプリ自身のもの**から作る。ほかのアプリの絵（`assets/gojuon-art/`）や BGM（`assets/gojuon-sounds/`）は、五十音マインスイーパーの動画だけに使う
- 既定：背景はそのアプリの録画をぼかしたもの、アクセントの色はアイコンのいちばん鮮やかな色（`common/look.py`）、音楽はアプリごとに `common/bgm.py` で一から合成する。**毎回ちがう曲にする**（2026-11-11 本人：「似てるから、毎回ちゃんと作って」）：`python common/bgm.py new <app>` で、直近 5 本のアプリが使っていないジャンル（lofi・chiptune・bossa・synthwave・folk・ambient・funk・waltz）を選び、アプリ名から決まる種でテンポ・調・音階・コード進行・メロディを変える。曲は イントロ → A → B（メロディが上がる）→ A → B。`apps/<app>/bgm.m4a` と `bgm.json`（ジャンル・テンポ・調）を書く。アプリの雰囲気に合うジャンルを `--genre` で選んでよい。作った BGM はそのアプリのリポジトリの `docs/promo/bgm.m4a` にも置く。アプリに自前の BGM があればそれを使う（StudyReel・五十音マインスイーパー）
- チャンネルのバナーとアイコンは Enludus のロゴの色（紺・水色・オレンジ）

## 公開の時刻（2026-11-11 本人：「アメリカの日中に、夜中じゃなく」）

- `python publish/schedule.py` で、待ち行列の動画に公開日時を入れてから `publish/upload_queue.py` で上げる（YouTube が時刻に自分で公開する）
- 枠（米国東部時間。夏時間は自動）：**12:00 ET** は「AI ships an app a day」（`day<N>-*`）、**16:00 ET** はそれ以外。1 日 1 枠 1 本
- 冬時間では 12:00 ET = 9:00 PT = 日本時間の翌 2:00、16:00 ET = 13:00 PT = 翌 6:00
- 使った枠は `publish/scheduled.json`（Studio で手で予約したものも書いておく）

## 投稿

- 2026-11-11 に YouTube から返事：**API で上げた動画が自動で非公開になることはない**（ネットの「審査まで非公開に固定」は古い情報）。審査の申請は「割り当てを増やす必要がないので」閉じられた。→ `privacyStatus: public` でそのまま公開、または `private` + `publishAt` で予約できる。
- 手順と申請の下書きは `docs/youtube-api-audit.md`。
- 合成音声は自分の台本を読んでいるだけで、実在の人物を模したものではない。実際のゲーム画面なので「改変または合成されたコンテンツ」の申告は不要（現実と見分けがつかない人物・出来事を作った場合だけ必要）。
- 同じ型の量産は YouTube の inauthentic content に当たりやすい。お題・つかみの文・見せ方を毎回変える。
