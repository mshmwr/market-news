import os

from models import SocialSignal


def _unavailable(ticker: str) -> SocialSignal:
    return SocialSignal(posts=[], ticker=ticker, available=False)


def fetch_social_signal(ticker: str) -> SocialSignal:
    client_id = os.environ.get("PRAW_CLIENT_ID")
    client_secret = os.environ.get("PRAW_CLIENT_SECRET")
    user_agent = os.environ.get("PRAW_USER_AGENT")

    if not (client_id and client_secret and user_agent):
        return _unavailable(ticker)

    try:
        import praw

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

        posts: list[dict] = []
        for subreddit_name in ("wallstreetbets", "stocks"):
            subreddit = reddit.subreddit(subreddit_name)
            for submission in subreddit.search(ticker, limit=50, sort="relevance"):
                posts.append({
                    "title": submission.title,
                    "score": submission.score,
                    "url": submission.url,
                })

        posts.sort(key=lambda p: p["score"], reverse=True)
        return SocialSignal(posts=posts[:10], ticker=ticker, available=True)
    except Exception:
        return _unavailable(ticker)
