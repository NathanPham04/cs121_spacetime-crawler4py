from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler

# For debugging and report purposes
import json
import scraper


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    debug = True
    try:
        main(args.config_file, args.restart)
    except:
        if debug == True:
            with open("websites.json", "w") as f:
                json.dump(scraper.websites_as_json, f, indent=4)
    else:
        if debug == True:
            with open("websites.json", "w") as f:
                json.dump(scraper.websites_as_json, f, indent=4)

    # Crawler Statistics
    word_frequencies = [(freq, word) for word, freq in scraper.word_frequency_map.items()]
    top_freq_words = sorted(word_frequencies, reverse=True)
    top_words = [(word, freq) for freq, word in top_freq_words]
    all_subdomains = sorted(scraper.subdomain_counts.keys())
    subdomain_counts = [(subdomain, scraper.subdomain_counts[subdomain]) for subdomain in all_subdomains]


    with open("stats.txt", "w") as f:
        f.write("-------------------Crawler Statistics-------------------\n")
        f.write(f"Total pages: {str(len(scraper.pages_seen_set))}\n")
        f.write(f"Longest page: {scraper.longest_page_url} ({str(scraper.longest_page_len)} words)\n")
        f.write("Most common words:\n")
        for word, count in top_words[:50]:
            f.write(f"\t{word}, {str(count)}\n")
        f.write("Subdomains:\n")
        for subdomain, count in subdomain_counts:
            f.write(f"\t{subdomain}, {str(count)}\n")
        
        f.write("\n\n\n")
        f.write("--------Additional Statistics-------------------\n")
        f.write(f"Exact duplicate pages skipped: {scraper.num_duplicate_pages}\n")
        f.write(f"Near duplicate pages skipped: {scraper.num_near_duplicate_pages}\n")

    with open("top_words.txt", "w") as f:
        f.write(str(top_words))