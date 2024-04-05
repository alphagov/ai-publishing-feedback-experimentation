# AI Publishing Feedback Experimentation

A store of Data Science experimental work, started in Feb 2024, on how AI could help in understanding user feedback in GOV.UK Publishing.

## Nomenclature

TODO

## Technical documentation

You have two options for running the application - run it over the remote vector store (Qdrant collection) or populate a local collection and run over that. You can run locally either with docker from the command line, or using docker-compose to run everything with one command.

### Running over remote collection (using Google Cloud Engine)
Ensure you have the correct environment variables set (speak with the GOV.UK AI team), paying particular attention to the QDRANT_HOST variable, and ensuring the VM in GCE is running and populated. If so, you can run the application locally with
`streamlit run app/main.py`

If the collection on the VM has not been created/populated, you can simply run
`python collection/create_collection.py`
to populate it.

### Running over local collection
Before starting, make sure you have docker and docker-compose installed.

#### With docker-compose (recommended)
To run the application with one docker-compose command, make sure you have the relevant environment variables stored (speak with the AI team). Then run `docker-compose up`.

#### With Docker
To run locally using Docker, you can run
` docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant`
and then run
`python collection/create_collection.py`
to populate the local collection, ensuring `QDRANT_HOST` is set to "localhost" in your environment variables. This may take a while to run

You can then run
`streamlit run app/main.py`
to run the application locally.

## A note on Poetry

To install dependencies into a new environment, run `poetry install`. This will create an environment if one does not already exist, following the naming convention "project-name-py3.XX".

To add and remove more packages to the Poetry toml and lock, and therefore the environment, use `poetry add package-name` and `poetry remove package-name`. For dev dependencies (e.g. black), use the --group dev flag.

To run commands in the virtual env managed by poetry, either run `poetry shell` to open a terminal in the environment, or use `poetry run python scripts/myscript.py...`, where `poetry run` runs the subsequent command in the poetry virtual environment.

To run an ipython notebook in a virtual environment managed by poetry, run `poetry run python -m ipykernel install --user --name myname` to add a jupyter kernel for the existing poetry environment.

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
