import requests
import csv
import time
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("DUNE_API_KEY")

QUERY_ID = "6246979"
LIMIT = 1000
offset = 0

output_file = "wallet_dataset.csv"
first_page = True

print("Downloading full dataset from Dune…")

while True:
    url = f"https://api.dune.com/api/v1/query/{QUERY_ID}/results/csv?limit={LIMIT}&offset={offset}"
    headers = {"X-Dune-API-Key": API_KEY}

    print(f"Fetching offset {offset} ...")

    try:
        r = requests.get(url, headers=headers, timeout=40)

    except requests.exceptions.Timeout:
        print("Timeout. Retrying in 5 seconds…")
        time.sleep(5)
        continue

    except Exception as e:
        print(f"Network error: {e}. Retrying…")
        time.sleep(5)
        continue

    if len(r.text.strip()) == 0 or r.status_code != 200:
        print("No more rows or bad response. Finished.")
        break

    lines = r.text.splitlines()
    if len(lines) <= 1:
        print("Reached the last partial page. Stopping.")
        break

    mode = 'w' if first_page else 'a'
    with open(output_file, mode, newline='') as f:
        writer = csv.writer(f)
        for i, line in enumerate(lines):
            if not first_page and i == 0:
                continue
            writer.writerow(line.split(','))

    first_page = False
    offset += LIMIT
    time.sleep(0.3)

print(f"Saved CSV to: {output_file}")
