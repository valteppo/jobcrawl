import os
from data import JobListing
from netparser import Netparser
import ai

def load_cv():
    with open("cv/cv.md", "r") as f:
        return f.read()

def update():
    p = Netparser()
    p.update_database()

def evaluate():
    jobs = JobListing.load_all()
    cv = load_cv()
    for i, job in enumerate(jobs):
        if job.ranking < 0:
            res = ai.evaluate_job_listing(job,cv)
            print(f"{i+1}/{len(jobs)}: Eval: {res.ranking} - {res.url}")

def apply(ranking_minimum=7):
    jobs = [
        j for j in JobListing.load_all() 
        if j.ranking >= ranking_minimum 
        and (j.application is None or j.application == "")
    ]
    
    cv = load_cv()
    print(f"Generating letters for {len(jobs)} jobs...")
    for i, job in enumerate(jobs):
        ai.make_application_letter(job, cv)
        print(f"[{i+1}/{len(jobs)}] Saved application for {job.company} ({job.url_id})")

if __name__ == "__main__":
    apply()
    
