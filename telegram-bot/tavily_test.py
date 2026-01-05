# To install: pip install tavily-python
from tavily import TavilyClient


client = TavilyClient("...")
'''response = client.search(
    query="Что такое таксономия блума?"
)'''
response = client.crawl(
    url="https://skillbox.ru/media/education/taksonomiya-bluma-chto-eto-takoe-i-zachem-ona-pedagogam-i-metodistam/",
    extract_depth="advanced"
)
print(response)
