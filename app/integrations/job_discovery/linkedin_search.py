"""Generate LinkedIn job-search links without scraping LinkedIn."""
from urllib.parse import urlencode

def linkedin_search_urls(profile):
    links = []
    titles = profile.target_titles[:5] or ["Software Engineer"]
    for title in titles:
        params = {"keywords": title}
        if profile.location:
            params["location"] = profile.location
        if profile.remote_only:
            params["f_WT"] = "2"
        links.append((
            title,
            "https://www.linkedin.com/jobs/search/?" + urlencode(params),
        ))
    return links
