"""
nlp_tools.py (FINAL - NO API, NO NLTK)

Features:
- extract_keywords(messages)
- simple_summary(messages)

No external dependency needed
"""

from collections import Counter
import re


# ---------------------------
# Keyword Extraction（简单版）
# ---------------------------
def extract_keywords(messages, top_k=5):
    """
    Extract keywords from chat messages
    """
    if not messages:
        return []

    text = " ".join(messages).lower()

    # 只保留字母
    words = re.findall(r'\b[a-z]+\b', text)

    # 简单停用词（可以自己加）
    stopwords = {
        "the", "is", "and", "to", "i", "you", "a",
        "it", "of", "in", "that", "this", "for",
        "on", "with", "as", "are", "was"
    }

    words = [w for w in words if w not in stopwords]

    freq = Counter(words)
    most_common = freq.most_common(top_k)

    return [word for word, count in most_common]


# ---------------------------
# Summary（超级稳定版🔥）
# ---------------------------
def simple_summary(messages, n=3):
    """
    Return last n messages as summary
    """
    if not messages:
        return []

    return messages[-n:]


# ---------------------------
# Demo（可删）
# ---------------------------
if __name__ == "__main__":
    msgs = [
        "I love this project",
        "This chat system is interesting",
        "We need to add GUI",
        "Maybe add chatbot feature",
        "Also image generation is cool"
    ]

    print("Keywords:", extract_keywords(msgs))
    print("Summary:", simple_summary(msgs))