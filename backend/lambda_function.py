"""AWS Lambda Function URL handler for a minimal Bedrock chat PoC."""

from __future__ import annotations

import base64
import json
import os
import traceback
from typing import Any, Dict, Tuple

import boto3

from agent_config import build_system_prompt

DEFAULT_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
DEFAULT_REGION = os.environ.get("AWS_REGION", "us-east-1")


def _cors_headers() -> Dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
        "Content-Type": "application/json; charset=utf-8",
    }


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_body(event: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    try:
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except json.JSONDecodeError as exc:
        raise ValueError("リクエストbodyはJSON形式にしてください。") from exc

    message = body.get("message")
    if not message and isinstance(body.get("inputs"), dict):
        message = body["inputs"].get("input_text")
    if not isinstance(message, str) or not message.strip():
        raise ValueError('"message" または "inputs.input_text" に文字列を指定してください。')
    return message.strip(), body


def _call_bedrock(message: str) -> str:
    region = os.environ.get("BEDROCK_REGION", DEFAULT_REGION)
    model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    client = boto3.client("bedrock-runtime", region_name=region)
    result = client.converse(
        modelId=model_id,
        system=[{"text": build_system_prompt(message)}],
        messages=[{"role": "user", "content": [{"text": message}]}],
        inferenceConfig={"maxTokens": 800, "temperature": 0.3},
    )
    contents = result.get("output", {}).get("message", {}).get("content", [])
    texts = [item.get("text", "") for item in contents if item.get("text")]
    return "\n".join(texts).strip() or "Bedrockから空の応答が返りました。"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = (event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod") or "").upper()
    if method == "OPTIONS":
        return _response(200, {"reply": "ok", "outputs": "ok"})
    if method and method != "POST":
        return _response(405, {"error": "POSTメソッドを使用してください。", "reply": "", "outputs": ""})

    try:
        message, _ = _parse_body(event)
        reply = _call_bedrock(message)
        return _response(200, {"reply": reply, "outputs": reply})
    except ValueError as exc:
        return _response(400, {"error": str(exc), "reply": "", "outputs": ""})
    except Exception as exc:  # Keep Lambda errors JSON-readable for PoC troubleshooting.
        print(traceback.format_exc())
        return _response(500, {"error": f"サーバーエラー: {exc}", "reply": "", "outputs": ""})
