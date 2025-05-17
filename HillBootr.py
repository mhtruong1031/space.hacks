import statistics, json

from simulate_feed import get_data
from scipy.signal import medfilt
from pydantic import BaseModel

DATA_PATH     = 'resources/thermal_data.csv'
FEATURE_TYPES = ["RAW", "MEDIAN_FILTERED", "RAW_DIFF", "MEDIAN_FILTERED_DIFF", "ROLLING_MEAN", "ROLLING_STD"]

class HillBootr:
    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path

    def run(self, verbose: bool = False) -> None:
        time, time_states = get_data(self.data_path, stream = True)

        rolling_means = {f"SENSOR{i+1}": [] for i in range(20)}
        rolling_stds  = {f"SENSOR{i+1}": [] for i in range(20)}

        # Set up feature extractions [raw, median_filter, rolling_mean, diff]
        for i, state in enumerate(time_states):
            data = state

            sensor_data   = {f"SENSOR{i+1}": {key: [] for key in FEATURE_TYPES} for i in range(20)}

            for sensor in data:
                readings = data[sensor]

                # Median Filter
                median_filter = list(medfilt(readings, kernel_size=5))

                # Differential
                raw_diff = self.__first_derivative(readings, time)
                med_diff = self.__first_derivative(median_filter, time)

                # // Underlying Frequency Features // 
                # Rolling mean on MF
                tail  = median_filter[-5:]               
                mean  = sum(tail) / len(tail)
                rolling_means[sensor].append(mean)

                # Rolling STD
                if len(tail) > 1:
                    std = statistics.stdev(tail)
                else:
                    std = 0
                rolling_stds[sensor].append(std)

                sensor_data[sensor]["RAW"].append(readings)
                sensor_data[sensor]["MEDIAN_FILTERED"].append(median_filter)
                sensor_data[sensor]["RAW_DIFF"].append(raw_diff)
                sensor_data[sensor]["MEDIAN_FILTERED_DIFF"].append(med_diff)
                sensor_data[sensor]["ROLLING_MEAN"].append(rolling_means[sensor])
                sensor_data[sensor]["ROLLING_STD"].append(rolling_stds[sensor])

        '''with open('test.json', 'w') as file:
            json.dump(sensor_data, file, indent=4)'''

    # Returns an outcome tuple (is_anomoly, type, desc)
    # types = ["None", "Warning", "Alert", "Anomoly"]
    def analyze(self, features: dict):
        response = self.client.models.generate_content(
            model    = "gemini-2.0-flash",
            contents = command,
            config   = {
                "response_mime_type": "application/json",
                "response_schema": list[add_ons.WebPages],
            },
        )

    def __first_derivative(self, values: list, times: list) -> list[float]:
        return [
            (values[i+1] - values[i]) / (times[i+1] - times[i])
            for i in range(len(values) - 1)
        ]