import html
import re

def extract_company(web_content_lines):
    for line in web_content_lines:
        if '<meta property="article:author" content="' in line:
            name = line.split('content="')[1].split('"')[0]
            return re.sub(r'[<>:"/\\|?*]', '', name)
    return "Unknown Company"

def extract_dates(web_content_lines):
    publish = "Unknown"
    expiry = "Unknown"
    for line in web_content_lines:
        if 'published_time' in line:
            publish = line.split('content="')[1].split('"')[0]
        if 'expiration_time' in line:
            expiry = line.split('content="')[1].split('"')[0]
    return publish, expiry

def clean_html(text):
    return re.sub('<[^<]+?>', '', text).strip()

def extract_description(web_content_lines):
    markers = {
        'om jobbet</h2>': 'sv',
        'työpaikkakuvaus</h2>': 'fi',
        'job description</h2>': 'en'
    }
    
    capture = False
    lang = "unknown"
    lines = []
    div_depth = 0

    for line in web_content_lines:
        lower_line = line.lower()
        for marker, l in markers.items():
            if marker in lower_line:
                lang, capture, div_depth = l, True, 1
                continue
        
        if capture:
            lines.append(line)
            div_depth += line.count('<div')
            div_depth -= line.count('</div>')
            if div_depth <= 0:
                break
                
    raw_text = "\n".join(lines).replace("</p>", "\n").replace("<br>", "\n")
    return lang, clean_html(raw_text)

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    text = html.unescape(text)
    text = text.replace('\xa0', ' ')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
