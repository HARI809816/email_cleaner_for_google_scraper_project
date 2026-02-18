from main import is_junk_email, get_country

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
    "info@startup.io", # 'info' is not in our junk block list, though 'extract_name' might ignore it for name extraction, it's a valid email.
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
