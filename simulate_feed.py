import pandas as pd

def clean_time(time: str) -> int:
    string = time[time.index(" ")+1:]
    string = int("".join(list(filter(lambda x: x in "1234567890", string))))

    return string

def get_data(path: str = "resources/thermal_data.csv", stream: bool = False):
    df          = pd.read_csv(path)
    sensor_data = {}
    timestamps  = []
    states      = []

    for i in range(20):
        sensor_data[f"SENSOR{i+1}"] = []
    
    for time in df["packet_time"]:
        timestamps.append(clean_time(time))

    for data in df["items"]:
        json = dict(eval(data))

        for i in range(20):
            sensor_data[f"SENSOR{i+1}"].append(json[f"SENSOR{i+1}"])
        
        states.append((timestamps, sensor_data))

    if stream:
        return states

