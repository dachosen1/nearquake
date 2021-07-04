from dags.models.tweeter import post_tweet, weekly_top_tweet, weekly_quake_count


if __name__ == '__main__':
    post_tweet(weekly_top_tweet())
    post_tweet(weekly_quake_count())
