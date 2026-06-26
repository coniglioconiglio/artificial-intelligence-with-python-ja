# PythonによるAIプログラミング入門 / 源内AI Bedrock PoC

本リポジトリは、書籍『PythonによるAIプログラミング入門』のサンプルコードに加えて、AWS Lambda Function URL と Amazon Bedrock を使った最小構成の「源内AI」チャットPoCを含みます。

## 追加したPoCの構成

```text
ローカルPCのブラウザ
  └─ frontend/index.html（単体HTML。Python不要）
      └─ fetch POST
          └─ AWS Lambda Function URL（AuthType NONE / CORS *）
              └─ backend/lambda_function.py
                  └─ Amazon Bedrock Converse API
```

エージェント構成は `backend/agent_config.py` にまとめています。

- **Character**: 「源内AIデモ用の行政・社内説明向けアシスタント」という人格・口調
- **Provider**: 現在時刻、利用目的、PoC上の注意事項
- **Action**: 通常チャット、構成説明、デプロイ説明の簡易ルーティング

## 前提条件

- AWSアカウントを利用できること
- AWS CloudShellを利用すること
- AWS SAM CLIが使えること（CloudShellには多くの環境でプリインストールされています）
- Amazon Bedrockで利用する対象モデルが有効化されていること
  - AWS Bedrockで対象モデルの利用申請が必要な場合があります。
  - 例: `anthropic.claude-3-haiku-20240307-v1:0`
- 社内PCにはPythonをインストールしません。ローカルでは `frontend/index.html` をブラウザで開くだけです。

## ディレクトリ

```text
backend/
  agent_config.py      # Character / Provider / Action 定義
  lambda_function.py   # Lambda Function URL handler / Bedrock Converse呼び出し
frontend/
  index.html           # ローカルで開ける単体HTMLチャットUI
infra/
  template.yaml        # AWS SAMテンプレート
```

## デプロイ手順（AWS CloudShell）

### 1. リポジトリをclone

```bash
git clone <このリポジトリのURL>
cd artificial-intelligence-with-python-ja
```

### 2. SAMテンプレートを確認

```bash
cd infra
sam validate
```

### 3. ビルド

```bash
sam build
```

### 4. 初回デプロイ

```bash
sam deploy --guided
```

対話では、例えば次のように指定します。

- **Stack Name**: `gennai-ai-bedrock-poc`
- **AWS Region**: Lambdaを置きたいリージョン（例: `ap-northeast-1`）
- **Parameter BedrockRegion**: Bedrock Runtimeを呼び出すリージョン（例: `ap-northeast-1`）
- **Parameter BedrockModelId**: 利用するBedrockモデルID（例: `anthropic.claude-3-haiku-20240307-v1:0`）
- **Confirm changes before deploy**: `Y` または `N`
- **Allow SAM CLI IAM role creation**: `Y`
- **Disable rollback**: 任意
- **Save arguments to configuration file**: `Y`

デプロイが成功すると、Outputsに `GennaiAiChatFunctionUrl` が表示されます。

### 5. 2回目以降のデプロイ

初回に設定を保存した場合は、次のコマンドで再デプロイできます。

```bash
sam build
sam deploy
```

## ローカルHTMLから使う

1. 社内PCで `frontend/index.html` をダブルクリックしてブラウザで開きます。
2. `Lambda Function URL` 欄に、SAMデプロイ後の `GennaiAiChatFunctionUrl` を貼り付けます。
3. メッセージ欄に質問を入力して送信します。

例:

```text
このPoCの構成を説明してください
```

## curlで動作確認

CloudShellまたは任意の端末から、Function URLを環境変数に入れて確認します。

```bash
export FUNCTION_URL='https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.lambda-url.ap-northeast-1.on.aws/'
```

`message` 形式:

```bash
curl -sS -X POST "$FUNCTION_URL" \
  -H 'content-type: application/json' \
  -d '{"message":"このPoCの構成を説明してください"}'
```

`inputs.input_text` 形式:

```bash
curl -sS -X POST "$FUNCTION_URL" \
  -H 'content-type: application/json' \
  -d '{"inputs":{"input_text":"デプロイ手順を教えてください"}}'
```

どちらも次のように `reply` と `outputs` の両方を含むJSONを返します。

```json
{
  "reply": "...",
  "outputs": "..."
}
```

## セキュリティ上の注意

このPoCでは、簡単にローカルHTMLから呼び出せるように次の設定を使っています。

- Lambda Function URL `AuthType: NONE`
- CORS `*`

本番利用では、そのまま公開しないでください。API Gateway、Cognito、IAM認証、WAF、アクセス元制限、監査ログ、レート制限、コスト監視などを検討してください。

また、AWSアクセスキー、APIキー、秘密情報、`.env` ファイルなどはリポジトリにコミットしないでください。

## 既存の書籍サンプルコードについて

書籍サンプルコードの実行には、Python、NumPy、SciPy、Matplotlib、Jupyter Notebookなどが必要です。PoCチャットのローカル利用には、これらを社内PCへインストールする必要はありません。
