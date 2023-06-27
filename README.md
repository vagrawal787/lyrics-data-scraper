# Lyrics Data Collector

This is a script to get a dataset for lyrics and their associated genres

## Installation

Create a venv in the main directory with 
```bash
python3 venv -m "insert venv_name here"
source "venv_name"/bin/activate
```
Install all requirements:
```bash
pip install -r requirements.txt 
```
## Setup

From the Spotify Developer Dashboard, create a new app and retrieve the client_id and client_secret keys.

Replace these values in the code with your keys:
```python
client_id = "" ### Insert Spotify app id here
client_secret = "" ### Insert Spotify app secret here
```

## Usage

```bash
python3 requester.py
```

## Contributing

Pull requests are welcome! Please reach out if you have any improvements or uses that
you'd like to discuss. 
