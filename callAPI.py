import requests

input_string = "sleep in bed"
url = 'http://localhost:5000/experience/' + input_string
response = requests.get(url)
print(response.text)
