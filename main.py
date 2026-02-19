from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import re
import os
import uuid
import tempfile
from dotenv import load_dotenv

load_dotenv()

# ======================
# APP SETUP
# ======================

app = FastAPI()

UPLOAD_DIR = tempfile.gettempdir()
# os.makedirs(UPLOAD_DIR, exist_ok=True) # System temp dir always exists

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# ======================
# HELPERS
# ======================

def clean_name(value):
    if pd.isna(value):
        return ""
    cleaned = " ".join(str(value).split()).strip()
    cleaned = re.sub(r'[\u00a0\u200b\u200c\u200d\ufeff\u2028\u2029]', '', cleaned)
    return cleaned

def is_missing_name(name):
    name = " ".join(name.split()).strip().lower()
    return name in ["", "nan", "none", "null", "unknown", "-", "na", "n/a", "not available"]

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
        "email", "contact", "domain", "here",
        # Hyphenated/dot-separated placeholder patterns
        "first-name", "last-name", "first.last", "first.name", "last.name",
        # Generic role/action words that appear as usernames
        "working", "postdoc", "professor", "researcher",
    ]

    if any(word in local_part for word in block_words):
        return True

    # 2. Token-level placeholder check: split on separators and look for
    #    both 'first' and 'last' tokens (e.g. first.last@, first-last@)
    tokens = re.split(r'[.\-_+]', local_part)
    if "first" in tokens and "last" in tokens:
        return True
    # Single-token generic words used as name placeholders
    if tokens == ["working"] or tokens == ["name"] or tokens == ["user"]:
        return True

    # 3. Specific Starts/Ends checks for "name"
    if local_part.startswith("name.") or local_part.endswith(".name") or ".name." in local_part:
        return True

    # 4. Starting with domain patterns (common scraping error)
    if local_part.startswith("gmail.com") or local_part.startswith("yahoo.com") or local_part.startswith("hotmail.com"):
        return True

    # 5. Length Heuristic (Sentences often > 50 chars)
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

def extract_name_from_email(email):
    """
    Strict name extraction — requires at least 2 valid word parts.
    e.g. john.smith@x.com → John Smith
         guohao@x.com     → (empty, single token)
    """
    STOPWORDS = {
        "admin", "info", "support", "contact", "mail", "email",
        "noreply", "no-reply", "help", "team", "office", "phd",
        "lab", "dept", "university", "research", "group", "center",
        "cs", "eng", "sci", "edu", "web", "service", "services",
        # Placeholder / generic words
        "first", "last", "name", "working", "user", "postdoc",
    }
    try:
        username = email.split("@")[0].lower()
        parts = re.split(r'[.\-_+]', username)
        valid_parts = []
        for part in parts:
            if not part:
                continue
            if part.isdigit():
                continue
            if any(c.isdigit() for c in part):
                continue
            if len(part) <= 2:
                continue
            if part in STOPWORDS:
                continue
            valid_parts.append(part.capitalize())
        if len(valid_parts) < 2:
            return ""
        return " ".join(valid_parts)
    except Exception:
        return ""


def extract_name_from_email_relaxed(email):
    """
    Relaxed name extraction — accepts a single valid word as a name.
    Used for Sheet 4 on emails that already failed the strict check.
    e.g. guohao@x.com  → Guohao
         errolf@x.com  → Errolf
         cchen151@x.com → (empty, contains digits)
         admin@x.com   → (empty, stopword)
    """
    STOPWORDS = {
        "admin", "info", "support", "contact", "mail", "email",
        "noreply", "no-reply", "help", "team", "office", "phd",
        "lab", "dept", "university", "research", "group", "center",
        "cs", "eng", "sci", "edu", "web", "service", "services",
        # Placeholder / generic words
        "first", "last", "name", "working", "user", "postdoc",
    }
    try:
        username = email.split("@")[0].lower()
        parts = re.split(r'[.\-_+]', username)
        valid_parts = []
        for part in parts:
            if not part:
                continue
            if part.isdigit():
                continue
            if any(c.isdigit() for c in part):
                continue
            if len(part) <= 2:
                continue
            if part in STOPWORDS:
                continue
            valid_parts.append(part.capitalize())
        # Relaxed: accept even a single valid word
        if len(valid_parts) < 1:
            return ""
        return " ".join(valid_parts)
    except Exception:
        return ""


# ======================
# API ENDPOINT
# ======================

@app.post("/process-excel/")
async def process_excel(file: UploadFile = File(...)):

    uid = str(uuid.uuid4())
    input_path = f"{UPLOAD_DIR}/{uid}_input.xlsx"
    output_path = f"{UPLOAD_DIR}/{uid}_output.xlsx"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    df = pd.read_excel(input_path)

    all_rows = []
    similar_rows = []
    extracted_rows = []

    for _, row in df.iterrows():

        original_name = clean_name(row["Name"])
        citations     = row["Citations"]
        name_missing  = is_missing_name(original_name)

        # Parse emails
        all_emails = []
        if pd.notna(row["All Emails"]):
            all_emails = [e.strip() for e in str(row["All Emails"]).split(",")]

        similar_emails = set()
        if pd.notna(row["Similar Emails"]):
            similar_emails = {e.strip() for e in str(row["Similar Emails"]).split(",")}

        # Only valid emails
        valid_emails = [e for e in all_emails if e and EMAIL_REGEX.match(e) and not is_junk_email(e)]

        # First email keeps the real name; extra emails get "None" in Sheet 1
        first_email = valid_emails[0] if valid_emails else None

        for email in valid_emails:

            domain     = email.split("@")[1]
            country    = get_country(domain)
            is_similar = email in similar_emails
            is_extra   = (email != first_email)

            # -------- Sheet 1 --------
            sheet1_name = original_name if not is_extra else "None"

            all_rows.append({
                "Name":      sheet1_name,
                "Email":     email,
                "Domain":    domain,
                "Country":   country,
                "Citations": citations
            })

            # -------- Sheet 2 --------
            if is_similar:
                similar_rows.append({
                    "Name":      original_name,
                    "Email":     email,
                    "Domain":    domain,
                    "Country":   country,
                    "Citations": citations
                })

            # -------- Sheet 3 (Python extraction when name missing or extra email) --------
            if (name_missing or is_extra) and not is_similar:
                extracted_name = extract_name_from_email(email)  # "" if not found

                extracted_rows.append({
                    "Name":      extracted_name,   # empty string if no name found
                    "Email":     email,
                    "Domain":    domain,
                    "Country":   country,
                    "Citations": citations
                })

    columns = ["Name", "Email", "Domain", "Country", "Citations"]

    all_df       = pd.DataFrame(all_rows,       columns=columns).drop_duplicates("Email")
    similar_df   = pd.DataFrame(similar_rows,   columns=columns).drop_duplicates("Email")
    extracted_df = pd.DataFrame(extracted_rows, columns=columns).drop_duplicates("Email")

    all_df       = all_df.sort_values("Citations", ascending=False)
    similar_df   = similar_df.sort_values("Citations", ascending=False)
    extracted_df = extracted_df.sort_values("Citations", ascending=False)

    # -------- Sheet 4: Email_Name_Extracted --------
    # Take blank-name rows from Name_Processed_Emails and try to infer a name from the email address.
    # Only keep rows where extraction succeeds (non-empty result).
    email_name_rows = []
    blank_name_mask = extracted_df["Name"] == ""
    for _, row in extracted_df[blank_name_mask].iterrows():
        # Use the relaxed extractor — the strict one already returned "" for these emails
        inferred = extract_name_from_email_relaxed(row["Email"])
        if inferred:
            r = row.to_dict()
            r["Name"] = inferred
            email_name_rows.append(r)

    email_name_df = (
        pd.DataFrame(email_name_rows, columns=columns)
        .drop_duplicates("Email")
        .sort_values("Citations", ascending=False)
        if email_name_rows
        else pd.DataFrame(columns=columns)
    )

    # -------- Sheet 5: Final_Combined --------
    # Merge: Similar_Name_Emails + named rows from Name_Processed_Emails + Email_Name_Extracted
    named_extracted_df = extracted_df[extracted_df["Name"] != ""].copy()

    final_combined_df = (
        pd.concat([similar_df, named_extracted_df, email_name_df], ignore_index=True)
        .drop_duplicates("Email")
        .sort_values("Citations", ascending=False)
        .reset_index(drop=True)
    )

    # -------- Summary Statistics --------
    s1_count       = len(all_df)
    s2_count       = len(similar_df)
    s3_named_count = len(extracted_df[extracted_df["Name"] != ""])
    s3_blank_count = len(extracted_df[extracted_df["Name"] == ""])
    s4_count       = len(email_name_df)
    s5_count       = len(final_combined_df)

    summary_data = [
        {"Metric": "Sheet 2 Total (All Clean)",        "Count": s1_count},
        {"Metric": "Sheet 3 (Similar Name Emails)",    "Count": s2_count},
        {"Metric": "Sheet 4 (Name Found)",             "Count": s3_named_count},
        {"Metric": "Sheet 4 (Name Blank)",             "Count": s3_blank_count},
        {"Metric": "Sheet 5 (Email Name Extracted)",   "Count": s4_count},
        {"Metric": "Sheet 6 Final Combined",           "Count": s5_count},
    ]
    summary_df = pd.DataFrame(summary_data)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer,        sheet_name="Summary",               index=False)
        all_df.to_excel(writer,            sheet_name="All_Clean_Emails",      index=False)
        similar_df.to_excel(writer,        sheet_name="Similar_Name_Emails",   index=False)
        extracted_df.to_excel(writer,      sheet_name="Name_Processed_Emails", index=False)
        email_name_df.to_excel(writer,     sheet_name="Email_Name_Extracted",  index=False)
        final_combined_df.to_excel(writer, sheet_name="Final_Combined",        index=False)

    return JSONResponse({
        "uid": uid,
        "stats": summary_data
    })

@app.get("/download/{uid}")
async def download_file(uid: str):
    file_path = f"{UPLOAD_DIR}/{uid}_output.xlsx"
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            filename="cleaned_emails.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return JSONResponse({"error": "File not found"}, status_code=404)
    