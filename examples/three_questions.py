#!/usr/bin/env python3
"""最小示例：一次 decide() 同时问三件事（noul + score + choice）。

跑法:
    export OPENROUTER_API_KEY=sk-or-...
    cd jevkit && python3 examples/three_questions.py

成本：约 $0.00003 / 次（三个问题一次请求）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jevkit import Client, gate  # noqa: E402

STATE = (
    "Opportunity: 'Create contributors webpage', 23 USDC bounty, opened 3 months ago "
    "and still open. Four applicants submitted pull requests with wallet addresses; "
    "none has been paid. Other bounties on the same board use fictional currencies. "
    "The maintainer bot replies in roleplay prose."
)


def main():
    if not (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("JEV_API_KEY")):
        print("先设置 OPENROUTER_API_KEY 再跑本示例")
        return 1

    client = Client()
    resp = client.decide({
        # ① noul：真假/值不值 —— criteria 是 record
        "is_real": {
            "type": "noul",
            "instructions": "Is this a genuine paid opportunity?",
            "criteria": {
                "true": "a real payer with verifiable payment record and human review",
                "false": "no payment record, roleplay only, or asks for secrets",
            },
        },
        # ② score：期望值 —— criteria 是 array（锚点表）
        "ev": {
            "type": "score",
            "instructions": "Score the expected value of pursuing this.",
            "criteria": [
                "1 - not worth it",
                "2 - weak",
                "3 - fair (real payer, winnable)",
                "4 - strong",
                "5 - excellent",
            ],
        },
        # ③ choice：下一步 —— criteria 是 record（键即选项）
        "next_step": {
            "type": "choice",
            "instructions": "What should we do next?",
            "criteria": {
                "submit_now": "we can deliver a strong submission immediately",
                "ask_sponsor": "need clarification before spending effort",
                "skip": "not worth the effort or risk",
            },
        },
    }, state=STATE)

    a = resp["answers"]
    p = float(a["is_real"]["noul"])
    raw = float(a["ev"]["score"])
    anchors = 5 - 1                      # 锚点个数 - 1
    ev = max(0.0, min(1.0, raw / anchors))   # ⚠️ score 是锚点序号，必须归一化
    step = a["next_step"]["choice"]
    conf = a["next_step"].get("confidence")

    print(f"noul(真伪)    = {p:.2f}   → gate: {gate(p)}")
    print(f"score(EV)     = {raw:.2f} 锚点序号 = 归一 {ev:.2f}")
    print(f"choice(下一步) = {step} (confidence {conf})")
    print(f"用例成本       = ${(resp.get('usage') or {}).get('cost', 0):.6f}")

    verdict = "GO" if (gate(p) == "act" and ev >= 0.5) else ("DROP" if gate(p) == "escalate" or ev < 0.25 else "HOLD")
    print(f"\n结论（示例规则）= {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
