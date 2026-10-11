from google_play_scraper import reviews, Sort
import pandas as pd

result, token = reviews("com.gojek.app", lang="id", country="id",
                        sort=Sort.NEWEST, count=5000)
pd.DataFrame(result).to_csv("gojek_reviews.csv", index=False)
print(f"Done! Saved {len(result)} reviews.")