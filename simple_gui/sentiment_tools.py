from textblob import TextBlob
import nltk

# 自动下载必要资源（第一次运行会用到）
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


def analyze_sentiment(message: str):
    polarity = TextBlob(message).sentiment.polarity

    if polarity > 0.2:
        return "Positive", "😊"
    elif polarity < -0.2:
        return "Negative", "😡"
    else:
        return "Neutral", "😐"