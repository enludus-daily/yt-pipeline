# アプリごとの BGM を Audio Studio MCP で作る（2026-11-20 から）

本人の判断（2026-11-20）：BGM は、自宅の Mac（M2・8GB、`m4-studio.local`、画面は割れていて SSH で使う）で Audio Studio MCP（Stable Audio 3、ローカル生成、API キー不要）を使って作り、**自動で**回す。クラウドのセッションは、Mac の Remote Control のセッションに「Day N の BGM を作って」と頼む。

- 試した結果：medium モデルで 30 秒の曲が 17 秒でできた（8GB でも足りる）
- `common/bgm.py`（自前の合成）は、Mac が使えないときの予備として残す

## Mac の準備（1 回だけ、本人が SSH で行う）

1. `brew install uv ffmpeg tmux gh`
2. `uvx --python 3.11 audio-studio-mcp setup`（モデル約 6 GB。切れても止まらないよう `nohup caffeinate -i sh -c 'yes | uvx --python 3.11 audio-studio-mcp setup' > ~/audio-setup.log 2>&1 &`）
3. Claude Code：`curl -fsSL https://claude.ai/install.sh | bash`、`claude mcp add --scope user audio-studio -- uvx --python 3.11 audio-studio-mcp`、`claude` でサインイン
4. GitHub：`gh auth login`（本人がブラウザで）→ `gh repo clone enludus-daily/yt-pipeline ~/src/yt-pipeline`
5. Remote Control を tmux の中で動かす（SSH が切れても残る）：
   `tmux new -d -s rc 'cd ~/src/yt-pipeline && caffeinate -i claude remote-control'`
   見るとき `tmux attach -t rc`（抜けるとき `Ctrl+b` → `d`）
6. スリープ止め：`sudo pmset -a sleep 0 disablesleep 1`（設定済み）

再起動したあとは、ログインしてから 5 をもう一度実行する（画面が映らないので、ログインのパスワードは見えないまま打つ）。

## 1 曲作る手順（Mac のセッションが行う）

1. `git pull`。そのアプリの README（だれの・どう使う・デモの流れ）を読む。クラウドから英文の指示が来ていればそれを使う
2. 英語の説明を 1〜2 文で書く：ジャンル・主な楽器・リズム・雰囲気。**直近 5 本の `apps/*/bgm.json` の `prompt`／`genre` とジャンル・主な楽器が重ならないようにする**（2026-11-11 本人：「似てるから、毎回ちゃんと作って」）。歌・歌詞は作れない
3. `generate_audio`：音楽、40 秒、2 バージョン。2 つを聴き比べられないので、`process_audio` の情報（音量・無音）で破綻していない方を選ぶ
4. `python3 common/bgm_import.py <app> <選んだ wav> --prompt "<英文>" --seed <seed>` → `apps/<app>/bgm.m4a` と `bgm.json`
5. commit して `git push origin HEAD:main`。クラウドに「apps/<app>/bgm.m4a を push した」と返す
6. 生成物は `~/AudioStudio` に残る。容量が増えたら古いものを消してよい

`apps/<app>` の名前は、リポジトリ名から日付を除いたもの（例：`app-20261117-reversi-delve` → `reversi-delve`）。

## ライセンスと説明文

- コードは MIT。モデルの重みは Stability AI Community License：年間の総収入が 100 万ドル未満なら商用利用できる（YouTube の収益化・アプリへの同梱を含む）。超えそうになったら見直す
- Stable Audio の曲を使った動画の説明文は「The music in this video was generated for this channel with Stable Audio.」と書く（「made from scratch」とは書かない）
