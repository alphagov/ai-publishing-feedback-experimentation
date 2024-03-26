import subprocess


def main():
    subprocess.run(["python", "-u", "collection/create_collection.py"])
    subprocess.run(["python", "-u", "collection/get_metadata_for_filters.py"])


if __name__ == "__main__":
    main()
