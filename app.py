# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

# Database Setup
#################################################

# Create an SQLAlchemy engine and session
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station
session = Session(engine)

def is_valid_date_format(date_string):
    try:
        dt.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Flask Setup
#################################################
app = Flask(__name__)

# Flask Routes
#################################################

@app.route("/")
def home():
    return (
        f"Welcome to the Climate App API!<br/><br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year from the last date in the data set
    last_date = session.query(func.max(Measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d').date()
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query to retrieve precipitation data for the last 12 months
    results = session.query(Measurement.date, Measurement.prcp)\
        .filter(Measurement.date >= one_year_ago)\
        .all()

    # Convert the query results to a dictionary with date as the key and prcp as the value
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():
    # Query to retrieve a JSON list of stations
    station_results = session.query(Station.station).all()
    stations_list = [station[0] for station in station_results]

    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Calculate the date one year from the last date in the data set
    last_date = session.query(func.max(Measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d').date()
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query to retrieve temperature observations for the most active station for the last 12 months
    most_active_station = session.query(Measurement.station)\
        .group_by(Measurement.station)\
        .order_by(func.count().desc())\
        .first()[0]

    tobs_results = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == most_active_station)\
        .filter(Measurement.date >= one_year_ago)\
        .all()

    # Convert the query results to a list of dictionaries
    tobs_data = [{"Date": date, "Temperature": temp} for date, temp in tobs_results]

    return jsonify(tobs_data)

@app.route("/api/v1.0/<start>")
def temperature_stats(start):
    if is_valid_date_format(start):
        start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()

        # Query to calculate temperature statistics for a given start date
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start_date)\
            .all()

        min_temp, avg_temp, max_temp = results[0]

        return jsonify({"Minimum Temperature": min_temp, "Average Temperature": avg_temp, "Maximum Temperature": max_temp})
    else:
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD' format for the start date."}), 400

@app.route("/api/v1.0/<start>/<end>")
def temperature_stats_range(start, end):
    if is_valid_date_format(start) and is_valid_date_format(end):
        start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
        end_date = dt.datetime.strptime(end, '%Y-%m-%d').date()

        # Query to calculate temperature statistics within the specified date range
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start_date)\
            .filter(Measurement.date <= end_date)\
            .all()

        min_temp, avg_temp, max_temp = results[0]

        return jsonify({"Minimum Temperature": min_temp, "Average Temperature": avg_temp, "Maximum Temperature": max_temp})
    else:
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD' format for the start and end dates."}), 400

if __name__ == "__main__":
    port = 8080
    app.run(debug=True, port=port)
