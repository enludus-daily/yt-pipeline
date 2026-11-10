# yt-pipeline

海外向け YouTube Shorts を作るパイプライン。自作アプリの実際の画面を自動で録り、英語のナレーションと字幕を付けて、1080×1920 の縦型動画にする。

## シリーズ

| シリーズ | 中身 | 状態 |
|---|---|---|
| **AI ships an app a day** | enludus-daily で毎日作るアプリを 1 本ずつ紹介（困りごと → AI が 1 日で作った解決策） | 準備中（アプリ側の英語対応と `-demo` 起動引数を daily-app-template の手順書に追加済み） |
| **Can you beat the bot?**（五十音マインスイーパー） | 英語 A〜Z 盤でボットと対戦。止めて「Pause & guess!」→ 答え | 試作できた（`gojuon/`） |

## 構成

```
gojuon/record.js      Web 版をブラウザで自動操作し、乱数を固定したボット対戦を 1080x1920 で録る（frames/ と times.json）
common/frames_to_video.py  録った frames を 30fps の mp4 にする
common/tts.sh         英語のナレーション（Piper、en_US-ryan-high。初回に声のモデルをダウンロード）
gojuon/compose.py     つかみ → プレイ → 一時停止（Pause & guess! → 3・2・1 の声と音）→ 答え → アプリの紹介、をゲームの BGM 付きで合成
gojuon/make_short.sh  上をまとめて 1 本作る
assets/gojuon-sounds/ アプリの BGM・効果音（アプリの scripts/sounds/make_sounds.py で一から合成したもの。権利の問題なし）
examples/             投稿用のタイトル・説明文・タグの例
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
   CLUE="7 letters · a condiment" CLUES=3 GAME_LINE="Seven letters. A condiment. Can you beat it?" \
     gojuon/make_short.sh 14 KETCHUP 3.5 10.7 13.4
   ```

   - `G0`（3.5）：盤面が出た時刻。`record.js` の `MARK board` の少しあと
   - `GF`（10.7）：ボットが最後に考えている場面（答えが出る直前）。止めてカウントダウンを出す
   - `R1`（13.4）：結果の画面の終わり
   - 時刻は `MARK` の行を見て決め、`work/out/` のコマ（`ffmpeg -ss <秒> -i work/rec.mp4 -frames:v 1 x.png`）で確かめる

3. `output/` の mp4 と、`examples/` に倣ったタイトル・説明文で投稿する。

## 投稿

- YouTube Data API の審査（audit）が通るまで、API で上げた動画は非公開に固定され、公開に切り替えられない。それまでは **YouTube Studio から手で上げる**。
- 合成音声は自分の台本を読んでいるだけで、実在の人物を模したものではない。実際のゲーム画面なので「改変または合成されたコンテンツ」の申告は不要（現実と見分けがつかない人物・出来事を作った場合だけ必要）。
- 同じ型の量産は YouTube の inauthentic content に当たりやすい。お題・つかみの文・見せ方を毎回変える。
