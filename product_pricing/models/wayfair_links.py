import requests
from bs4 import BeautifulSoup

url = 'https://www.wayfair.co.uk/rugs/pdp/blue-elephant-agner-dark-redsaffron-rug-u004474971.html?rtype=8&redir=U004474971&piid=1553983130'

# Send a GET request to the URL
response = requests.get(url)
print(response)

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Find the element that contains the price information
price_element = soup.find('span', {'class': 'Price-characteristic'})

# Extract the price value
price = price_element.text.strip()

# Output the price
print('Product Price:', price)
