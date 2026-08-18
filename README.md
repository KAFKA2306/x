# X archive analyzer

自分のXデータアーカイブをローカルのFastAPIアプリで読み込み、投稿・いいね・フォロー関係・交流履歴を集計するツールです。

X公式は、データアーカイブにポスト、フォロワー、フォロー中アカウントなどを含むHTML/JSON形式のデータを提供すると説明しています。
https://help.x.com/ja/managing-your-account/accessing-your-x-data

## できること

- 投稿数、投稿時間帯、投稿タイプ、頻出語を集計する
- いいねをキーワードで分類し、TF-IDF + KMeansでクラスタリングする
- フォロー/フォロワー集合と交流回数を集計する
- 投稿時間帯ごとの過去の平均エンゲージメントを表示する
- 低交流かつ相互フォローでないアカウント、高交流の相互フォローを一覧化する
- 集計結果をCSVで出力する

表示するスコアや一覧は、このリポジトリの設定値と過去データから計算した指標です。将来のエンゲージメント、人物の重要性、フォロー解除の妥当性を保証するものではありません。

## データとネットワーク境界

Pythonアプリは `config.yaml` で指定したローカルファイルを読み込みます。X APIへ投稿やフォロー操作を送る実装はありません。

一方、現在のWeb UIはブラウザから Google Fonts、Tailwind CSS CDN、unpkg、jsDelivr の静的アセットを取得します。そのため、Web UI全体をオフライン動作とは扱いません。

`config.yaml` の `data/tweets.js` などのパスはこのアプリの入力設定であり、Xが将来のアーカイブでも同じファイル名を保証するという意味ではありません。

## セットアップ

Python 3.11以上と `uv` を使用します。

```bash
uv sync --locked
```

Xデータアーカイブから利用するファイルを配置し、必要なら `config.yaml` のパスを変更します。

```yaml
files:
  tweets: "data/tweets.js"
  follower: "data/follower.js"
  following: "data/following.js"
  like: "data/like.js"
```

入力ファイルが存在しない項目は空データとして扱います。

## 起動

```bash
task dev
```

または:

```bash
uv run uvicorn src.web.app:app --host 0.0.0.0 --port 8000 --reload
```

ブラウザで `http://localhost:8000` を開きます。

## 検証

Pull Requestとmain pushではGitHub Actionsで次を確認します。

```bash
uv sync --locked
uvx ruff check .
uv run python -c "import src.web.app"
```

実データを使ったブラウザE2Eテストは現在ありません。
