import re
from typing import List


def test_filter(titles: List[str]):
    results = []
    for title in titles:
        # Match "【ライブ】M/D 朝ニュースまとめ" prefix
        if not re.match(r"^【ライブ】\d{1,2}/\d{1,2}\s+朝ニュースまとめ", title):
            continue

        results.append(title)
    return results


test_titles = [
    "【ライブ】1/17 朝ニュースまとめ 最新情報を厳選してお届け ANN/テレ朝【LIVE】",
    "【ライブ】1/17 昼ニュースまとめ 最新情報を厳選してお届け ANN/テレ朝【LIVE】",
    "【ライブ】1/17 夜ニュースまとめ 最新情報を厳選してお届け ANN/テレ朝【LIVE】",
    "【ライブ】1/17 あさのニュース ANN/テレ朝",
    "【ライブ】1/17 グッド！モーニング ANN/テレ朝",
    "1/17 朝のニュース (No live prefix)",
    "【ライブ】1/17 ANN/テレ朝 (No keywords)",
]

filtered = test_filter(test_titles)
print("Filtered Titles:")
for t in filtered:
    print(f"- {t}")

assert len(filtered) == 1
assert "朝ニュースまとめ" in filtered[0]
print("\nTest Passed!")
