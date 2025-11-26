import os

cwd = os.getcwd()
dirs = cwd.split("/")
output_dir = "/".join(dirs[:-1]) + "/output"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Download and display a web page as a string
import requests
response = requests.get("https://duunitori.fi/tyopaikat/ala/ohjelmointi-ja-ohjelmistokehitys")
web_content = response.text

with open(f"{output_dir}/webpage.html", "w", encoding="utf-8") as file:
    file.write(web_content)