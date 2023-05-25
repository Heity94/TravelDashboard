# Travel Dashboard

Group project to extract airplane traffic data from different API/data sources to visualize global passenger travel streams utilizing python, PySpark and MongoDB.

The project is divided into three separate parts:
1) **Data retrieval**
  Retrieval and preprocessing of flight data from [OpenSkyAPI](https://openskynetwork.github.io/opensky-api/) using a python script which is executed every 5 minutes using crontab. The resulting data is stored as .csv files.
2) **Data storage**
  The stored .csv files are dumped in the MongoDB in batches periodically
3) **Data analysis and User Interface**
  Using a streamlit dashboard the user selects a data range to be analyzed. The data is retrieved and aggregated using Spark and displayed as a heatmap.

Part 2 & 3 are run within a multi-container Docker application using Docker-compose.

## Structure of the repository
The general structure of this repository is detailed below
```bash
.
├── TravelDashboard           # Python module to call OpenSky API and preprocess data to estimate passenger travel per flight
├── crontab_description.txt   # Crontab command to run the script on a server
├── data                      # Storage of created .csv files and mongoDB local volume
├── docker-compose.yml        # Defines and runs the multi-container Docker application (MondoDB, Spark Master and Worker and Streamlit application)
├── notebooks                 # Notebooks used during development
├── requirements.txt          # Requirements for TravelDashboard module
├── scripts                   # Script to call OpenSky API and store data in data folder
├── spark-driver-streamlit    # Streamlit application for the User Interface and relevant spark queries
├── setup.py
├── jar_files
└── spark_conf
```

## Installation

### Clone repository
1. Open the Terminal.
2. Change the current working directory to the location where you want the cloned directory
3. Clone the repository using
```bash
git clone git@github.com:Heity94/TravelDashboard.git
```
4. Change into the cloned directory
```bash
cd TravelDashboard/
```
### Create and activate virtual environment
To avoid dependency issues we recommend to create a new virtual environment to install and run our code. Please note, that in order to follow the next steps [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) need to be installed.
1. Create a virtual environment using `pyenv virtualenv`. You can of course use another name as `travel_dash` for the environment.
```bash
pyenv virtualenv travel_dash
```
2. Optionally: Use `pyenv local` within the TravelDashboard source directory to select that environment automatically:
```bash
pyenv local travel_dash
```
From now on, all the commands that you run in this directory (or in any sub directory) will be using `travel_dash` virtual env.

### Install the package to call and preprocess the OpenSky travel data

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install TravelDashboard.
```bash
pip install --upgrade pip
pip install -e .
```

## Usage

### Execute data retrieval
After succesful installation the script can be run. If you are using a server you can use crontab to periodically execute the script and store the preprocessed flight data.
```python
python TravelDashboard-run
```

### Start multi-container application using Docker Compose
Please follow the commands below to start the application.

Please note, that you need to create and store some flight data in the MongoDB. Please see [here](notebooks/PH_FlightData2Mongo.ipynb) on how to dump data into MongoDB.

```bash
# Change current directory to spark-drive-streamlit
cd spark-drive-streamlit

# Build the docker image for the driver including streamlit
docker build -t spark-drive-streamlit

# Change back to the main folder
cd ..

# Create and run all the docker images
docker compose up -d

# Check if all containers are running
docker ps # You can now check http://localhost:8080/ to check if your spark is set up properly and the worker is alive

# Load data into MongoDB: Please see `PH_FlightData2Mongo.ipynb` on how to dump data into MongoDB.

# To start the streamlit page we need to access the bash of the sprk driver container
docker exec -it traveldashboard-spark-driver-1 /bin/bash

# Now run the streamlit app
streamlit run spark-driver-streamlit/app/app.py

#You can see your website on http://localhost:8501/ (This may take a while but at some time a df should show up)
# You can exit the bash using `exit`
# To shut down the container just run `docker compose down`
```
