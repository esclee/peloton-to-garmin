import xml.etree.ElementTree as etree
from datetime import datetime, timezone
import logging
import os

##############################
# Logging Setup
##############################

logger = logging.getLogger('peloton-to-garmin.Tcx_Builder')

METERS_PER_MILE = 1609.34

def getTimeStamp(timeInSeconds):
    timestamp = datetime.fromtimestamp(timeInSeconds, timezone.utc)
    iso = timestamp.isoformat()
    return iso.replace("+00:00", ".000Z")

def getHeartRate(heartRate):
    return "{0:.0f}".format(heartRate)

def getCadence(cadence):
    return "{0:.0f}".format(cadence)

def getSpeedInMetersPerSecond(speedInMilesPerHour):
    metersPerHour = speedInMilesPerHour * METERS_PER_MILE
    metersPerMinute = metersPerHour / 60
    metersPerSecond = metersPerMinute / 60
    return str(metersPerSecond)

def getInstructor(workout):
    if workout["workout_type"] == "class":
        if workout["peloton"]["ride"]["instructor"] is not None:
            return " with " + workout["peloton"]["ride"]["instructor"]["name"]
    return ""

def getGarminActivityType(workout):
        # Valid Garmin Parent types: Running/Biking/Other
    # Peloton Disciplines: cardio, circuit, running, cycling, walking, strength, stretching, meditation, yoga
    fitness_discipline = ""
    try:
        fitness_discipline = workout["fitness_discipline"]
    except Exception as e:
        logger.error("Failed to Parse Activity Type, defaulting to 'Other' - Exception: {}".format(e))

    if fitness_discipline == "cycling":
        sport = dict(Sport="Biking")
        simple_garmin_type = "Biking"
    elif fitness_discipline == "running" or fitness_discipline == "walking":
        sport = dict(Sport="Running")
        simple_garmin_type = "Running"
    else:   
        sport = dict(Sport="Other")
        simple_garmin_type = "Other"
    
    return sport, simple_garmin_type


def workoutSamplesToTCX(workout, workoutSummary, workoutSamples, outputDir):

    if(workoutSamples is None):
        logger.error("No workout sample data.") 
        return

    startTimeInSeconds = workout['start_time']

    etree.register_namespace("","http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
    etree.register_namespace("activityExtensions", "http://www.garmin.com/xmlschemas/ActivityExtension/v2")    

    root = etree.fromstring("""<TrainingCenterDatabase
  xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"
  xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2"
  xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns4="http://www.garmin.com/xmlschemas/ProfileExtension/v1"></TrainingCenterDatabase>""")

    activities = etree.Element("Activities")

    activity = etree.Element("Activity")
    sport, simple_garmin_type = getGarminActivityType(workout)
    activity.attrib = sport

    activityId = etree.Element("Id")
    activityId.text = getTimeStamp(startTimeInSeconds)

    lap = etree.Element("Lap")
    lap.attrib = dict(StartTime=getTimeStamp(startTimeInSeconds))

    totalTimeSeconds = etree.Element("TotalTimeSeconds")
    totalTimeSeconds.text = str(workout["ride"]["duration"])

    instructor = getInstructor(workout)
    title = "{0}{1}".format(workout["ride"]["title"].replace("/","-").replace(":","-"), instructor)

    try:
        notes = etree.Element("Notes")
        notes.text = "{} - {}".format(title, workout["ride"]["description"])
    except Exception as e:
        logger.error("Failed to Parse Description - Exception: {}".format(e))

    try:
        distanceMeters = etree.Element("DistanceMeters")
        distanceMeters.text = ""
        if len(workoutSamples["summaries"]) >= 2:
            miles = workoutSamples["summaries"][1]["value"]
            totalMeters = miles * METERS_PER_MILE
            distanceMeters.text = "{0:.1f}".format(totalMeters)
    except Exception as e:
            logger.error("Failed to Parse Distance - Exception: {}".format(e))
            return

    try:
        maximumSpeed = etree.Element("MaximumSpeed")
        maximumSpeed.text = getSpeedInMetersPerSecond(workoutSummary["max_speed"])

        calories = etree.Element("Calories")
        calories.text = str(int(round((workoutSummary["calories"]))))

        averageHeartRateBpm = etree.Element("AverageHeartRateBpm")
        ahrbValue = etree.Element("Value")
        ahrbValue.text = getHeartRate(workoutSummary["avg_heart_rate"])
        averageHeartRateBpm.append(ahrbValue)

        maximumHeartRateBpm = etree.Element("MaximumHeartRateBpm")
        mhrbValue = etree.Element("Value")
        mhrbValue.text = getHeartRate(workoutSummary["max_heart_rate"])
        maximumHeartRateBpm.append(mhrbValue)

        extensions = etree.Element("Extensions")
        lx = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}LX")
        avgSpeed = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}AvgSpeed")
        avgSpeed.text = getSpeedInMetersPerSecond(workoutSummary["avg_speed"])
        maxBikeCadence = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}MaxBikeCadence")
        maxBikeCadence.text = getCadence(workoutSummary["max_cadence"])
        avgWatts = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}AvgWatts")
        avgWatts.text = "{0:.0f}".format(workoutSummary["avg_power"])
        maxWatts = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}MaxWatts")
        maxWatts.text = "{0:.0f}".format(workoutSummary["max_power"])
        lx.append(avgSpeed)
        lx.append(maxBikeCadence)
        lx.append(avgWatts)
        lx.append(maxWatts)
        extensions.append(lx)
    except Exception as e:
        logger.error("Failed to Parse Speed/Cal/HR - Exception: {}".format(e))
        return

    track = etree.Element("Track")

    metrics = workoutSamples["metrics"]
    heartRateMetrics = []
    outputMetrics = []
    cadenceMetrics = []
    speedMetrics = []

    if(metrics is None):
        logger.error("No workout metrics data.") 
        return

    for item in metrics:
        if item["slug"] == "heart_rate":
            heartRateMetrics = item
        if item["slug"] == "output":
            outputMetrics = item
        if item["slug"] == "cadence":
            cadenceMetrics = item
        if item["slug"] == "speed":
            speedMetrics = item
        
    seconds_since_start = workoutSamples["seconds_since_pedaling_start"]

    for index, second in enumerate(seconds_since_start):
        trackPoint = etree.Element("Trackpoint")

        trackTime = etree.Element("Time")
        secondsSinceStart = second
        timeInSeconds = startTimeInSeconds + secondsSinceStart
        trackTime.text = getTimeStamp(timeInSeconds)

        try:
            if heartRateMetrics:
                trackHeartRate = etree.Element("HeartRateBpm")
                thrValue = etree.Element("Value")
                thrValue.text = getHeartRate(heartRateMetrics["values"][index])
                trackHeartRate.append(thrValue)
                trackPoint.append(trackHeartRate)
                
        except Exception as e:
            logger.error("Exception: {}".format(e))

        try:
            if cadenceMetrics:
                trackCadence = etree.Element("Cadence")
                trackCadence.text = getCadence(cadenceMetrics["values"][index])
                trackPoint.append(trackCadence)
        except Exception as e:
            logger.error("Exception: {}".format(e))

        trackExtensions = etree.Element("Extensions") 
        tpx = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}TPX")
        tpxSpeed = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}Speed")

        try:
            if speedMetrics:
                tpxSpeed.text = getSpeedInMetersPerSecond(speedMetrics["values"][index])
                tpx.append(tpxSpeed)
        except Exception as e:
            logger.error("Exception: {}".format(e))

        try:
            if outputMetrics:
                tpxWatts = etree.Element("{http://www.garmin.com/xmlschemas/ActivityExtension/v2}Watts")
                tpxWatts.text = "{0:.0f}".format(outputMetrics["values"][index])
                tpx.append(tpxWatts)
        except Exception as e:
            logger.error("Exception: {}".format(e))
        
        trackExtensions.append(tpx)
        
        trackPoint.append(trackTime)
        trackPoint.append(trackExtensions)
        
        track.append(trackPoint)

    lap.append(totalTimeSeconds)
    lap.append(distanceMeters)
    lap.append(maximumSpeed)
    lap.append(calories)
    lap.append(averageHeartRateBpm)
    lap.append(maximumHeartRateBpm)
    lap.append(track)
    lap.append(extensions)

    activity.append(activityId)
    activity.append(lap)
    activity.append(notes)

    activities.append(activity)
    root.append(activities)
    tree = etree.ElementTree(root)

    
    filename = "{0}-{1}-{2}.tcx".format(startTimeInSeconds, title, workout['id'])

    outputDir = outputDir.replace("\"", "")
    tree.write(os.path.join(outputDir,filename), xml_declaration=True, encoding="UTF-8", method="xml")
    return title, filename, simple_garmin_type
