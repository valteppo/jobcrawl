import os
from net import Netparser
from data import load_saved_listing_information, JobListing

AI_AGENT_LIGHT = os.environ.get('AI_AGENT_LIGHT')
AI_AGENT_HEAVY= os.environ.get('AI_AGENT_HEAVY')

if __name__ == "__main__":
    netparser = Netparser()
    urls = netparser.form_listing_urls()
    print(len(urls))
