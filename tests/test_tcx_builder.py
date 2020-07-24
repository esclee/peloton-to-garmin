import json
import os
import pytest
from lib import tcx_builder

class TestTcxBuilder:
    
    @classmethod
    def setup_class(cls):
        outputDir = cls.getOutputDir(cls)
        if not os.path.exists(outputDir):
            os.mkdir(outputDir)

    def loadTestData(self, filename):
        with open(os.path.join(os.getcwd(), "data", filename)) as json_file:
            return json.load(json_file)

    def getOutputDir(self):
        return os.path.join(os.getcwd(),"testOutput")

    def test_cycling_smoketest(self):
        # Setup
        workout_data = self.loadTestData("peloton_workout_cycling.json")
        workout_summary = self.loadTestData("peloton_workoutsummary_cycling.json")
        workout_samples = self.loadTestData("peloton_workoutsamples_cycling.json")
        output_directory = self.getOutputDir()

        # Act
        title, filename, garmin_activity_type = tcx_builder.workoutSamplesToTCX(workout_data, workout_summary, workout_samples, output_directory)
        
        # Assert
        assert title == "20 min HIIT Ride with Denis Morton"
        assert filename == "1586208689-20 min HIIT Ride with Denis Morton-6c4d525d20134c74b7395991ed6912ce.tcx"
        assert garmin_activity_type == "Biking"
        assert os.path.exists(os.path.join(output_directory, filename))

    def test_cycling_freestyle_smoketest(self):
        # Setup
        workout_data = self.loadTestData("peloton_workout_cycling_freestyle.json")
        workout_summary = self.loadTestData("peloton_workoutsummary_cycling_freestyle.json")
        workout_samples = self.loadTestData("peloton_workoutsamples_cycling_freestyle.json")
        output_directory = self.getOutputDir()

        # Act
        title, filename, garmin_activity_type = tcx_builder.workoutSamplesToTCX(workout_data, workout_summary, workout_samples, output_directory)
        
        # Assert
        assert title == "27 sec Just Ride"
        assert filename == "1595374979-27 sec Just Ride-88963f6daf89445387da4ee2e26015f9.tcx"
        assert garmin_activity_type == "Biking"
        assert os.path.exists(os.path.join(output_directory, filename))

    def test_strength_smoketest(self):
        # Setup
        workout_data = self.loadTestData("peloton_workout_strength.json")
        workout_summary = self.loadTestData("peloton_workoutsummary_strength.json")
        workout_samples = self.loadTestData("peloton_workoutsamples_strength.json")
        output_directory = self.getOutputDir()

        # Act
        title, filename, garmin_activity_type = tcx_builder.workoutSamplesToTCX(workout_data, workout_summary, workout_samples, output_directory)
        
        # Assert
        assert title == "10 min Bodyweight Strength with Becs Gentry"
        assert filename == "1589907174-10 min Bodyweight Strength with Becs Gentry-38583cbc0e434e54a2eb91be1a770e01.tcx"
        assert garmin_activity_type == "Other"
        assert os.path.exists(os.path.join(output_directory, filename))

    def test_running_smoketest(self):
        # Setup
        workout_data = self.loadTestData("peloton_workout_running.json")
        workout_summary = self.loadTestData("peloton_workoutsummary_running.json")
        workout_samples = self.loadTestData("peloton_workoutsamples_running.json")
        output_directory = self.getOutputDir()

        # Act
        title, filename, garmin_activity_type = tcx_builder.workoutSamplesToTCX(workout_data, workout_summary, workout_samples, output_directory)
        
        # Assert
        assert title == "20 min Pop Fun Run with Olivia Amato"
        assert filename == "1565299850-20 min Pop Fun Run with Olivia Amato-63eef26a23744af295f14006811b159b.tcx"
        assert garmin_activity_type == "Running"
        assert os.path.exists(os.path.join(output_directory, filename))
    
    def test_running_outdoor_smoketest(self):
        # Setup
        workout_data = self.loadTestData("peloton_workout_running_outdoor.json")
        workout_summary = self.loadTestData("peloton_workoutsummary_running_outdoor.json")
        workout_samples = self.loadTestData("peloton_workoutsamples_running_outdoor.json")
        output_directory = self.getOutputDir()

        # Act
        title, filename, garmin_activity_type = tcx_builder.workoutSamplesToTCX(workout_data, workout_summary, workout_samples, output_directory)
        
        # Assert
        assert title == "20 min Walk + Run with Olivia Amato"
        assert filename == "1574980432-20 min Walk + Run with Olivia Amato-af25d72ea4c0400daeac2707fc30994f.tcx"
        assert garmin_activity_type == "Running"
        assert os.path.exists(os.path.join(output_directory, filename))

    getDistanceMeters_testdata = [
        (10, "m", "10.0"),
        (10, "km", "10000.0"),
        (10, "mi", "{0:.1f}".format(10 * tcx_builder.METERS_PER_MILE))
    ]
    @pytest.mark.parametrize("distanceValue, distanceUnit, expectedDistance", getDistanceMeters_testdata)
    def test_getDistanceMeters(self, distanceValue, distanceUnit, expectedDistance):
        # Setup
        workout_samples = self.loadTestData("peloton_workoutsamples_cycling.json")
        workout_samples["summaries"][1]["display_unit"] = distanceUnit
        workout_samples["summaries"][1]["value"] = distanceValue
        distance = workout_samples["summaries"][1]["value"]
        expectedDistanceUnit = distanceUnit

        # Act
        distanceMeters, originalDistanceUnit = tcx_builder.getDistanceMeters(workout_samples)

        # Assert
        assert distanceMeters == expectedDistance
        assert originalDistanceUnit == expectedDistanceUnit

    convertDistanceValueToMeters_testdata = [
        (10, "m", 10),
        (10, "km", 10000),
        (10, "mi", 10 * tcx_builder.METERS_PER_MILE)
    ]
    @pytest.mark.parametrize("distanceValue, distanceUnit, expected", convertDistanceValueToMeters_testdata)
    def test_convertDistanceValueToMeters(self, distanceValue, distanceUnit, expected):
        # Act
        meters = tcx_builder.convertDistanceValueToMeters(distanceValue, distanceUnit)

        # Assert
        assert meters == expected
    
    getSpeedInMetersPerSecond_testdata = [
        (10, "m", 0.0027777777777777775),
        (10, "km", 2.7777777777777777),
        (10, "mi", 4.4703888888888885)
    ]
    @pytest.mark.parametrize("speedPerHour, distanceUnit, expected", getSpeedInMetersPerSecond_testdata)
    def test_getSpeedInMetersPerSecond(self, speedPerHour, distanceUnit, expected):
        # Act
        meters = tcx_builder.getSpeedInMetersPerSecond(speedPerHour, distanceUnit)

        # Assert
        assert meters == expected

    getMaxSpeedMetersPerSecond_testdata = [
        (10, "m", "0.0027777777777777775"),
        (10, "km", "2.7777777777777777"),
        (10, "mi", "4.4703888888888885")
    ]
    @pytest.mark.parametrize("speedValue, distanceUnit, expected", getMaxSpeedMetersPerSecond_testdata)
    def test_getMaxSpeedMetersPerSecond(self, speedValue, distanceUnit, expected):
        # Setup
        workout_summary = self.loadTestData("peloton_workoutsummary_cycling.json")
        workout_summary["max_speed"] = speedValue
        expectedDistanceUnit = distanceUnit

        # Act
        speed = tcx_builder.getMaxSpeedMetersPerSecond(workout_summary, distanceUnit)

        # Assert
        assert speed == expected
