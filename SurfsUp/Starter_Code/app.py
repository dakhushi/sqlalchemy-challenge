# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine,func

from flask import Flask , jsonify

#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base ()

# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Base.classes.keys()

Measurement = Base.classes.measurement
Station =Base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def homepage():
    """List all the available routes"""
    return(
            f"Available Routes:<br/>"
            f"/api/v1.0/precipitation<br/>"    
            f"/api/v1.0/stations<br/>"
            f"/api/v1.0/tobs<br/>"
            f"/api/v1.0/2010-01-01<br/>"
            f"/api/v1.0/2010-01-01/2017-08-23<br/>"
            )
@app.route("/api/v1.0/precipitation")
def precipitation():
    
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all dates and precipitation"""
    # Query all dates and prcp
    results = session.query(Measurement.date, Measurement.prcp).all()
    
    session.close()
    
    # Create a dictionary from the row data and append to a list of all_prcp
    all_prcp = []
    
    for date,prcp in results:
        date_prcp_dict = {}

        date_prcp_dict["date"]=date
        date_prcp_dict["prcp"]=prcp

        all_prcp.append(date_prcp_dict)
    
    return jsonify(all_prcp)


@app.route("/api/v1.0/stations")
def stations():

    session = Session(engine)

    #Query all stations
    stations = session.query(Measurement.station).all()
    session.close()

    #convert list of tuples into normal list
    all_stations = list(np.ravel(stations))

    return jsonify(all_stations)

#Query the dates and temperature observations of the most-active station for the previous year of data.
@app.route("/api/v1.0/tobs")
def tobs():

    session=Session(engine)

    # Getting the latest date from dataset
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    # Calculate the date of previous year from the last date in data set.
    query_date = dt.date(2017,8,23) + relativedelta(months=-12)
    
    #Most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
                            group_by(Measurement.station).\
                            order_by(func.count(Measurement.station).desc()).first()
 
    most_active_station_id = most_active_station[0]

    active_station_last_12_month_data = session.query(Measurement.station,Measurement.date, Measurement.tobs).\
                                        filter(Measurement.station == most_active_station_id).\
                                        filter(Measurement.date >=query_date).all()
    session.close()
   
    # Create a dictionary from the row data and append to a list of active_station_data
    active_station_data = []

    for station,date,tobs in active_station_last_12_month_data:
            station_dict = {}

            station_dict['station']=station
            station_dict["date"]=date
            station_dict["tobs"]=tobs

            active_station_data.append(station_dict)
        
    return jsonify(active_station_data)

#Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temprature_range(start,end=None):
    session = Session(engine)
    date_range = session.query(func.min(Measurement.date), func.max(Measurement.date)).all()
    
    #convert start and end to datetime objects
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    if end:
        end_date = dt.datetime.strptime(end, "%Y-%m-%d")
    else:
        # If no end date is provided, use the latest date in the dataset
        end_date = session.query(func.max(Measurement.date)).scalar()
    
    #Query for TMIN , TAVG, TMAX temps
    results = session.query(func.min(Measurement.tobs),\
                            func.avg(Measurement.tobs),\
                            func.max(Measurement.tobs)).\
                            filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    
    session.close()
    
    #If data is not available for requested date, return a message
    if not results or not results[0][0]:
        return jsonify({"Error": "Data is not available for requested date(s). Please try between this dates date_range[0][0]"}),404
    
    #Create dictionary to hold the temprature data
    temp_data = {'TMIN':results[0][0],
                'TAVG': results[0][1],
                'TMAX': results[0][2]
                }

    return jsonify(temp_data)
    


#Run the app
if __name__ == '__main__':
    app.run(debug=True)