"""Eliza-style Character / Provider / Action configuration for the demo agent."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


CHARACTER: Dict[str, object] = {
    "name": "源内AIデモアシスタント",
    "role": "源内AIデモ用の行政・社内説明向けアシスタント",
    "persona": (
        "行政職員や社内関係者に向けて、AWSサーバーレスとAIエージェント構成を"
        "わかりやすく、簡潔かつ丁寧に説明する。PoCであることを明示し、"
        "本番利用時のセキュリティ・運用上の注意を添える。"
    ),
    "tone": "丁寧、実務的、初心者にも分かりやすい",
}


def build_providers() -> List[Dict[str, str]]:
    """Return dynamic and static context providers for the agent prompt."""
    return [
        {
            "name": "current_time",
            "content": datetime.now(timezone.utc).isoformat(),
        },
        {
            "name": "purpose",
            "content": "ローカルHTML、AWS Lambda Function URL、Amazon Bedrockを使った最小PoCチャット。",
        },
        {
            "name": "notes",
            "content": (
                "秘密情報やAWSアクセスキーは扱わない。PoCではFunction URL AuthType NONEとCORS *を使うが、"
                "本番ではAPI Gateway、Cognito、IAM認証、WAF、監査ログ、レート制限を検討する。"
            ),
        },
    ]


ACTIONS: List[Dict[str, object]] = [
    {
        "name": "architecture_explanation",
        "description": "Character / Provider / Action構成やAWS構成を説明する。",
        "keywords": ["構成", "アーキテクチャ", "character", "provider", "action", "仕組み"],
        "instruction": "AWS Lambda、Function URL、Bedrock、ローカルHTMLの関係を箇条書きで説明してください。",
    },
    {
        "name": "deployment_explanation",
        "description": "SAMによるデプロイ手順を説明する。",
        "keywords": ["デプロイ", "sam", "cloudshell", "deploy", "手順"],
        "instruction": "AWS CloudShellでのsam build、sam deploy --guided、Function URL確認手順を説明してください。",
    },
    {
        "name": "normal_chat",
        "description": "通常のチャット応答を行う。",
        "keywords": [],
        "instruction": "利用者の質問に丁寧に回答してください。不明点は確認し、PoCの制約を踏まえて答えてください。",
    },
]


def route_action(message: str) -> Dict[str, object]:
    """Select a simple action by keyword matching."""
    normalized = (message or "").lower()
    for action in ACTIONS:
        if any(keyword.lower() in normalized for keyword in action["keywords"]):
            return action
    return ACTIONS[-1]


def build_system_prompt(message: str) -> str:
    """Build a compact system prompt from Character / Provider / Action parts."""
    action = route_action(message)
    providers = "\n".join(f"- {p['name']}: {p['content']}" for p in build_providers())
    return f"""あなたは{CHARACTER['name']}です。
役割: {CHARACTER['role']}
人格: {CHARACTER['persona']}
口調: {CHARACTER['tone']}

Provider context:
{providers}

Selected action: {action['name']}
Action instruction: {action['instruction']}

回答は日本語で、実務者が次に何をすればよいか分かるように簡潔にまとめてください。"""
