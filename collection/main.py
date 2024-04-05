import subprocess


def main():
    subprocess.run(["python", "-u", "collection/create_collection.py", "-ev", "-rs"])
    subprocess.run(["python", "-u", "collection/delete_snapshots.py"])


if __name__ == "__main__":
    main()
