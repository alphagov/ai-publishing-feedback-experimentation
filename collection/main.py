import argparse
import subprocess


def parse_arguments():
    """
    Parses command line arguments.

    Returns:
        argparse.Namespace: The namespace containing the arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run collection scripts with optional flags."
    )
    # Add arg for populate from snapshot or from BigQuery
    parser.add_argument(
        "-ev",
        "--eval-only",
        action="store_true",  # This will set the value to True when the flag is used
        default=False,  # Default value is False
        dest="eval_only",
        help="Set to True to populate only the evaluation collection. Defaults to False.",
    )

    # Add arg for populate from snapshot or from BigQuery
    parser.add_argument(
        "-rs",
        "--restore-from-snapshot",
        action="store_true",  # This will set the value to True when the flag is used
        default=False,  # Default value is False
        dest="restore_from_snapshot",
        help="Set to True to enable restoring from a snapshot. Defaults to False.",
    )
    return parser.parse_args()


def main():
    """
    Main function that runs scripts with optional command line arguments.
    """
    args = parse_arguments()

    # Command for create_collection.py
    create_collection_cmd = ["python", "-u", "collection/create_collection.py"]
    delete_snapshots_cmd = ["python", "-u", "collection/delete_snapshots.py"]

    for cmd in [create_collection_cmd, delete_snapshots_cmd]:
        if args.restore_from_snapshot:
            cmd.append("-rs")
        if args.eval_only:
            cmd.append("-ev")

    # Execute the commands
    subprocess.run(create_collection_cmd)
    subprocess.run(delete_snapshots_cmd)


if __name__ == "__main__":
    main()
