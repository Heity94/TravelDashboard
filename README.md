# Data analysis
- Document here the project: TravelDashboard
- Description: Project Description
- Data Source:
- Type of analysis:

Please document the project the better you can.

# Startup the project

The initial setup.

Create virtualenv and install the project:
```bash
sudo apt-get install virtualenv python-pip python-dev
deactivate; virtualenv ~/venv ; source ~/venv/bin/activate ;\
    pip install pip -U; pip install -r requirements.txt
```

Unittest test:
```bash
make clean install test
```

Check for TravelDashboard in gitlab.com/{group}.
If your project is not set please add it:

- Create a new project on `gitlab.com/{group}/TravelDashboard`
- Then populate it:

```bash
##   e.g. if group is "{group}" and project_name is "TravelDashboard"
git remote add origin git@github.com:{group}/TravelDashboard.git
git push -u origin master
git push -u origin --tags
```

Functionnal test with a script:

```bash
cd
mkdir tmp
cd tmp
TravelDashboard-run
```

# Install

Go to `https://github.com/{group}/TravelDashboard` to see the project, manage issues,
setup you ssh public key, ...

Create a python3 virtualenv and activate it:

```bash
sudo apt-get install virtualenv python-pip python-dev
deactivate; virtualenv -ppython3 ~/venv ; source ~/venv/bin/activate
```

Clone the project and install it:

```bash
git clone git@github.com:{group}/TravelDashboard.git
cd TravelDashboard
pip install -r requirements.txt
make clean install test                # install and test
```
Functionnal test with a script:

```bash
cd
mkdir tmp
cd tmp
TravelDashboard-run
```

Download und unzip required .csv data and store in data folder
```bash
curl https://opensky-network.org/datasets/metadata/aircraftDatabase.csv > TravelDashboard/data/OpenSky_AircraftDatabase.csv
curl https://registry.faa.gov/database/ReleasableAircraft.zip > TravelDashboard/data/US_ReleasableAircraft.zip
cd TravelDashboard/data
unzip US_ReleasableAircraft.zip -d US_ReleasableAircraft/
rm US_ReleasableAircraft.zip
```
