from bs4 import BeautifulSoup
import os

file_path = "debug_view.html"

if not os.path.exists(file_path):
    print(f"File {file_path} not found.")
    exit()

with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Check title
print(f"Title: {soup.title.string if soup.title else 'No Title'}")

# List all classes used in li elements to find the result item container
li_classes = set()
for li in soup.find_all("li"):
    if li.get("class"):
        li_classes.add(".".join(li.get("class")))

print(f"\nUnique LI classes found ({len(li_classes)}):")
for c in sorted(list(li_classes)):
    print(f"li.{c}")

# Find elements containing keyword "임플란트"
print(f"\nElements containing '임플란트':")
count = 0
for tag in soup.find_all(string=lambda text: "임플란트" in text if text else False):
    parent = tag.parent
    print(f"Tag: {parent.name}, Class: {parent.get('class')}, Text: {tag.strip()[:50]}...")
    count += 1
    if count > 10:
        break

# Try to find common view containers
print("\nChecking for common containers:")
containers = soup.select(".total_wrap")
print(f".total_wrap count: {len(containers)}")

containers = soup.select(".view_wrap")
print(f".view_wrap count: {len(containers)}")

containers = soup.select(".api_txt_lines")
print(f".api_txt_lines count: {len(containers)}")
