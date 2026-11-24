BABY_KEYWORDS = [
    "기저귀", "하기스", "팸퍼스", "마미포코", "보솜이", "군기저귀",
    "물티슈", "분유", "이유식", "젖병", "아기", "유아", "신생아", "베이비",
]


def is_baby_deal(title: str) -> bool:
    return any(k in title for k in BABY_KEYWORDS)
