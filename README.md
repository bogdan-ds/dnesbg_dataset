## Dnes.bg comment dataset

This is a dataset of comments from the Bulgarian news site [dnes.bg](https://dnes.bg/). The repository contains the code needed to extract the comments. Comments are stored in a CSV format along with their author's handle and the positive and negative votes they received.

# Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

In order to fetch the pages and adjust the date range you want the comments from, go to the url: https://www.dnes.bg/news.php?last&cat=1&page=0



```python
from main import DnesArticleScraper, DnesCommentScraper

article_scraper = DnesArticleScraper(page_start=10, page_end=20)
article_scraper.run()

comment_scraper = DnesCommentScraper()
comment_scraper.process_articles()

```