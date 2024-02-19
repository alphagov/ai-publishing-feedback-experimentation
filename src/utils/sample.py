import pandas as pd


def stratified_sample_with_underrepresented_bias(
    df: pd.DataFrame, n: int, underrepresented_bias_frac=0.2
):
    """Create a stratified sample with a bias towards underrepresented classes. Class variable should be called 'labels'.

    Args:
        df (pd.DataFrame): data to sample from
        n (int): desired sample size
        underrepresented_bias_frac(float): proportion of sample that should be made up of underrepresented classes

    Returns:
        pd.DataFrame: stratified sample
    """
    # Normalize the DataFrame by exploding 'labels'
    df_normalized = df.explode("labels")

    # Calculate the proportion of each class
    class_proportions = df_normalized["labels"].value_counts(normalize=True)

    # Determine the number of samples for underrepresented classes (20% of n)
    samples_for_underrepresented = max(1, int(n * underrepresented_bias_frac))

    # Calculate sample sizes for each class, considering the total desired size n and the additional allocation for diversity
    total_samples_needed = (
        n + samples_for_underrepresented
    )  # Adjust total samples to include diversity allocation

    # Calculate initial sample size per class before adding diversity, attempting to respect original proportions
    initial_samples_per_class = (
        (class_proportions * (total_samples_needed - samples_for_underrepresented))
        .round()
        .astype(int)
    )

    # Ensure the sum of initial samples does not exceed total_samples_needed due to rounding adjustments
    while initial_samples_per_class.sum() > (
        total_samples_needed - samples_for_underrepresented
    ):
        initial_samples_per_class[initial_samples_per_class.idxmax()] -= 1

    # Sample based on calculated sizes
    initial_samples_list = [
        df_normalized[df_normalized["labels"] == cls].sample(
            n=min(cnt, len(df_normalized[df_normalized["labels"] == cls])),
            random_state=42,
        )
        for cls, cnt in initial_samples_per_class.items()
        if cnt > 0
    ]
    initial_samples = pd.concat(initial_samples_list)

    # Now add diversity: sample from underrepresented classes not already covered in initial_samples
    covered_classes = initial_samples["labels"].unique()
    additional_classes = df_normalized[~df_normalized["labels"].isin(covered_classes)][
        "labels"
    ].unique()

    if additional_classes.size > 0:
        additional_samples_list = [
            df_normalized[df_normalized["labels"] == cls].sample(n=1, random_state=42)
            for cls in additional_classes
        ]
        additional_samples = pd.concat(additional_samples_list)
        # Combine initial and additional samples
        final_sample = (
            pd.concat([initial_samples, additional_samples]).drop_duplicates().head(n)
        )
    else:
        final_sample = initial_samples.head(n)

    # Join back on to df to get full set of labels per record
    final_sample = pd.merge(
        final_sample.drop(columns=["labels"]),
        df[["feedback_record_id", "labels"]],
        on="feedback_record_id",
        how="left",
    )

    return final_sample
