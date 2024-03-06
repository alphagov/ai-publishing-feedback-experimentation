# AI Publishing Feedback Experimentation

A store of Data Science experimental work, started in Feb 2024, on how AI could help in understanding user feedback in GOV.UK Publishing.

## Nomenclature

TODO

## Technical documentation


## To download data from GCS

To download a file from a Google Cloud Storage (GCS) bucket using the gsutil command-line tool, you can use the cp command.
To download the file to a specific directory, specify the full path to the directory in the command.

e.g. `gsutil cp gs://example-bucket/example.json /path/to/your/local/directory`

If you're in the root directory of our folder you can download the data using the following command:

`gsutil cp gs://example-bucket/example.json $(pwd)/data/file.json`

*Make sure you have the necessary permissions to access the GCS bucket and download the file. If you're not already authenticated,
you may need to run `gcloud auth login` to set up your credentials.*


## Licence

[MIT License](LICENSE)
