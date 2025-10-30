debug = False

import re
from urllib.parse import urlparse, urljoin, urldefrag
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
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    # Added stop words
    "s", "d", "p", "b"
}

# URLs to avoid when crawling
skip_urls = {
    "https://cs.ics.uci.edu/accessibility-statement", # Page not found
    "https://ics.uci.edu/vrst", # Page not found
    "https://ics.uci.edu/~rjuang", # Page not found
    "https://ics.uci.edu/~bsajadi", # Page not found
    "https://isg.ics.uci.edu/wp-login.php", # Word-press login page is useless
    "https://grape.ics.uci.edu/wiki/asterix", # Download links
    "https://ics.uci.edu/events/category/student-experience/day", # Calendar trap
    "https://ics.uci.edu/events/category/student-experience/list/?tribe-bar-date", # Calendar trap
    "https://grape.ics.uci.edu/wiki/public/zip-attachment", # Attachment download
    "https://grape.ics.uci.edu/wiki/public/raw-attachment", # Attachment download
    "https://isg.ics.uci.edu/events", # Calendar trap
    "http://mlphysics.ics.uci.edu/data", # Scientific data in txt files
    "http://wics.ics.uci.edu", # Crawler trap
    "https://wics.ics.uci.edu", # Crawler trap
    "https://grape.ics.uci.edu/wiki/public/wiki", # Crawler trap
    "https://grape.ics.uci.edu/wiki/public/timeline?", # Crawler trap
    "https://ngs.ics.uci.edu", # Crawler trap
    "http://www.ics.uci.edu/~babaks/BWR/Home_files", # Useless pages
    "https://ics.uci.edu/~dechter/publications", # Useless pages
}

# Global word frequency map
word_frequency_map = DefaultDict(int)

# Longest page
longest_page_url = None
longest_page_len = 0

# Keep a set of all the pages here so we can analyze subdomains later
pages_seen_set = set()

# Subdomains counts
subdomain_counts = DefaultDict(int)

# Website JSON for debugging
websites_as_json = []

# Set of all hashed page contents visited
hashed_content = set()
num_duplicate_pages = 0

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
    global websites_as_json, longest_page_len, longest_page_url, num_duplicate_pages

    # -------------------------------URL Tracking and Duplicate Detection-----------------------------------------

    # Add to the seen set if we haven't parsed the page yet
    if resp.url in pages_seen_set:
        return []
    else:
        pages_seen_set.add(resp.url)

    # Check for no-response page
    if resp.raw_response is None:
        return []

    # Checking for duplicate sites
    hashed_site = hash(resp.raw_response.content)
    if hashed_site in hashed_content:
        num_duplicate_pages+= 1
        return []
    
    hashed_content.add(hashed_site)
    
    # -------------------------------Preprocessing Metadata Checks-----------------------------------------

    # Used to store the website data for report in a JSON format
    website_json = {
        "url": resp.url,
        "status": resp.status,
        "error": resp.error,
    }

    # If the response code isn't in the 200s or there is no content return an empty list
    if resp.status < 200 or resp.status > 299:
        website_json["raw_content"] = resp.raw_response.content.decode('utf-8', errors='ignore')
        websites_as_json.append(website_json)
        return []


    # -------------------------------Getting Page Word Statistics-----------------------------------------

    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    hyperlinks = []

    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    # Scan page text (for word frequency and longest page)
    raw_text = soup.get_text()
    words = re.split(r'[ \t\r\n,.!?;:"(){}\[\]<>/\-&*=\u2013\u00a0\u2022\ufeff\u201d\u201c\u2018\u00a9]+', raw_text)

    page_len = len(words)
    website_json["page_len"] = page_len
    websites_as_json.append(website_json)

    # Check for longest page
    if page_len > longest_page_len or not longest_page_url:
        longest_page_url = resp.url
        longest_page_len = page_len

    for raw_word in words:
        word = raw_word.lower()
        if not word or word in stopwords or word.isdigit():
            continue
        word_frequency_map[word]+= 1

    # Update subdomain count
    subdomain = urlparse(resp.url).hostname
    subdomain_counts[subdomain]+= 1

    # -------------------------------Parse normal web pages and defragment URLs-----------------------------------------

    # Extract anchor tags with the href attribute
    for link in soup.find_all('a', href=True):
        # Defragment the URL by splitting at the '#' and taking everything to the front of it
        curr_link = link.get('href').strip()

        # Skip unwanted link types
        if (
            curr_link.startswith("mailto:") or
            curr_link.startswith("javascript:") or
            curr_link.startswith("#") or
            curr_link.startswith("tel:")
        ):
            continue

        # Convert relative and protocol-relative URLs to absolute URLs
        try:
            full_url = urljoin(resp.url, curr_link)
        # If there is an error just skip the URL
        except:
            continue

        # Remove fragments
        full_url, _ = urldefrag(full_url)

        # Remove trailing slash for consistency in URL storage
        if full_url.endswith('/'):
            full_url = full_url[:-1]

        # TODO handle get requests with parameters?

        hyperlinks.append(full_url)


    return hyperlinks


"""
- Only URLs that are within the domains and paths
"""
def is_valid(url): 
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    
    # Check URLs to skip
    for skip_url in skip_urls:
        if url.startswith(skip_url):
            return False
    
    # Check seen URLs to not crawl again
    if url in pages_seen_set:
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check if the link is not in the list of valid hostnames
        if not re.match(r"^https?:\/\/(?:[\w.-]+\.)?(?:ics\.uci\.edu|cs\.uci\.edu|informatics\.uci\.edu|stat\.uci\.edu)(?:\/.*)?$", url):
            return False

        # Don't allow the content-uploads from this specific route that aren't parsable
        if re.match(r"^https?:\/\/www\.stat\.uci\.edu\/wp-content\/uploads\/[A-Za-z\-]+-?Abstract-?\d{1,2}-\d{1,2}-(?:\d{2}|\d{4})", url):
            return False
        
        # Don't allow these 404 sites that have no information
        if re.match(r"^https?:\/\/www\.stat\.uci\.edu\/ICS\/statistics\/research\/seminarseries\/\d{4}-\d{4}\/index$", url):
            return False
        
        # Don't allow urls with ical={number} since those are download links for an ics calender
        if re.search(r"[?&](?:ical|outlook-ical)=\d+", url):
            return False

        # Don't allow these helpdesk ticket get request pages that have no info
        if re.match(r"^https?:\/\/helpdesk\.ics\.uci\.edu\/Ticket\/Display\.html\?id=\d+$", url): 
            return False

        # Don't allow urls with doku.php since it is a crawler trap with a bunch of useless no information pages
        if "doku.php" in url:
            return False

        # Don't allow ?tribe since it is a calendar crawler trap
        if "?tribe" in url:
            return False
        
        # Don't allow pictures from eppstein's page since they are useless photos with descriptions
        if re.match(r"^https?:\/\/(?:www\.)?ics\.uci\.edu\/~eppstein\/pix(?:\/.*)?$", url):
            return False
        
        # Don't allow the get request download links with format=txt
        if re.search(r"[?&]format=txt", url):
            return False

        # Don't allow WordPress login pages
        if "wp-login" in url:
            return False
        
        # Disallow a bunch of slides from zivs website
        if re.match(r"^https?://www\.ics\.uci\.edu/~ziv/.*\.htm$", url):
            return False  # disallow

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|mpg|py|h|cp|c|emacs|ppsx|lif|rle|nb|tsv|htm|odc|bib|pps)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
    except ValueError:
        print("ValueError for ", parsed)
        return False

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