import requests
from bs4 import BeautifulSoup

root = "https://forgottenrealms.fandom.com/wiki/"
specific_page = "Elminster"

# MediaWiki API endpoint (instead of page HTML)
api_url = (
    "https://forgottenrealms.fandom.com/api.php"
    "?action=parse"
    f"&page={specific_page}"
    "&prop=text"
    "&format=json"
)

def scrape_page():
    response = requests.get(api_url)
    data = response.json()

    # Extract rendered HTML from API response
    html = data["parse"]["text"]["*"]
    soup = BeautifulSoup(html, "html.parser")

    # Remove citation superscripts like [51]
    for sup in soup.find_all("sup"):
        sup.decompose()

    main_content = soup.select_one(".mw-parser-output")
    if not main_content:
        print("Main content not found")
        return

    with open(f"./lore/{specific_page}.txt", "w", encoding="utf-8") as f:
        # Loop only over h2 headings
        for h2 in main_content.find_all("h2"):
            title_span = h2.find("span", class_="mw-headline")
            if not title_span:
                continue

            section_title = title_span.text.strip()

            # STOP when Appendix is reached
            if section_title.lower().startswith("appendix"):
                break

            f.write(f"\n\n=== {section_title} ===\n")

            # Write all <p> until the next h2
            for sibling in h2.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name == "p":
                    text = sibling.get_text(" ", strip=True)
                    if text:
                        f.write(text + "\n")

if __name__ == "__main__":
    try:
        scrape_page()
    except Exception as e:
        print(f"An error occurred: {e}")

# Improvement, missing the first part introduction, try to add that.