# 🚀 Twitter(X) データ分析ツール

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![HTMX](https://img.shields.io/badge/HTMX-339933?style=for-the-badge&logo=htmx)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

Twitter(X)のデータアーカイブを利用して、あなたの活動を多角的に分析・可視化するツールです。
完全ローカル環境で動作するため、高速かつプライバシーも安心。外部APIへの送信は一切行いません。

---

## ✨ 機能

- **📊 包括的な分析 (Analytics)**
    - **活動ヒートマップ**: 投稿アクティビティを日次・時間帯別・Githubスタイルの草グラフで可視化。
    - **コンテンツ分析**: 頻出キーワードや興味関心を抽出してワードクラウド化（TF-IDF使用）。
    - **投稿タイプ**: オリジナルツイート、リプライ、リツイートの比率を分析。

- **⏰ 効率化インサイト (Efficiency)**
    - **ベストな投稿時間**: 過去のデータから、エンゲージメント（いいね・RT）が得られやすい「最適な投稿時間帯」を提案します。

- **👥 オーディエンス分析 (Audience Insights)**
    - **関係性グラフ**: 相互フォロー、片思い、片思われの比率を視覚化（積み上げ棒グラフ）。
    - **トップインタラクション**: 最も交流の多いユーザー（リプライ・RT数）をランキング表示。

- **🧹 フォロー整理 (Follow Management)**
    - **アンフォロー候補**: 長期間交流がなく、かつフォローバックされていないアカウントをリストアップ。
    - **重要な相互フォロワー**: インタラクション頻度が高く、大切にすべきフォロワーを特定。CSVエクスポート対応。

- **💻 モダンなWebダッシュボード**
    - **FastAPI + HTMX**: 高速で快適な操作感のUI。
    - **レスポンシブデザイン**: スマートフォンやタブレットでも閲覧可能。

---

## 🛠️ インストール

依存関係の管理には `uv` を使用します。

```bash
# 依存関係のインストール
uv sync
```

---

## 🚀 使い方

### Webダッシュボードの起動

以下のコマンドを実行すると、分析サーバーが起動します。

```bash
task dev
# または
uv run uvicorn src.web.app:app --host 0.0.0.0 --port 8000 --reload
```

ブラウザで **[http://localhost:8000](http://localhost:8000)** にアクセスして分析結果を確認してください。

---

## � 設定

`config.yaml` を編集し、Twitterアーカイブデータへのパスを指定してください。

```yaml
# config.yaml (例)
files:
  tweets: "data/tweets.js"      # 全ツイート履歴
  follower: "data/follower.js"  # フォロワー一覧
  following: "data/following.js" # フォロー中一覧
  like: "data/like.js"          # いいね履歴
```

---

## 📂 プロジェクト構成

```
.
├── src/
│   ├── analytics/      # 分析ロジック (オーディエンス, 興味関心, 推奨等)
│   ├── web/            # Webアプリケーション (FastAPI + HTMX)
│   ├── features.py     # 統計処理・特徴量抽出
│   └── visualization.py # グラフ生成
├── data/               # データディレクトリ (Twitterアーカイブ)
├── output/             # 出力ディレクトリ (CSVレポート等)
├── config.yaml         # 設定ファイル
└── Taskfile.yaml       # タスクランナー定義
```

---

<p align="center">
  <sub>Built with ❤️ by Antigravity. Minimalist, fast, and local-first.</sub>
</p>
