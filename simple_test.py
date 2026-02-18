
def is_junk_email(email):
    """
    Filters out garbage emails containing sentences, placeholders, or instruction text.
    Returns True if email is considered junk.
    """
    if not email:
        return True
        
    local_part = email.split("@")[0].lower()
    
    # 1. Block Words (Instructions / Sentences / Common Placeholders)
    block_words = [
        "correspondence", "pleasesend", "workconducted", "workdone", 
        "writtenwhile", "interning", "currentaddress", "author", 
        "reprint", "address", "published", "submitted", "preprint",
        "firstname", "lastname", "surname", "secondname", 
        "yourname", "username", "user.name", "example", 
        "email", "contact", "domain", "here"
    ]
    
    if any(word in local_part for word in block_words):
        return True

    # 2. Specific Starts/Ends checks for "name"
    if local_part.startswith("name.") or local_part.endswith(".name") or ".name." in local_part:
        return True

    # 3. Starting with domain patterns (common scraping error)
    if local_part.startswith("gmail.com") or local_part.startswith("yahoo.com") or local_part.startswith("hotmail.com"):
        return True

    # 4. Length Heuristic (Sentences often > 50 chars)
    if len(local_part) > 50:
        return True
        
    return False

def get_country(domain):
    domain = domain.lower()
    # Ordered by length to match specific subdomains first (e.g. .co.uk before .uk)
    tld_map = {
        ".ac.uk": "United Kingdom", ".co.uk": "United Kingdom", ".uk": "United Kingdom",
        ".edu.au": "Australia", ".com.au": "Australia", ".net.au": "Australia", ".au": "Australia",
        ".edu.cn": "China", ".com.cn": "China", ".cn": "China",
        ".edu.hk": "Hong Kong", ".hk": "Hong Kong",
        ".edu.tw": "Taiwan", ".tw": "Taiwan",
        ".de": "Germany",
        ".fr": "France",
        ".edu": "USA (Academic)",
        ".jp": "Japan", ".ac.jp": "Japan",
        ".kr": "South Korea", ".ac.kr": "South Korea",
        ".ca": "Canada",
        ".in": "India", ".ac.in": "India", ".co.in": "India",
        ".sg": "Singapore", ".com.sg": "Singapore",
        ".it": "Italy",
        ".es": "Spain",
        ".nl": "Netherlands",
        ".ru": "Russia",
        ".br": "Brazil",
        ".pk": "Pakistan",
        ".se": "Sweden",
        ".no": "Norway",
        ".dk": "Denmark",
        ".fi": "Finland",
        ".pl": "Poland",
        ".ch": "Switzerland",
        ".at": "Austria",
        ".be": "Belgium",
        ".cz": "Czech Republic",
        ".tr": "Turkey",
        ".gr": "Greece",
        ".il": "Israel", ".ac.il": "Israel",
        ".za": "South Africa", ".ac.za": "South Africa",
        ".mx": "Mexico",
        ".ar": "Argentina",
        ".cl": "Chile",
        ".co": "Colombia",
        ".my": "Malaysia",
        ".id": "Indonesia",
        ".th": "Thailand",
        ".vn": "Vietnam",
        ".ph": "Philippines",
        ".nz": "New Zealand",
        ".ie": "Ireland",
        ".pt": "Portugal",
        ".hu": "Hungary",
        ".ro": "Romania",
        ".ua": "Ukraine",
        ".ir": "Iran",
        ".eg": "Egypt",
        ".sa": "Saudi Arabia",
        ".ae": "UAE",
    }
    for tld in sorted(tld_map, key=len, reverse=True):
        if domain.endswith(tld):
            return tld_map[tld]
    return "Other/Global"

# Test Data
bad_emails = [
    "ApolloResearch.Emailcorrespondencetomarius@apolloresearch.ai",
    "OpenAI.Emailcorrespondencetojenny@openai.com",
    "Pleasesendcorrespondencetogemini-report@google.com",
    "Workconductedwhilethefirstauthorwasanintern@Booking.com",
    "firstname.lastname@lne.fr",
    "firstname.secondname@cl.cam.ac.uk",
    "name.surname@unibo.it",
    "Germany.firstname.surname@tum.de",
    "gmail.comnatsuhadder001@gmail.com"
]

good_emails = [
    "j.doe@univ.edu",
    "jane.smith@company.com",
    "researcher@lab.ac.uk"
]

print("--- Testing Junk Filter ---")
for email in bad_emails:
    is_junk = is_junk_email(email)
    print(f"[{'FILTERED' if is_junk else 'ALLOWED'}] {email}")

print("\n--- Testing Good Emails ---")
for email in good_emails:
    is_junk = is_junk_email(email)
    print(f"[{'FILTERED' if is_junk else 'ALLOWED'}] {email}")

print("\n--- Testing Country ---")
domains = [
    "test.pk", "test.br", "test.ru", "test.ac.uk", "test.edu.au", "test.unknown"
]
for d in domains:
    print(f"{d} -> {get_country(d)}")
