import re
import pandas as pd

def is_missing_name(name):
    if not isinstance(name, str): return True
    name = " ".join(name.split()).strip().lower()
    return name in ["", "nan", "none", "null", "unknown", "-", "na", "n/a", "not available"]

def is_name_similar_to_email(name, email):
    """
    Checks if the given name is likely associated with the given email.
    """
    if is_missing_name(name) or not email:
        return False

    name = str(name).lower()
    # Remove punctuation for matching
    name_clean = re.sub(r'[^\w\s]', ' ', name)
    name_parts = [p for p in name_clean.split() if len(p) > 2]

    local_part = email.split("@")[0].lower()

    if not name_parts:
        return False

    match_count = 0
    for np in name_parts:
        if np in local_part:
            match_count += 1
            
    return match_count >= 1

# Test cases
test_data = [
    # (Name, Email, Expected)
    ("Anders Søgaard", "soegaard@di.ku.dk", True), # 'soegaard' contains 'gaard'? No, wait. 
    ("Anders Søgaard", "anders@example.com", True),
    ("Anders Søgaard", "as@example.com", False), # too short
    ("Zhenhua Feng", "zhfeng@example.com", True), # 'feng' in 'zhfeng'
    ("Zhenhua Feng", "z.feng@surrey.ac.uk", True), # 'feng' in 'z.feng'
    ("John Smith", "jane.doe@example.com", False),
    ("Zhenhua Feng", "extracted_junk@example.com", False),
]

print("--- Testing Similarity Logic ---")
for name, email, expected in test_data:
    result = is_name_similar_to_email(name, email)
    print(f"Name: {name:15} | Email: {email:25} | Result: {result} | Expected: {expected} | {'PASS' if result == expected else 'FAIL'}")

# Testing deduplication logic
print("\n--- Testing Deduplication Logic ---")
rows = [
    {"Name": "Anders Søgaard", "Email": "anders@ku.dk", "Citations": 10},
    {"Name": "Anders Søgaard", "Email": "soegaard@ku.dk", "Citations": 13}, # This should be kept if citations are sorted
    {"Name": "Zhenhua Feng",   "Email": "z.feng@surrey.ac.uk", "Citations": 6},
]
df = pd.DataFrame(rows)
print("Before Dedup:")
print(df)

# Sort by citations descending, then drop duplicate names
df_dedup = df.sort_values("Citations", ascending=False).drop_duplicates("Name")
print("\nAfter Dedup (one email per name, highest citations):")
print(df_dedup)
