from net import Netparser
from ai import AI
from data import load_saved_listing_information, JobListing

if __name__ == "__main__":
    netparser = Netparser()
    ai = AI()

    netparser.form_listing_urls()
    while len(netparser.field_listing_urls) > 1:
        chunk = 5 if 5 <= len(netparser.field_listing_urls) else len(netparser.field_listing_urls)
        jobs = netparser.download_n(chunk)
        for job in jobs:
            if job.evaluated == False:
                ai.evaluate_job_listing(job)
            if job.ranking >= 7:
                ai.make_application_letter(job)
        print("CHUNK PROGRESSION", len(netparser.field_listing_urls))
