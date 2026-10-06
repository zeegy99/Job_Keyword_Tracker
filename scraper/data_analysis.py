from main import fetch_company_jobs
from main import BOARD_TOKENS


from collections import Counter

c = Counter()
for token in BOARD_TOKENS:
    for job in fetch_company_jobs(token):
        for o in job.get("offices", []):
            if o['name'] == 'US':
                print('This job is in the US', job['location']['name'])

            c["OFFICE: " + str(o.get("location"))] += 1

print(c)