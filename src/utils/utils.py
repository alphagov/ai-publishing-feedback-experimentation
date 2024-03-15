import csv
import json


def jsonify_data(records: list, labelled=False):
    """
    Create json string from feedback
    :return: json string of feedback records
    """
    subs = []
    for i, item in enumerate(records):
        response_value = item["concatenated_response_value"]
        subs.append(
            {
                "id": item["feedback_record_id"],
                "feedback": response_value,
                "label": [item["labels"] if labelled else ""],
            }
        )

    return json.dumps(subs, indent=4)


def process_txt_file(file_obj):
    """Process a text file containing URLs, attempting to handle different encodings.

    Args:
        file_obj (UploadedFile): The text file object uploaded by the user.

    Returns:
        list: A list of URLs extracted from the file.
    """
    url_list = []
    encodings = ["utf-8", "latin-1", "iso-8859-1", "windows-1252"]

    for encoding in encodings:
        try:
            # Reset the file pointer to the beginning before trying to read
            file_obj.seek(0)
            # Read and decode the file content with the specified encoding
            content = file_obj.read().decode(encoding)
            url_list = [url.strip() for url in content.split(",")]
            break  # Break the loop if file is successfully read
        except UnicodeDecodeError:
            continue  # Try next encoding if an error occurs

    if not url_list:
        raise ValueError("Failed to decode the text file with the tried encodings.")

    return url_list


def process_csv_file(file_obj):
    """Process a CSV file containing URLs, attempting to handle different encodings.

    Args:
        file_obj (UploadedFile): The CSV file object uploaded by the user.

    Returns:
        list: A list of URLs extracted from the file.
    """
    url_list = []

    # Attempt to decode the file using different encodings
    for encoding in ["utf-8", "latin-1", "iso-8859-1", "windows-1252"]:
        try:
            # Reset the file pointer to the beginning before trying to read
            file_obj.seek(0)
            # Read and decode the file content with the specified encoding
            decoded_content = file_obj.read().decode(encoding)
            reader = csv.reader(decoded_content.splitlines())
            for row in reader:
                url_list.extend([url.strip() for url in row])
            break  # Exit the loop if reading the file succeeds
        except UnicodeDecodeError:
            continue  # Try the next encoding if an error occurs

    if not url_list:
        raise ValueError("Failed to decode the CSV file with the tried encodings.")

    return url_list
