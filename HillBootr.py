import statistics, json, os
from colorama import Fore, Style

import matplotlib.pyplot as plt

from google       import genai
from google.genai import types

from simulate_feed import get_data
from scipy.signal import medfilt
from pydantic import BaseModel

from config import *

import warnings, pyttsx3

warnings.filterwarnings('ignore')

DATA_PATH     = 'resources/thermal_data.csv'
FEATURE_TYPES = ["RAW", "MEDIAN_FILTERED", "RAW_DIFF", "MEDIAN_FILTERED_DIFF", "ROLLING_MEAN", "ROLLING_STD"]

DEFAULT_MODEL = "gemini-2.0-flash"
MAX_TOKENS    = 1000

plt.ion()

class Analysis(BaseModel):
    is_anomaly: bool
    anom_type: int
    desc: str

class HillBootr:
    def __init__(self, data_path: str = DATA_PATH, model: str = DEFAULT_MODEL):
        os.system('clear')
        self.data_path = data_path

        # Gemini Initialization
        self.model      = model
        self.api_key    = API_KEY
        self.max_tokens = MAX_TOKENS

        self.client = genai.Client(api_key=API_KEY)

        # pyttsx3 Initialization
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170) # speaking speed

        self.fig, self.ax = plt.subplots(2, 3)
        self.fig.set_figheight(6)
        self.fig.set_figwidth(9)

        self.colors    = [Fore.WHITE, Fore.GREEN, Fore.YELLOW, Fore.RED]
        self.anom_type = ["No Issues. ", "WARNING. ", "ALERT. ", "!! URGENT !!"]

    def run(self, verbose: bool = False) -> None:
        time, time_states = get_data(self.data_path, stream = True)

        rolling_means = {f"SENSOR{i+1}": [] for i in range(20)}
        rolling_stds  = {f"SENSOR{i+1}": [] for i in range(20)}

        # Set up feature extractions [raw, median_filter, rolling_mean, diff]
        for i, state in enumerate(time_states):
            data = state

            sensor_data   = {f"SENSOR{i+1}": {key: [] for key in FEATURE_TYPES} for i in range(20)}

            raw_lines       = []
            med_lines       = []
            raw_diff_lines  = []
            med_diff_lines  = []
            roll_mean_lines = []
            roll_std_lines  = []

            features = [raw_lines, med_lines, raw_diff_lines, med_diff_lines, roll_mean_lines, roll_std_lines]
            for j, sensor in enumerate(data):
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

                line_data = [readings, median_filter, raw_diff, med_diff, rolling_means[sensor], rolling_stds[sensor]]

                x = (0, 0, 0, 1, 1, 1)
                y = (0, 1, 2, 0, 1, 2)
                for k, feat in enumerate(features):
                    if len(feat) < 20:
                        feat.append(self.ax[x[k], y[k]].plot(line_data[k])[0])
                        self.ax[x[k], y[k]].set_title(FEATURE_TYPES[k])
                    feat[j].set_ydata(line_data[k])
                
            plt.draw()
            plt.pause(0.1)
            if i % 10 == 9:
                output = self.analyze(sensor_data)
                self.log(output)
                if verbose:
                    if output.is_anomaly:
                        self.speak(self.anom_type[output.anom_type] * 3)
            
        plt.show()

    # Returns an outcome tuple (is_anomoly, type, desc)
    # types = ["None", "Warning", "Alert", "Anomoly"]
    def analyze(self, features: dict):
        response = self.client.models.generate_content(
            model    = self.model,
            contents = f"If there are over 20 datapoints, examine the 20 datapoints at the end in comparison to the others. The following is thermal data readings from 20 sensors on a sattelite over time. Please pay special attention to both the overlying frequencies (Raw) and underlying frequencies (Median-filtered), as well as the overall trend as depicted by the differential and rolling means and averages. In the description, please describe possible explanations for any anomalies, and classify them according to urgency. There will be an increase in the median-filtered and rolling-mean that you will have to recognize around index 75-85. Repeated patterns over time may not be anomalies and just be a product of the enviroment, in which case please explain a possible cause and mark as not an anomaly. Please be sparing with marking as an anomaly. Anomalies will likely be reflected in the rolling mean. All sensors are functional. Be as brief as possible while still explaining. anom_types are 0: None ; 1: Warning; 2: Alert; 3: Urgent. JSON: {features}",
            config   = {
                "response_mime_type": "application/json",
                "response_schema": Analysis,
            },
        )

        return response.parsed

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def log(self, log_json: str) -> None:
        if log_json.anom_type != 0:
            os.system("afplay /System/Library/Sounds/Sosumi.aiff")
        print(self.colors[log_json.anom_type] + self.anom_type[log_json.anom_type])
        print(Style.RESET_ALL + f"Anomaly: {log_json.is_anomaly}")
        print(log_json.desc)
        print()
        
    def __first_derivative(self, values: list, times: list) -> list[float]:
        return [
            (values[i+1] - values[i]) / (times[i+1] - times[i])
            for i in range(len(values) - 1)
        ]