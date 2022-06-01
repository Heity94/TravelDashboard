import pandas as pd
import numpy as np
import reverse_geocoder
import requests
import os

def get_data():

    print("Load local databases ...")
    # Load required databases for matching/ preprocessing
    seat_data = pd.read_csv(os.path.join(os.path.dirname(__file__),"data","seats_p_aircraft_final.csv"),
                            index_col=0)

    #seat_data = pd.read_csv("TravelDashboard/data/seats_p_aircraft_final.csv",
    #                        index_col=0)
    aircraftregister_US = pd.read_csv(os.path.join(
        os.path.dirname(__file__), "data",
        "US_ReleasableAircraftRegister.csv"),
                                      index_col=0,
                                      low_memory=False)
    opensky_DB = pd.read_csv(os.path.join(
        os.path.dirname(__file__), "data",
        "OpenSky_AircraftDatabase.csv"))

    #Call OpenSky API to receive current status of all aircrafts
    print("Call OpenSky API ...")
    response = requests.get(
        "https://opensky-network.org/api/states/all").json()

    # Define column names for dataframe
    col_names = [
        'icao24', 'callsign', 'origin_country', 'time_position',
        'last_contact', 'long', 'lat', 'baro_altitude', 'on_ground',
        'velocity', 'true_track', 'vertical_rate', 'sensors', 'geo_altitude',
        'squawk', 'spi', 'position_source', "drop"
    ]

    # Create Dataframe
    flights = pd.DataFrame(response["states"], columns=col_names)
    flights['time'] = response[
        'time']  #add time column and set to time of API call

    # Drop columns & rows which are not required
    flights.drop(columns=[
        "time_position", "last_contact", "sensors", "squawk", "spi",
        "position_source", "drop"
    ],
                 inplace=True)  # drop columns
    flights.dropna(
        subset=['lat', "long", "icao24"], inplace=True
    )  #drop rows where lat or long or icao24 is NaN -> can not be used for further processing

    return flights, opensky_DB, seat_data, aircraftregister_US, response

def filter_passenger_carriers(flights_df):
    '''Filter out aircrafts from carriers which do not transport passengers'''

    # Create list of carriers and type of transport
    wikiurl = "https://de.wikipedia.org/wiki/Liste_von_Fluggesellschaften" #URL of lists of carriers from
    carriers_df = pd.DataFrame(pd.read_html(wikiurl, keep_default_na=False)[1]) # read table from wikipedia
    car_types = ["B", "C", "P", "P+", "U", "U+"] # Labels for passenger carriers
    p_carriers = carriers_df[carriers_df["Bemerkung"].isin(car_types)] # Filter wikipedia table for passenger carriers

    # merge carrier to df
    pflights_df = flights_df[flights_df.callsign.str[:3].isin(p_carriers.ICAO)].copy() # Filter flights only to include passenger flights
    pflights_df["callsign_carrier"] = pflights_df["callsign"].str[:3] # extra column (not sure if needed)
    pflights_df = pflights_df.merge(p_carriers[["Name", "ICAO", "Bemerkung"]], left_on="callsign_carrier", right_on="ICAO", how="left")
    pflights_df.rename(columns = {'Name':'carrier_company', "ICAO":"icao", "Bemerkung":"carrier_type"}, inplace = True)
    pflights_df.drop(columns=["icao"], inplace=True)

    return pflights_df

def get_aircraft_data(pflights_df, opensky_DB):
    '''Add aircraft data from OpenSky_Aircraft Database'''

    # Merge pflights df with openskyDB on "icao24"
    pflights_df = pflights_df.merge(opensky_DB[['icao24', 'manufacturericao', 'manufacturername', 'model', 'icaoaircrafttype']],
                                    on="icao24", how="left")

    # strip whitespace
    cols = pflights_df.select_dtypes(object).columns # select all columns with dtype string
    pflights_df[cols] = pflights_df[cols].apply(lambda x: x.str.strip()) # strip whitespace

    #Filter pflights_df to only include "Landplanes" == icaoaircrafttype starts with "L"
    pflights_df = pflights_df.loc[pflights_df.icaoaircrafttype.str.startswith("L", na=True)]

    return pflights_df

def merge_seat_data(pflights_df, seat_data):
    '''Add average number of seats for each aircraft based on "seat_data"'''

    pflights_man = pflights_df # create deep copy to not order input df

    # create new row with first 3-4 letters of model number (for better matching results)
    pflights_man["model_no_stripped"] = pflights_man["model"]

    ##AIRBUS & BOEING -----------------
    #General Matching for Airbus & Boeing using Regex
    pflights_man["model_no_stripped"] = pflights_man.loc[:,"model_no_stripped"].replace(regex={"Airbus\sA?|AIRBUS\sA?":"A", "Boeing\s?|BOEING\s?":"", "(?<=\d{3})(\s)(?=\d{1})":"-"})
    indexer = pflights_man[(pflights_man.manufacturericao.str.contains("Airbus", na=False, regex=True, case=False))&(pflights_man.model_no_stripped.str.startswith("3", na=True))].index
    pflights_man.loc[indexer, 'model_no_stripped'] = "A"+pflights_man.loc[indexer, 'model_no_stripped'].astype(str) # Add an "A" at the beginning for Airbus models which start with 3...
    pflights_man["model_no_stripped"] = pflights_man.loc[(~pflights_man["model_no_stripped"].isnull()),"model_no_stripped"].str.findall("\w{1,4}[-\s][\w]?|^\w{4}?|^\w{3,4}\Z").transform("".join)
    pflights_man["model_no_stripped"] = pflights_man.loc[:,"model_no_stripped"].replace(regex={"NG\s":"-", "\s?MAX\s?":"-", "(?<=^A)-":""})
    pflights_man["model_no_stripped"] = pflights_man.loc[(~pflights_man["model_no_stripped"].isnull()),"model_no_stripped"].str.findall("^\w{3,4}[- ]?\w?").transform("".join)#.copy()
    pflights_man.loc[pflights_man.model.str.contains("A-320neo|A320neo", na=False),"model_no_stripped"]="A320neo"
    pflights_man.loc[pflights_man.model.str.contains("A-321neo|A321neo", na=False),"model_no_stripped"]="A321"
    pflights_man.loc[pflights_man.model.str.contains("^A-320$", na=False),"model_no_stripped"]="A320"
    pflights_man.loc[pflights_man.model.str.contains("^BD-500-1A10", na=False),"model_no_stripped"]="A220-1"
    pflights_man.loc[pflights_man.model.str.contains("^BD-500-1A11", na=False),"model_no_stripped"]="A220-3"

    # list of most frequent missing aircrafts in model_no_stripped (created manually)
    missing_aircrafts = ['A319-1','A320-2', 'A320-3','321-2','A300 B','A318-1','A388','A320-N','A359','350-1','A300B','320-2','330-3','A320 N', '717-2','777 F','B777-','777-F','B747-','777F','B777-F']

    # insert model_no_stripped for majority of missing aircrafts from Boeing and Airbus
    indexer = pflights_man[pflights_man.model_no_stripped.isin(missing_aircrafts)].index
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model_no_stripped'].str.findall("[A]?\d{3}(?=[-\sBF])").transform("".join)

    # Replace model_no_stripped for special Airbus models
    missing_aircrafts = ['A330-8','A330-9']
    indexer = pflights_man[pflights_man.model_no_stripped.isin(missing_aircrafts)].index
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model_no_stripped'].str.findall("[A]?\d{3}-\d").transform("".join)

    # Replace model_no_stripped for special Boeing models
    missing_aircrafts = ['B787-9','738-8','B737-8','B737-9','B787-8', 'B777-2', 'B777-3','B747-8', 'B747-4']
    indexer = pflights_man[pflights_man.model_no_stripped.isin(missing_aircrafts)].index
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model_no_stripped'].str.findall("\d{3}-\d").transform("".join)


    ##EMBRAER -----------------
    # for Embraer we have to rename EMB to ERJ in order that aircrafts can be mapped with seat_data list
    indexer = pflights_man[(pflights_man.manufacturericao.str.contains("Embraer", na=False, regex=True, case=False))].index
    pflights_man.loc[indexer, 'model_no_stripped'] = ""

    indexer = pflights_man[(pflights_man.model.str.contains("EMB|ERJ", na=False, regex=True, case=False))].index
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model'].str.replace("EMB|emb|Emb","ERJ", regex=True).transform("".join).str.replace("(?<=ERJ) ","-", regex=True).transform("".join).str.findall("ERJ-\d{3}").transform("".join)

    indexer = pflights_man[(~pflights_man["model"].isnull())&(pflights_man.manufacturericao.str.contains("Embraer", na=False, regex=True, case=False))&(pflights_man["model_no_stripped"]=="")].index
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model'].str.replace("E(?=\d{3})","ERJ-", regex=True).transform("".join)
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model_no_stripped'].str.findall("ERJ-\d{3}").transform("".join)

    ##BOMBARDIER -----------------
    # Bombardier: map unknown models from Bombardier to our seat_data list (manual research)
    map_unkn_models = {
        "CL-600-2B19":"CRJ200",
        "CL-600-2C10":"CRJ700",
        "CL-600-2D2":"CRJ900",
        "CL-600-2D24":"CRJ900",
        "DHC-8 311":"Q-300",
        "DHC-8 311Q":"Q-300",
        "DHC-8 1":"Series 1",
        "DHC-8 101":"Series 1",
        "DHC-8 2":"Q-200",
        "DHC-8 3":"Q-300",
        "DHC-8 4":"Q-400",
        "CL-600-2C11":"CRJ700",
        "DHC-8-402":"Q-400",
        "DHC-8-402 (Dehavilland)":"Q-400"
    }

    indexer = pflights_man.loc[(pflights_man.manufacturername.str.contains("Bombardier|De Havilland Canada|De Havilland",case=False, na=False))].index
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model']

    indexer = pflights_man[(~pflights_man["model"].isnull())&(~pflights_man.model_no_stripped.isin(map_unkn_models.keys()))&(pflights_man.manufacturername.str.contains("Bombardier",case=False, na=False))].index
    pflights_man.loc[indexer, 'model_no_stripped'] = pflights_man.loc[indexer, 'model_no_stripped'].str.findall("CRJ[- ]\d+|DHC[- ]\d[ -]\d").transform("".join).str.replace("(?<=CRJ) ","", regex=True).transform("".join)
    pflights_man.replace({"model_no_stripped": map_unkn_models}, inplace=True)


    # Merge pflights and seat_data (drop duplicates necessary, because keys "model_no_stripped" match more than one row in seat_data)
    merged_df = pflights_man.merge(seat_data[["model_no_stripped", "avg_no_seats"]].drop_duplicates(subset=["model_no_stripped"]), how="left", on="model_no_stripped")

    return merged_df

def merge_seat_data_US(pflights_df, aircraftregister_US):
    '''Update values for aircrafts from the US based on official US aircraft register'''

    # Merge dataframes to get Aircraft model and no of seats for american registered airlines
    pflights_df = pflights_df.merge(aircraftregister_US, on="icao24", how="left")

    #Filter DataFrame, so that only engine powered aircrafts are included (type 4 or 5)
    pflights_df = pflights_df.loc[pflights_df["TYPE AIRCRAFT"].str.contains("4|5", case=False, na=True)]

    # Overwrite values in column "avg_no_seats" if value from US register exists
    pflights_df["avg_no_seats"] = np.where(pflights_df["NO-SEATS"].notnull(), pflights_df["NO-SEATS"], pflights_df["avg_no_seats"])

    # Overwrite values in column "model_no" if value from US register exists
    pflights_df["model"] = np.where(pflights_df["MODEL"].notnull(), pflights_df["MODEL"], pflights_df["model"])

    # Overwrite values in column "manufacturericao" if value from US register exists
    pflights_df["manufacturericao"] = np.where(pflights_df["MFR"].notnull(), pflights_df["MFR"], pflights_df["manufacturericao"])

    # Drop columns which are not required anymore/duplicates
    pflights_df.drop(columns=['manufacturername', 'MODE S CODE HEX', 'TYPE AIRCRAFT', 'MFR', 'MODEL', 'NO-SEATS'], inplace=True)

    return pflights_df

def impute_missing_seats(pflights_df, seat_data):
    '''Impute average seat number for missing values based on average seat number from seat_data (over all airlines)'''

    # Overall Average of seat data list
    mean_seats = np.round(seat_data["avg_no_seats"].mean(),0)

    #Get index from all aircrafts where avg_no_seat is Null
    indexer = pflights_df[pflights_df.avg_no_seats.isnull()].index

    # Replace avg_seat_no with average
    pflights_df.loc[indexer, 'avg_no_seats'] = mean_seats

    return pflights_df

def increase_capacity_cheap_airlines(pflights_df):
    '''Incerease avg_no_seats for cheap carriers "Billigfliefger" by 10%'''

    #Get index from all aircrafts where carrier_type is "Billigflieger"
    indexer = pflights_df[pflights_df.carrier_type=="B"].index
    # Replace avg_seat_no with average
    pflights_df.loc[indexer, 'avg_no_seats'] = pflights_df.loc[indexer, 'avg_no_seats']*1.1

    return pflights_df

def rev_geocode(pflights_df):
    '''Reverse Geocode the city, area and country based on Lat & Long'''

    # create coord column with the required format for the reverse_geocoder
    pflights_df["coord"]= [(lat, long) for lat, long in zip(pflights_df["lat"], pflights_df["long"])]

    # Get coordinates
    coordinates = pflights_df.coord.tolist()
    rev_geo = reverse_geocoder.search(coordinates)

    # Create df and filter important rows
    rev_geo_df = pd.DataFrame(rev_geo)[["name", "admin1", "admin2", "cc"]]
    rev_geo_df.columns = ["city_name", "reg_admin1", "reg_admin2", "country_cc"]

    # Concat Geo Data with old dataframe
    pflights_df = pd.concat([pflights_df, rev_geo_df], axis=1)

    return pflights_df

def preproc_flight_data(flights_df, opensky_DB, seat_data, aircraftregister_US):
    '''Preprocess flight data from OpenSky API'''

    print("Start preprocessing ...")
    print("Shape before filter_passenger_carriers:", flights_df.shape)
    pflights_df = filter_passenger_carriers(flights_df)

    print("Shape before get_aircraft_data:", pflights_df.shape)
    pflights_df = get_aircraft_data(pflights_df, opensky_DB)

    print("Shape before merge_seat_data:", pflights_df.shape)
    pflights_df = merge_seat_data(pflights_df, seat_data)

    print("Shape before merge_seat_data_US:", pflights_df.shape)
    pflights_df = merge_seat_data_US(pflights_df, aircraftregister_US)

    print("Shape before impute_missing_seats:", pflights_df.shape)
    pflights_df = impute_missing_seats(pflights_df, seat_data)

    print("Shape before increase_capacity_cheap_airlines:", pflights_df.shape)
    pflights_df = increase_capacity_cheap_airlines(pflights_df)

    print("Shape before rev_geocode:", pflights_df.shape)
    pflights_df = rev_geocode(pflights_df)

    print("Preprocessing finished")

    return pflights_df

def save_processed_data(pflights_df, response):

    #Set path to store data
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw_data",
                        "preproc_data_test", f"{response['time']}.csv")
    #path = "raw_data/preproc_data_test/"

    # Store preprocessed DataFrame to csv
    pflights_df.to_csv(path)
    print(f'''Final DataFrame stored as .csv under {path}''')


if __name__ == "__main__":

    #Load data
    flights, opensky_DB, seat_data, aircraftregister_US, response = get_data()

    # Preprocess flight data
    pflights_df_final = preproc_flight_data(flights, opensky_DB, seat_data, aircraftregister_US)

    # Store preprocessed DataFrame to csv
    save_processed_data(pflights_df_final, response)
