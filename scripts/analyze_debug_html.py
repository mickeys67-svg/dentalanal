from bs4 import BeautifulSoup
import os

# Adjust path for running inside container vs host
path = "backend/debug_view.html"
if not os.path.exists(path):
    path = "debug_view.html"

try:
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
except FileNotFoundError:
    print(f"File not found: {path}")
    exit(1)

soup = BeautifulSoup(html, 'html.parser')

print(f"HTML Length: {len(html)}")

# Check for Blog Tab content
# Usually in <section class="sc_new ..."> or similar
sections = soup.select("section")
print(f"Found {len(sections)} sections")
for sec in sections:
    cls = sec.get("class", [])
    print(f"Section classes: {cls}")
    # Check if it contains "blog" or "view"
    text = sec.text[:50]
    print(f"  Text start: {text}")

items = soup.select("li.bx")
print(f"Found {len(items)} items using 'li.bx'")

items_total = soup.select(".total_area")
print(f"Found {len(items_total)} items using '.total_area'")

# Print details of a few items if found
if items:
    print("--- Item 0 structure ---")
    print(items[0].prettify()[:500])
else:
    print("No items found with li.bx. Listing other potential lists:")
    uls = soup.select("ul")
    for ul in uls:
        cls = ul.get("class", [])
        if cls:
             print(f"ul class: {cls}, children count: {len(ul.find_all('li', recursive=False))}")
