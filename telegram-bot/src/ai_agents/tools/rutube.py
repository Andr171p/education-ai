import requests

r = requests.get("https://rutube.ru/api/search/video/?query='C#'")

print(r.json())
