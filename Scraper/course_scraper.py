import requests
import json
import os
import re

def scrape_course_content():
    """
    Scrapes the "Tools in Data Science" course content from its public GitHub repo.
    This version uses the corrected filenames found in the repository.
    """
    
    repo_owner = "sanand0"
    repo_name = "tools-in-data-science-public"
    branch = "main"
    
    raw_content_base_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/"
    public_site_base_url = "https://tds.s-anand.net/#/"

    # CORRECTED list of markdown files based on the actual repository contents.
    # The main page is README.md, and prefixes are removed from other files.
    pages_to_scrape = [
        "README.md",
        "development-tools.md",
        "deployment-tools.md",
        "large-language-models.md",
        "data-sourcing.md",
        "data-preparation.md",
        "data-analysis.md",
        "data-visualization.md"
    ]
    
    scraped_data = []
    
    print("🚀 Starting scraper with updated URLs...")

    for page_md in pages_to_scrape:
        raw_url = f"{raw_content_base_url}{page_md}"
        
        # Adjust the public-facing URL based on the filename
        if page_md == "README.md":
            # The README corresponds to the main 2025-01 section
            page_name = "2025-01"
            public_url = f"{public_site_base_url}{page_name}/"
        else:
            page_name = page_md.replace(".md", "")
            public_url = f"{public_site_base_url}{page_name}/"

        print(f"📄 Fetching content for: {page_md}")
        
        try:
            response = requests.get(raw_url)
            response.raise_for_status()  # Checks for HTTP errors
            
            content = response.text
            
            # The title is assumed to be the first H1 heading in the markdown file
            first_line = content.split('\n', 1)[0]
            title = re.sub(r'#+\s*', '', first_line).strip()
            
            scraped_data.append({
                "title": title,
                "url": public_url,
                "content": content
            })
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not fetch {raw_url}. Error: {e}")
            
    return scraped_data

if __name__ == "__main__":
    data = scrape_course_content()
    
    if data:
        output_dir = '../data'
        output_file = os.path.join(output_dir, 'course_content.json')

        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        absolute_path = os.path.abspath(output_file)
        print(f"\n💾 Data saved to: {absolute_path}")
        print(f"📊 Total pages scraped: {len(data)}")
        
        print("\n🔍 Sample content from the first scraped page:")
        print(f"   Title: {data[0]['title']}")
        print(f"   URL: {data[0]['url']}")
        print(f"   Preview: {data[0]['content'][:200].strip()}...")
    else:
        print("\n🚫 No data was scraped. Please check your internet connection and the script's URLs.")
