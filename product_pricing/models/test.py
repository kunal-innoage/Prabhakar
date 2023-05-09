# import requests

# from bs4 import BeautifulSoup 

# r=requests.get("https://www.wayfair.co.uk/rugs/pdp/blue-elephant-kopf-browngreybeige-rug-u003415115.html?piid=213222371")

# print(r.status_code)
# import requests
# from bs4 import BeautifulSoup

# url = "https://www.wayfair.co.uk/rugs/pdp/blue-elephant-kopf-browngreybeige-rug-u003415115.html?piid=213222371"

# response = requests.get(url)

# soup = BeautifulSoup(response.content, "html.parser")

# classes = [tag["class"] for tag in soup.find_all()]

# for class_list in classes:
#     for class_name in class_list:
#         print(class_name)

import requests
from bs4 import BeautifulSoup

url = "https://www.wayfair.co.uk/rugs/pdp/blue-elephant-kopf-browngreybeige-rug-u003415115.html?piid=213222371"

response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")

tags = soup.find_all()

for tag in tags:
    if "class" in tag.attrs:
        class_list = tag["class"]
        for class_name in class_list:
            print(class_name)



