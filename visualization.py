import pandas as pd
from scipy.signal import medfilt
import numpy as np

import matplotlib.pyplot as plt

def clean_time(time: str) -> int:
    string = time[time.index(" ")+1:]
    string = int("".join(list(filter(lambda x: x in "1234567890", string))))

    return string

def remove_spikes_median(data, kernel_size=5):
    return medfilt(data, kernel_size=kernel_size)

def main() -> None:
    df          = pd.read_csv("resources/thermal_data.csv")
    sensor_data = {}
    timestamps  = []

    for i in range(20):
        sensor_data[f"SENSOR{i+1}"] = []
    
    for time in df["packet_time"]:
        timestamps.append(clean_time(time))

    for data in df["items"]:
        json = dict(eval(data))

        for i in range(20):
            sensor_data[f"SENSOR{i+1}"].append(json[f"SENSOR{i+1}"])

    print(sensor_data)

    for key in sensor_data:
        val = remove_spikes_median(sensor_data[key])
        plt.plot(val, label=key)

    plt.show()

if __name__ == '__main__':
    main()
