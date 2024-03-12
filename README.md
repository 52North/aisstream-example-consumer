## Set up a virtual environment (venv)

Create the virtual environment:

```sh
python -m venv ais_env
```

Activate the virtual environment:

```sh
source ais_env/bin/activate
```

Deactivate the virtual environment (after finishing your work):

```sh
deactivate
```

## Install Python requirements

```sh
pip install -r requirements.txt
```

## Configuration

You can use a `.env` file to configure aisstream API key, bbox and output location (example in `sample.env`)

## Run

```sh
python -m app.stream
```
