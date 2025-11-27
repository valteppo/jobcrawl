from net import Netparser
from ai import AI

if __name__ == "__main__":
    # Resource initialization is downloadilization
    netparser = Netparser(skip_download=True)
    ai = AI()

    # Run primary evaluation and immediately make letter.
    for job in netparser.listings():
        if job["evaluated"] == True:
            continue
        evaluated_job = ai.evaluate_job_listing(job=job)
        if evaluated_job["suitable"] == True:
            letter = ai.make_application_letter(job=job)
            ai.save_application_letter(letter=letter, listing_information=job)
        netparser.update_listing_information(evaluated_job)
