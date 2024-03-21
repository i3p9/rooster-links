import csv
import requests
import subprocess
from datetime import datetime

SHOW_FILTER = None
CHANNEL_FILTER = None


def load_csv(filename, show_filter=None, channel_filter=None) -> list:
    data = []
    with open(filename, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if (show_filter is None or row["series"] == show_filter) and (
                channel_filter is None or row["channel"] == channel_filter
            ):
                data.append(row)
    return data


def format_filename(show_filter, channel_filter) -> str:
    filename = "missing"
    if show_filter:
        filename += f"_{show_filter}"
    if channel_filter:
        filename += f"_{channel_filter}"
    filename += ".txt"
    return filename


def process_chunk(chunk):
    archive_ids = [row["archive_id"] for row in chunk]
    or_conditions = "+OR+".join(id for id in archive_ids)
    url = f"https://archive.org/advancedsearch.php?q=identifier:({or_conditions})&fl[]=identifier&sort[]=&sort[]=&sort[]=&rows=300&page=1&output=json&save=yes"
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        found_ids = [doc["identifier"] for doc in result["response"]["docs"]]
        missing_ids = [id for id in archive_ids if id not in found_ids]
        return missing_ids
    else:
        return []


def main(filename):
    data = load_csv(filename, show_filter=SHOW_FILTER, channel_filter=CHANNEL_FILTER)
    missing_links = []
    chunk_size = 250
    total_chunks = len(data) // chunk_size + (1 if len(data) % chunk_size != 0 else 0)
    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        chunk_number = i // chunk_size + 1
        missing_ids = process_chunk(chunk)
        missing_links.extend(
            [row["link"] for row in chunk if row["archive_id"] in missing_ids]
        )

    total_links = len(data)
    present_links = total_links - len(missing_links)
    last_ran = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n## Total links: {total_links}\n")
    print(f"## Links present in Archive.org: {present_links}\n")
    print(f"## Missing links: {len(missing_links)}\n")
    print(f"## Percentage Done: {(present_links/total_links)*100} %\n")
    print(f"\nLast updated: {last_ran}")

    return missing_links


if __name__ == "__main__":
    csv_filename = "all_episodes_mar22.csv"
    missing_links = main(csv_filename)

    filename = "output.txt"
    with open(f"{filename}", "w") as file:
        for link in missing_links:
            file.write(link + "\n")

    subprocess.run(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ]
    )
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "add", filename])
    subprocess.run(["git", "commit", "-m", "Update misisng output txt"])
    subprocess.run(["git", "push"])
