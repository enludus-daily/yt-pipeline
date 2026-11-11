# YouTube Data API の審査（audit）の申請メモ

2026-11-11 に YouTube から返事：**API で上げた動画が自動で非公開になることはない**（ネットの「審査まで非公開に固定」は古い情報）。審査の申請は「割り当てを増やす必要がないので」閉じられた。→ `privacyStatus: public` でそのまま公開、または `private` + `publishAt` で予約できる。

## 1. Google Cloud の準備（本人）

| すること | リンク |
|---|---|
| プロジェクトを作る（名前の例：`enludus-shorts-publisher`） | https://console.cloud.google.com/projectcreate |
| YouTube Data API v3 を有効にする | https://console.cloud.google.com/apis/library/youtube.googleapis.com |
| OAuth 同意画面（Google Auth Platform）を作る：種類「外部」、アプリ名「Enludus Shorts Publisher」、サポートのメール、ホームページ `https://enludus.com`、プライバシーポリシー `https://enludus.com/products/shorts-publisher-privacy`、利用規約 `https://enludus.com/products/shorts-publisher-terms`、スコープ `.../auth/youtube.upload` | https://console.cloud.google.com/auth/overview |
| 公開ステータスを「本番」にする（「テスト」のままだとトークンが 7 日で切れる。自分だけで使うので「未確認のアプリ」の警告は出たまま使ってよい） | https://console.cloud.google.com/auth/audience |
| OAuth クライアント ID を作る：種類「デスクトップ アプリ」→ JSON をダウンロードし、`.cache/client_secret.json` に置く（コミットしない） | https://console.cloud.google.com/auth/clients |
| 割り当て（quota）を確かめる：videos.insert の 1 回の消費と 1 日の上限 | https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas |
| 審査のフォーム | https://support.google.com/youtube/contact/yt_api_form |

プロジェクト番号は、Cloud Console のダッシュボード（https://console.cloud.google.com/home/dashboard ）に出る。フォームで聞かれる。

## 2. 最初のサインイン

```bash
python common/upload.py --auth                # ブラウザのある PC
python common/upload.py --auth --no-browser   # ブラウザのないマシン（URL を開いて、最後のアドレスを貼る）
```

チャンネルを持っている Google アカウントで許可する。`.cache/youtube-token.json` ができる。

## 3. 審査のフォームの答え（下書き）

フォームは英語で書く。「」の中はそのまま貼れる。会社名・住所など、ここにない個人の情報は本人が入れる。

**Organization / developer**
- Organization name: 「Enludus (sole proprietorship of Ibuki Nagase)」
- Website: 「https://enludus.com」
- Contact email: 「contact@enludus.com」

**API client**
- Name: 「Enludus Shorts Publisher」
- Type: 「Internal command-line tool (not offered to the public)」
- Google Cloud project number: （本人が入れる）
- Privacy policy: 「https://enludus.com/products/shorts-publisher-privacy」
- Terms of service: 「https://enludus.com/products/shorts-publisher-terms」

**How the API is used**

「Enludus is a one-person studio that makes iPhone apps and games. Enludus Shorts Publisher is an internal command-line tool that uploads short vertical videos about our own apps to our own YouTube channel. Each video is made by us: real gameplay or screen recordings of our apps, music and sound effects we synthesized ourselves, and narration generated from scripts we write. The tool only calls videos.insert with the youtube.upload scope, to upload one video with its title, description, tags, category, and privacy settings, and it reads back the video ID and upload status. It does not read, store, or display any data about other channels or viewers. Only Enludus signs in, with the Google account that owns our channel. OAuth tokens stay on the computer that runs the tool. We are applying for the audit so that videos uploaded by the tool are not locked to private.」

**Endpoints and scopes**
- 「videos.insert (part=snippet,status) — scope https://www.googleapis.com/auth/youtube.upload」

**Users**
- Number of users: 「1 (Enludus only)」
- Channels: 「1 (our own channel)」

**Expected usage**
- 「About 1–3 uploads per day. We do not need more quota than the default.」

**Data handling**
- 「No YouTube data is stored except the video ID and upload status of our own uploads, in a local log. Tokens are stored locally and can be revoked at https://myaccount.google.com/permissions. We do not share any data with third parties.」

**Screencast / demo**（求められたら）
- ツールのサインインからアップロードまでを画面録画する：`--auth` → `--dry-run` で中身を見せる → 本番のアップロード → YouTube Studio で動画を見せる。

## 4. 通ったあと

- 審査より前に API で上げた動画は、Studio で手で公開に切り替える（2026-11-11 に切り替えられた）。
- `privacyStatus` を `public` にするか、`publishAt` で公開日時を予約する。
