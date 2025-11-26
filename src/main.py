import os
import requests
import json

ohjelmisto_ala_url = "https://duunitori.fi/tyopaikat/ala/ohjelmointi-ja-ohjelmistokehitys"

def download_web_content(url: str) -> list:
    response = requests.get(url)
    return response.text.splitlines()

def get_job_listings(web_content) -> list:
    job_marker = 'href="/tyopaikat/tyo/'
    job_listings = []
    for line in web_content:
        if "Duunitori suosittelee" in line:
            return job_listings
        if job_marker in line and "lisaa_suosikkeihin" not in line:
            # find the href link between href=" and </a>
            start_index = line.find('href="') + len('href="')
            end_index = line.find('">', start_index)
            job_link = line[start_index:end_index]
            job_link = "https://duunitori.fi" + job_link
            job_listings.append(job_link)
    return job_listings

def is_id_submitted(id: str) -> bool:
    cwd = os.getcwd()
    output_dir = os.path.join(cwd, "output")
    output_dir = os.path.join(output_dir, "listings")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # id csv should have "id" and "score" columns
    id_file_path = os.path.join(output_dir, "id.csv")
    if not os.path.exists(id_file_path):
        with open(id_file_path, "w") as f:
            f.write("id,score\n")
    
    # if id not found, make entry, initialize score to -1, and return False
    with open(id_file_path, "r") as f:
        lines = f.read().splitlines()
        for line in lines[1:]:
            if line.startswith(id + ","):
                return line.endswith(",True")
    with open(id_file_path, "a") as f:
        f.write(f"{id},-1\n")
    return False

def handle_job_listing(job_url: str) -> None:
    print(f"Processing job listing: {job_url}", end="", flush=True)
    id = job_url.split("-")[-1]
    if is_id_submitted(id):
        print(" Already submitted. Skipping.")
        return {}

    web_content = download_web_content(job_url)
    company_name = job_listing_company_extraction(web_content)
    print(f"\tCompany: {company_name}\tForming AI summary:", end="", flush=True)
    job_description = job_listing_description_extraction(web_content)
    ai_summary = ask_ai(
        "Summarize the following job description with 200 words. \
        Do not list dates, or people, or contact info. \
        Do not format the output. \
        Include all technologies mentioned. Description starts:\n" \
        + job_description)
    print(" Job submission done. Evaluating:", end="", flush=True)
    evaluate_score = evaluate_job_listing(ai_summary=ai_summary)
    update_job_score(id, evaluate_score)
    save_company_json({
        "url": job_url,
        "company": company_name,
        "file_name": company_name.replace(" ", "_").lower() + f"_{id}.json",
        "description": job_description,
        "summary": ai_summary,
        "evaluation_score": evaluate_score
    })
    tailor_application({
        "url": job_url,
        "company": company_name,
        "file_name": company_name.replace(" ", "_").lower() + f"_{id}.json",
        "description": job_description,
        "summary": ai_summary,
        "evaluation_score": evaluate_score
    })
    print(" Done.")


def job_listing_company_extraction(web_content) -> str:
    for line in web_content:
        if 'window.reviewCompanyLink =' in line:
            start_index = line.find('/yritys/') + len('/yritys/')
            end_index = line.find('/', start_index)
            company_name = line[start_index:end_index]
            company_name = company_name.replace("-", " ").title()
            return company_name
    return "Unknown Company"

def job_listing_description_extraction(web_content) -> str:
    strip_html_tags = \
        ["<li>",
         "</li>",
         "<ul>",
         "</ul>",
         "<div>", 
         "</div>", 
         "<br>", 
         "<br/>", 
         "<br />", 
         "<p>", 
         "</p>", 
         "<strong>",
         "</strong>", 
         "<em>", 
         "</em>"]
    description_lines = []
    capture = False
    for line in web_content:
        if 'Työpaikkakuvaus' in line:
            capture = True
            continue
        if capture and "<div class" not in line:
            description_lines.append(line.strip())
        if '</div>' in line and capture:
            break
    result = "\n".join(description_lines)

    # Strip HTML tags
    for tag in strip_html_tags:
        result = result.replace(tag, "")

    # Remove <a href="...">...</a> links
    while '<a href="' in result:
        start_index = result.find('<a href="')
        end_index = result.find('">', start_index) + 2
        link_text_start = end_index
        link_text_end = result.find('</a>', link_text_start)
        link_text = result[link_text_start:link_text_end]
        result = result[:start_index] + link_text + result[link_text_end + 4:]

    # Replacs \u00e4 and \u00f6 with ä and ö
    result = result.replace("\u00e4", "ä").replace("\u00f6", "ö")

    # Trim excessive newlines
    result = "\n".join([line for line in result.splitlines() if line.strip() != ""])
    return result

def ask_ai(content: str) -> str:
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": "deepseek-r1:14b",
        "messages": [
            {"role": "user", "content": content}
        ]
    }

    response_text = ""
    with requests.post(url, json=payload, stream=True) as r:
        for line in r.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                # Streamed chunks contain "message" only when tokenized content arrives
                if "message" in data and "content" in data["message"]:
                    response_text += data["message"]["content"]
                    print(".", end="", flush=True)
    return response_text

def save_company_json(company_data: dict):
    cwd = os.getcwd()
    output_dir = os.path.join(cwd, "output")
    output_dir = os.path.join(output_dir, "listings")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    company_name = company_data["company"].replace(" ", "_").lower()
    company_dir = os.path.join(output_dir, company_name)
    if not os.path.exists(company_dir):
        os.makedirs(company_dir)
    file_path = os.path.join(company_dir, company_data["file_name"])
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(company_data, f, ensure_ascii=False, indent=4)

def evaluate_job_listing(ai_summary: str) -> int:
    with open("applicant/cv.txt", "r", encoding="utf-8") as f:
        cv_text = f.read()

    ai_response = ask_ai(
        "On a scale from 1 to 10, how well does the following job description \
        match the skills and experiences listed in the CV? \
        Respond with only a single integer number between 1 and 10. \
        Job description:\n" + ai_summary + "\n\nCV:\n" + cv_text)
    try:
        score = int(ai_response.strip())
        if 1 <= score <= 10:
            return score
        else:
            return 0
    except ValueError:
        return 0
    
def update_job_score(id: str, score: int):
    cwd = os.getcwd()
    output_dir = os.path.join(cwd, "output")
    output_dir = os.path.join(output_dir, "listings")
    id_file_path = os.path.join(output_dir, "id.csv")
    lines = []
    with open(id_file_path, "r") as f:
        lines = f.read().splitlines()
    with open(id_file_path, "w") as f:
        for line in lines:
            if line.startswith(id + ","):
                f.write(f"{id},{score}\n")
            else:
                f.write(line + "\n")

def tailor_application(company_info: dict) -> None:
    # if evaluation_score is less than 7, skip
    if company_info["evaluation_score"] < 7:
        print(f"Skipping {company_info['company']} due to low evaluation score ({company_info['evaluation_score']})")
        return ""
    # Load CV
    with open("applicant/cv.txt", "r", encoding="utf-8") as f:
        cv_text = f.read()
    print(f"Tailoring application for {company_info['company']}", end="", flush=True)
    ai_response = ask_ai(
        "Based on the company information and job description provided, \
        write a tailored job application letter. \
        Output the letter in Mardkdown format. \
        The letter should highlight relevant skills and experiences from the CV. \
        Use the following CV as reference for skills and experiences. \n\n\
        Company Information and Job Description:\n" + company_info["summary"] + \
        "\n\nCV:\n" + cv_text)
    save_application_letter(company_info["company"], ai_response)
    print(" Application letter saved.")

def save_application_letter(company_name: str, letter_content: str):
    cwd = os.getcwd()
    output_dir = os.path.join(cwd, "output")
    output_dir = os.path.join(output_dir, "applications")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_name = company_name.replace(" ", "_").lower() + "_application.md"
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(letter_content)

if __name__ == "__main__":
    web_content = download_web_content(ohjelmisto_ala_url)
    job_listings = get_job_listings(web_content)
    for job_listing in job_listings:
        handle_job_listing(job_listing)
    
