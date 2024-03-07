# AI Publishing Feedback Experimentation

A store of Data Science experimental work, started in Feb 2024, on how AI could help in understanding user feedback in GOV.UK Publishing.

## Nomenclature

TODO

## Technical documentation

To run the application, make sure you have docker and docker-compose installed, and have the relevant environment variables stored (speak with the AI team). Then run `docker-compose up`.

### A note on Poetry

To install dependencies into a new environment, run `poetry install`. This will create an environment if one does not already exist, following the naming convention "project-name-py3.XX".

To add and remove more packages to the Poetry toml and lock, and therefore the environment, use `poetry add package-name` and `poetry remove package-name`. For dev dependencies (e.g. black), use the --group dev flag.

To run commands in the virtual env managed by poetry, either run `poetry shell` to open a terminal in the environment, or use `poetry run python scripts/myscript.py...`, where `poetry run` runs the subsequent command in the poetry virtual environment.

To run an ipython notebook in a virtual environment managed by poetry, run `poetry run python -m ipykernel install --user --name myname` to add a jupyter kernel for the existing poetry environment.

## Licence

[MIT License](LICENSE)
