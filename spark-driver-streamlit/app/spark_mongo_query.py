import datetime
import sys, os
from pyspark.conf import SparkConf
from pyspark.sql import SparkSession
from pyspark.sql.types import Row
from subprocess import check_output
from pyspark.sql.window import Window
from pyspark.sql.functions import col, row_number, explode, window
import pyspark.sql.functions as F
import pandas as pd


def get_mongo_data_spark(start_time, end_time):

    SPARK_DRIVER_HOST = check_output(["hostname", "-i"]).decode(encoding="utf-8").strip()


    #Set Spark Session Configs
    spark_conf_mongo = SparkConf()
    spark_conf_mongo.setAll([
        ("spark.master", "spark://spark-master:7077",),  # <--- this host must be resolvable by the driver in this case pyspark (whatever it is located, same server or remote) in our case the IP of server
        ("spark.app.name", "TravelDashboard"),
        ("spark.submit.deployMode", "client"),
        ("spark.ui.showConsoleProgress", "true"),
        ("spark.eventLog.enabled", "false"),
        ("spark.logConf", "false"),
        ("spark.dynamicAllocation.enabled","false"),
        ("spark.driver.bindAddress", "0.0.0.0",),  # <--- this host is the IP where pyspark will bind the service running the driver (normally 0.0.0.0)
        ("spark.driver.host", SPARK_DRIVER_HOST,),  # <--- this host is the resolvable IP for the host that is running the driver and it must be reachable by the master and master must be able to reach it (in our case the IP of the container where we are running pyspark
        ("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.2"), #Download required monog-spark-connector package (make sure versions are correct)
        ("spark.mongodb.input.uri", "mongodb://mongodb:27017/"), #Connect to mongo container: ...//mongodb:27017 -> mongodb is name of container and 27017 is the port within the docker container
        ("spark.mongodb.input.database", "TravelDashboard"), #The database name to read data from
        ("spark.mongodb.input.collection", "travel_data"), #The collection name to read data from.
    ])

    spark_sess = SparkSession.builder.config(conf=spark_conf_mongo).getOrCreate()

    df = spark_sess.read.format("mongo").load()

    # Filter for time
    df = df.filter((df.time>=start_time)&(df.time<=end_time))

    # explode dataframe (since our mongo documents are now nested)
    df = df.withColumn("new",
                    F.arrays_zip("flight_data.callsign",
                                    "flight_data.vertical_rate",
                                    "flight_data.geo_altitude",
                                    "flight_data.country_cc",
                                    "flight_data.avg_no_seats"))\
        .withColumn("new", F.explode("new"))\
        .select("time",
                F.col("new.vertical_rate").alias("vertical_rate"),
                F.col("new.geo_altitude").alias("geo_altitude"),
                F.col("new.callsign").alias("callsign"),
                F.col("new.country_cc").alias("country_cc"),
                F.col("new.avg_no_seats").alias("avg_no_seats")
                )


    # Create starting and landing df
    df_starting = df.filter(df.vertical_rate>=4.)
    df_landing= df.filter(df.vertical_rate<=-4.)

    #df_starting.groupBy(window(col("time")))

    #only keep one row per callsign (with the lowest altitude because closest to airport)
    w2 = Window.partitionBy([window("time", "2 hours"), "callsign"]).orderBy(col("geo_altitude"))#, ascending=True)
    df_starting = df_starting.withColumn("row",row_number().over(w2)).filter(col("row") == 1).drop("row")
    df_landing = df_landing.withColumn("row",row_number().over(w2)).filter(col("row") == 1).drop("row")

    #df_starting.show()

    # Calculate number of travelers incoming and outcoming per country
    df_starting = df_starting.groupBy('country_cc').agg({'avg_no_seats': 'sum'})
    df_landing = df_landing.groupBy('country_cc').agg({'avg_no_seats': 'sum'})

    #Turn both dataframes to pandas
    df_starting = df_starting.toPandas()
    df_landing = df_landing.toPandas()

    spark_sess.stop()

    print("Spark job finished")

    #Rename columns
    df_starting.columns = ["country", "net_passengers"]
    df_landing.columns = ["country", "net_passengers"]

    #set index to country
    df_starting = df_starting.set_index("country", drop=True)
    df_landing = df_landing.set_index("country", drop=True)

    # Calculate delta between outgoing and incoming
    sum_pass = df_landing.net_passengers.sub(df_starting['net_passengers'], fill_value = 0).reset_index()

    #sum_pass.to_csv("net_psgrs.csv")

    print("Final calculations complete")

    return sum_pass


if __name__=="__main__":

    start_date = datetime.date(2022,6,27)
    start_time = datetime.time(6, 13)
    start_dtime = datetime.datetime.combine(start_date, start_time)

    end_date = datetime.date(2022,6,28)
    end_time = datetime.time(17, 12)
    end_dtime = datetime.datetime.combine(end_date, end_time)

    net_psgrs = get_mongo_data_spark(start_dtime, end_dtime)
