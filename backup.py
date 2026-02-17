# from fastapi import FastAPI, UploadFile, File
# from fastapi.responses import FileResponse
# import pandas as pd
# import re
# import os
# import uuid
# from google import genai
# from dotenv import load_dotenv

# load_dotenv()

# # ======================
# # APP SETUP
# # ======================

# app = FastAPI()

# UPLOAD_DIR = "temp"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# # Configure Gemini
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     print("Warning: GEMINI_API_KEY not found in environment variables.")

# # Initialize the client (newer SDK)
# client = genai.Client(api_key=api_key)

# SYSTEM_PROMPT = """You are a data extraction engine.

# Extract a person's name ONLY if it clearly appears inside the email username.

# RULES:
# - Use only visible text
# - Never guess or expand
# - Never invent surnames
# - Never correct spelling
# - If unsure return empty

# ALLOWED:
# mohammad.ghadri@email.com -> Mohammad Ghadri
# binyuan@company.com -> Binyuan
# xinhuang@uni.edu -> Xinhuang

# NOT ALLOWED:
# johnsbenny@ -> blank
# random123@ -> blank
# mostam@ -> blank

# Return only the name or empty string.
# """


# EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# # ======================
# # STRICT PROMPT
# # ======================



# def llm_extract_name(email: str) -> str:
#     try:
#         response = client.models.generate_content(
#             model="gemini-1.5-flash",
#             contents=f"Email: {email}\nExtract name:",
#             config=genai.types.GenerateContentConfig(
#                 system_instruction=SYSTEM_PROMPT,
#                 temperature=0,
#                 top_p=0.95,
#                 top_k=40,
#                 max_output_tokens=20,
#                 response_mime_type="text/plain",
#             )
#         )
#         return response.text.strip()
#     except Exception as e:
#         print(f"Error extracting name for {email}: {e}")
#         return ""

# # ======================
# # API ENDPOINT
# # ======================

# @app.post("/process-excel/")
# async def process_excel(file: UploadFile = File(...)):

#     uid = str(uuid.uuid4())
#     input_path = f"{UPLOAD_DIR}/{uid}_input.xlsx"
#     output_path = f"{UPLOAD_DIR}/{uid}_output.xlsx"

#     with open(input_path, "wb") as f:
#         f.write(await file.read())

#     df = pd.read_excel(input_path)

#     rows = []
#     similar_rows = []

#     for _, row in df.iterrows():

#         name = row["Name"]
#         citations = row["Citations"]

#         # All Emails
#         all_emails = []
#         if pd.notna(row["All Emails"]):
#             all_emails = [e.strip().lower() for e in str(row["All Emails"]).split(",")]

#         # Similar Emails (trusted)
#         similar_emails = set()
#         if pd.notna(row["Similar Emails"]):
#             similar_emails = {e.strip().lower() for e in str(row["Similar Emails"]).split(",")}

#         for email in all_emails:

#             if not email or not EMAIL_REGEX.match(email):
#                 continue

#             domain = email.split("@")[1]
#             is_similar = email in similar_emails

#             if is_similar and pd.notna(name):
#                 final_name = name
#             else:
#                 final_name = llm_extract_name(email)

#             rows.append({
#                 "Name": final_name,
#                 "Email": email,
#                 "Domain": domain,
#                 "Citations": citations
#             })

#             if is_similar:
#                 similar_rows.append({
#                     "Name": name,
#                     "Email": email,
#                     "Domain": domain,
#                     "Citations": citations
#                 })

#     all_df = pd.DataFrame(rows).drop_duplicates(subset="Email")
#     similar_df = pd.DataFrame(similar_rows).drop_duplicates(subset="Email")

#     # visual cleanup
#     all_df["Name"] = all_df["Name"].mask(all_df["Name"].duplicated())

#     all_df = all_df.sort_values("Citations", ascending=False)
#     similar_df = similar_df.sort_values("Citations", ascending=False)

#     with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
#         all_df.to_excel(writer, sheet_name="All_Clean_Emails", index=False)
#         similar_df.to_excel(writer, sheet_name="Similar_Name_Emails", index=False)

#     return FileResponse(
#         output_path,
#         filename="cleaned_emails.xlsx",
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import re
import os
import uuid
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# ======================
# APP SETUP
# ======================

app = FastAPI()

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ======================
# GEMINI SETUP
# ======================

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY missing")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """You are a strict name extraction engine.

Extract a person's name ONLY if it clearly appears inside the email username.

Rules:
- No guessing
- No fixing spelling
- No invention
- If unclear return empty

Examples:
mohammad.ghadri@email.com -> Mohammad Ghadri
binyuan@company.com -> Binyuan
random123@ -> empty

Return only name or empty.
"""

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# ======================
# HELPERS
# ======================

def clean_name(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def is_missing_name(name):
    return name.strip().lower() in ["", "nan", "none", "null", "unknown", "-", "na"]

def get_country(domain):
    domain = domain.lower()
    tld_map = {
        ".ac.uk": "United Kingdom",
        ".uk": "United Kingdom",
        ".edu.au": "Australia",
        ".au": "Australia",
        ".cn": "China",
        ".hk": "Hong Kong",
        ".tw": "Taiwan",
        ".de": "Germany",
        ".fr": "France",
        ".edu": "USA (Academic)",
        ".jp": "Japan",
        ".kr": "South Korea",
        ".ca": "Canada",
        ".in": "India",
        ".sg": "Singapore",
    }
    for tld in sorted(tld_map, key=len, reverse=True):
        if domain.endswith(tld):
            return tld_map[tld]
    return "Other/Global"

def llm_extract_name(email):
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nEmail: {email}"
        response = model.generate_content(prompt)
        if not response.text:
            return ""
        name = response.text.strip()
        if len(name) > 40 or any(c.isdigit() for c in name):
            return ""
        print("AI:", email, "->", name)
        return name
    except Exception as e:
        print("Gemini error:", e)
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
        citations = row["Citations"]

        all_emails = []
        if pd.notna(row["All Emails"]):
            all_emails = [e.strip() for e in str(row["All Emails"]).split(",")]

        similar_emails = set()
        if pd.notna(row["Similar Emails"]):
            similar_emails = {e.strip() for e in str(row["Similar Emails"]).split(",")}

        for email in all_emails:

            if not email or not EMAIL_REGEX.match(email):
                continue

            domain = email.split("@")[1]
            country = get_country(domain)
            is_similar = email in similar_emails

            # -------- Sheet 1 --------
            all_rows.append({
                "Name": original_name,
                "Email": email,
                "Domain": domain,
                "Country": country,
                "Citations": citations
            })

            # -------- Sheet 2 --------
            if is_similar:
                similar_rows.append({
                    "Name": original_name,
                    "Email": email,
                    "Domain": domain,
                    "Country": country,
                    "Citations": citations
                })

            # -------- Sheet 3 (AI processing) --------
            if is_missing_name(original_name):

                extracted_name = llm_extract_name(email)

                extracted_rows.append({
                    "Name": extracted_name,   # empty or filled
                    "Email": email,
                    "Domain": domain,
                    "Country": country,
                    "Citations": citations
                })

    columns = ["Name", "Email", "Domain", "Country", "Citations"]

    all_df = pd.DataFrame(all_rows, columns=columns).drop_duplicates("Email")
    similar_df = pd.DataFrame(similar_rows, columns=columns).drop_duplicates("Email")
    extracted_df = pd.DataFrame(extracted_rows, columns=columns).drop_duplicates("Email")

    all_df["Name"] = all_df["Name"].mask(all_df["Name"].duplicated())

    all_df = all_df.sort_values("Citations", ascending=False)
    similar_df = similar_df.sort_values("Citations", ascending=False)
    extracted_df = extracted_df.sort_values("Citations", ascending=False)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        all_df.to_excel(writer, sheet_name="All_Clean_Emails", index=False)
        similar_df.to_excel(writer, sheet_name="Similar_Name_Emails", index=False)
        extracted_df.to_excel(writer, sheet_name="AI_Processed_Emails", index=False)

    return FileResponse(
        output_path,
        filename="cleaned_emails.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
