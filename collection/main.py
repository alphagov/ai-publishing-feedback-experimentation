import subprocess


def main():
    subprocess.run(["python", "collection/create_collection.py"])
    subprocess.run(["python", "collection/get_metadata_for_filters.py"])


if __name__ == "__main__":
    main()
