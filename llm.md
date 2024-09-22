# WSL2環境でのvLLMクイックセットアップガイド

## 前提条件

- Windows 10/11 with WSL2
- NVIDIA GPU（CUDA対応）
- Windows側にNVIDIA GPUドライバーインストール済み

## 初回セットアップ手順

1. WSL2でUbuntuを起動

2. 環境確認
   ```bash
   # GPUの確認
   nvidia-smi
   
   # WSL2のIPアドレス確認（後で使用）
   ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1
   ```

3. Dockerのインストールと設定
   ```bash
   # Dockerインストール
   sudo apt update && sudo apt install -y docker.io
   sudo usermod -aG docker $USER && newgrp docker
   
   # インストール確認
   docker --version
   
   # Docker daemon起動
   sudo service docker start
   ```

4. NVIDIAコンテナツールキットのインストール
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

5. vLLMコンテナの初回実行
   - Hugging Face tokenを取得: https://huggingface.co/settings/tokens/new?tokenType=read
   ```bash
   docker run --gpus all --name vllm -p 8000:8000 --ipc=host \
     -v ~/.cache/huggingface:/root/.cache/huggingface \
     --env "HUGGING_FACE_HUB_TOKEN=<your_token>" \
     vllm/vllm-openai:latest \
     --model microsoft/Phi-3.5-mini-instruct
   ```

6. vLLMサーバーのテスト（別ターミナルで実行）
   ```bash
   # <wsl2_ip>は手順2で確認したIPアドレス
   curl -X POST "http://192.168.92.83:8000/v1/chat/completions" \
   -H "Content-Type: application/json" \
   -d '{"model": "microsoft/Phi-3.5-mini-instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
   ```

## 2回目以降の起動

1. コンテナ起動
   ```bash
   docker start vllm
   ```

## トラブルシューティング

- **コンテナ名競合**: `docker rm vllm` で削除
- **接続問題**: `docker logs vllm` でエラーを確認
- **WSL2 IP使用**: `ip addr show eth0` で確認し、localhostの代わりに使用

## 注意事項

- Hugging Face tokenは安全に管理してください
