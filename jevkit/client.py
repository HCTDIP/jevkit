"""jevkit — Python client for the Jev decision model (OpenRouter Decisions API)."""
import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass

API = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"


@dataclass
class Answer:
    """单个问题的回答（校准结果）。"""
    name: str
    type: str                    # noul / choice / score
    noul: float = None           # noul 概率
    choice: str = None           # choice 选中项
    confidence: float = None     # choice/score 置信
    probabilities: dict = None   # choice 分布


class Client:
    """Jev Decisions API client。

    不是聊天模型：state + typed questions → 校准概率，零文本生成。
    """

    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("JEV_API_KEY")
        self.model = model

    def decide(self, questions: dict, state: str = "", timeout: int = 30) -> dict:
        """单次 decisions 调用。questions 是 record: {name: {type, instructions, ...}}。"""
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set.")
        payload = {"model": self.model, "state": state, "questions": questions}
        req = urllib.request.Request(
            API,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="ignore")
            # RuntimeError — except Exception 能接住（fallback 友好）
            raise RuntimeError(f"Jev HTTP {e.code}: {err[:300]}")

    def noul(self, name: str, instructions: str, criteria: dict,
             state: str = "", timeout: int = 30) -> float:
        """是/否校准概率。criteria: {"true": str, "false": str}（描述，不是 options）。"""
        r = self.decide(
            {name: {"type": "noul", "instructions": instructions, "criteria": criteria}},
            state=state, timeout=timeout,
        )
        a = r.get("answers", {}).get(name, {})
        if "noul" in a:
            return float(a["noul"])
        raise RuntimeError(f"Jev 响应无 noul: {json.dumps(r)[:200]}")

    def choice(self, name: str, instructions: str, options: list,
               state: str = "", timeout: int = 30) -> Answer:
        """挑一。"""
        r = self.decide(
            {name: {"type": "choice", "instructions": instructions, "options": options}},
            state=state, timeout=timeout,
        )
        a = r.get("answers", {}).get(name, {})
        return Answer(name=name, type="choice", choice=a.get("choice"),
                      confidence=a.get("confidence"), probabilities=a.get("probabilities"))


def gate(p: float, act: float = 0.7, confirm: float = 0.5) -> str:
    """confidence-gated act/confirm/escalate。

    act(>=0.7) → 直接执行；confirm(0.5-0.7) → 待审（borderline 会翻转，不自动执行）；
    escalate(<0.5) → 升级/跳过。
    """
    if p >= act:
        return "act"
    if p >= confirm:
        return "confirm"
    return "escalate"
