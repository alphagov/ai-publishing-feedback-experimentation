import random
from collections import Counter, defaultdict


def calculate_class_proportions(records: list):
    """
    Calculates the proportion of each class/label across all records.

    Args:
        records (list): A list of dictionaries, where each dictionary is a record and
                    contains a 'labels' key with its value being a list of labels.
    Returns:
        dict: A dictionary with labels as keys and their proportions as values.
    """
    label_counts = Counter()
    total_labels = 0

    for record in records:
        for label in record["labels"]:
            label_counts[label] += 1
            total_labels += 1

    class_proportions = {
        label: count / total_labels for label, count in label_counts.items()
    }
    return class_proportions


def get_random_sample(records: list, sample_size: int):
    """Generate a random sample of data from a list of dicts

    Args:
        records (list): A list of dictionaries, where each dictionary is a record and
                    contains a 'labels' key with its value being a list of labels.
        sample_size (int): desired sample size

    Returns:
        list: list of dicts
    """

    # Sample the dictionaries
    sampled_dicts = random.sample(records, sample_size)

    return sampled_dicts


def get_stratified_sample(
    records, total_sample_size=20, id_key="feedback_record_id", label_key="labels"
):
    """
    Performs simplified stratified sampling from a list of records. It aims to return a list
    of records close to the specified total sample size while approximating class proportions
    without including any duplicates.

    This function first calculates the proportional sample size for each label based on the
    occurrences in the input records. It then samples records for each label, ensuring no
    record is included more than once. If the sum of proportional samples exceeds the total
    sample size, it reduces the sample size for the most represented label. If the final
    sampled records are less than the total sample size, it fills the gap with random samples
    from the remaining records.

    Args:
        records (list of dict): A list where each dict is a record containing at least a 'labels'
                                key with its value being a list of labels and an 'id' key.
        total_sample_size (int): The desired total number of records to sample.
        id_key (str): The name of the key containing the unique id. Required to ensure
                        there are no duplicates in the sample.
        label_key (str): The name of the key containing the labels.

    Returns:
        list of dict: A list of sampled records, approximately matching the total sample size,
                      without any duplicates.

    """
    # Count the occurrences of each label
    label_counts = Counter(label for record in records for label in record[label_key])
    total_labels = sum(label_counts.values())

    # Determine proportional sample sizes for each label
    label_sample_sizes = {
        label: max(1, int((count / total_labels) * total_sample_size))
        for label, count in label_counts.items()
    }

    # Adjust sample sizes if the sum exceeds total_sample_size
    while sum(label_sample_sizes.values()) > total_sample_size:
        max_label = max(label_sample_sizes, key=label_sample_sizes.get)
        label_sample_sizes[max_label] -= 1

    grouped_records = defaultdict(list)
    for record in records:
        for label in record[label_key]:
            grouped_records[label].append(record)

    sampled_records = []
    sampled_ids = set()  # Track sampled record IDs to prevent duplicates

    for label, sample_size in label_sample_sizes.items():
        available_records = [
            record
            for record in grouped_records[label]
            if record[id_key] not in sampled_ids
        ]
        samples = random.sample(
            available_records, min(sample_size, len(available_records))
        )
        sampled_records.extend(samples)
        sampled_ids.update(record[id_key] for record in samples)

    # Adjust the final sampled records to meet the total_sample_size - required due to multi-labels
    if len(sampled_records) > total_sample_size:
        sampled_records = random.sample(sampled_records, total_sample_size)
    elif len(sampled_records) < total_sample_size:
        remaining_records = [
            record for record in records if record[id_key] not in sampled_ids
        ]
        if remaining_records:
            additional_samples = random.sample(
                remaining_records,
                min(total_sample_size - len(sampled_records), len(remaining_records)),
            )
            sampled_records.extend(additional_samples)

    return sampled_records
