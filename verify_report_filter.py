from main import is_junk_email

test_emails = [
    "report@google.com",
    "john.report.smith@gmail.com",
    "daily.report@company.org",
    "report.user@research.edu",
    "valid.user@google.com"
]

print("--- Verifying report filter ---")
for email in test_emails:
    is_junk = is_junk_email(email)
    status = "FILTERED" if is_junk else "ALLOWED"
    print(f"[{status}] {email}")

# Double check specifically for the user's requested email
if is_junk_email("report@google.com"):
    print("\nSUCCESS: 'report@google.com' is correctly filtered.")
else:
    print("\nFAILURE: 'report@google.com' is NOT filtered.")
