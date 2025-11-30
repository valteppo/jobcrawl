from net import Netparser
from ai import AI
from data import load_saved_listing_information, JobListing

if __name__ == "__main__":
    netparser = Netparser()
    ai = AI()

    netparser.form_listing_urls()
    netparser.download_n(5)
    jobs = load_saved_listing_information()
    for job in jobs:
        if job.evaluated == False:
            ai.evaluate_job_listing(job)
        if job.application == "":
            ai.make_application_letter(job)
