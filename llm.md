# WSL2環境でのvLLMクイックセットアップガイド

## 前提条件
- Windows 10/11 with WSL2
- NVIDIA GPU（CUDA対応）
- Windows側にNVIDIA GPUドライバーインストール済み
 

## セットアップ手順

1. WSL2でUbuntuを起動

2. GPUの確認
   ```bash
   nvidia-smi
   ```

3. Dockerインストール
   ```bash
   sudo apt update && sudo apt install -y docker.io
   sudo usermod -aG docker $USER && newgrp docker
   ```
1. Dockerがインストールされていることを確認:
   ```
   docker --version
   ```
2. Docker daemonが起動していることを確認:
   ```
   sudo service docker start
   ```
4. NVIDIAコンテナツールキットインストール
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

5. vLLMコンテナ初回実行
   https://huggingface.co/settings/tokens/new?tokenType=read
   ```bash
   docker run --gpus all --name vllm -p 8000:8000 --ipc=host \
     -v ~/.cache/huggingface:/root/.cache/huggingface \
     --env "HUGGING_FACE_HUB_TOKEN=<your_token>" \
     vllm/vllm-openai:latest \
     --model microsoft/Phi-3.5-mini-instruct
   ```

7. vLLMサーバーテスト（別ターミナルで実行）
   ```bash
   curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{"model": "microsoft/Phi-3.5-mini-instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
   ```

## 2回目以降の起動

1. コンテナ起動
   ```bash
   docker start vllm
   ```

2. ログの確認（オプション）
   ```bash
   docker logs vllm
   ```

## トラブルシューティング
- コンテナ名競合: `docker rm vllm`で削除
- GPU認識されない: Windowsのドライバー更新
- 接続問題: `docker logs vllm`でエラー確認
- WSL2 IP使用: `ip addr show eth0`で確認し、localhostの代わりに使用

## 注意事項
- Hugging Face tokenは安全に管理
- 本番環境では適切な認証とHTTPS設定を推奨

このガイドで、WSL2環境でのvLLM高速推論環境が構築できます。
