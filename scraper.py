import re
from urllib.parse import urlparse
from typing import DefaultDict
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

# A set of common English stop words to ignore
stopwords = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd",
    "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

# Global word frequency map
word_frequency_map = DefaultDict(int)

# Keep a set of all the pages here so we can analyze subdomains later
pages_set = set()

# Website JSON for debugging
global websites_as_json
websites_as_json = []

"""
- Make sure to defragment the URLs
- Use BeautifulSoup to extract links and content
- Save URLs and web page content to disk for parsing in report
"""
def extract_next_links(url, resp) -> list["urls"]:
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    hyperlinks = []
    
    # Used to store the website data for report in a JSON format
    website_json = {
        "url": resp.url,
        "status": resp.status,
        "error": resp.error,
        "raw_content": resp.raw_response.content.decode('utf-8')
    }
    websites_as_json.append(website_json)

    # If the response code isn't in the 200s or there is no content return an empty list
    if resp.status < 200 or resp.status > 299 or resp.raw_response is None:
        return []

    # TODO Check for robots.txt sitemaps

    # TODO Parse normal web pages and defragment URLs

    return hyperlinks


"""
- Only URLs that are within the domains and paths
"""
def is_valid(url): 
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(r"^https?:\/\/(?:[\w.-]+\.)?(?:ics\.uci\.edu|cs\.uci\.edu|informatics\.uci\.edu|stat\.uci\.edu)(?:\/.*)?$", url):  # if the link is not in the list of valid hostnames
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise


if __name__ == "__main__":
    print(is_valid("hello"))
    print(is_valid("https://ics.uci.edu/some/other/path#pleasework"))


"""
Things to remember
- Only crawl the following domains:  # Done I think
    - *.ics.uci.edu/*
    - *.cs.uci.edu/*
    - *.informatics.uci.edu/*
    - *.stat.uci.edu/*
- Keep track of unique pages
    - Uniqueness: only established by the URL and discarding the fragment
- Keep track of longest page in terms of the number of words (HTML markup doesn't count)
- What are the 50 most common words in the entire set of pages crawled under these domains? (Ignore english stop words)
    - Keep a global frequency count of all words seen so far besides stop words
- Keep track of how many subdomains found in the uci.edu domain
    - List subdomains and the number of unique pages in each subdomain
    - This can be done by keeping a list of all the unique pages
        - Parse the list and get subdomains and keep a frequency of the pages while parsing
"""