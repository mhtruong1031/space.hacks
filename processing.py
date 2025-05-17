import statistics

from simulate_feed import get_data
from scipy.signal import medfilt


DATA_PATH = 'resources/thermal_data.csv'

def main() -> None:
    time_states = get_data(DATA_PATH, stream = True)
    means       = []

    # Set up feature extractions [raw, median_filter, rolling_mean, diff]
    for state in time_states:
        time = state[0]
        data = state[1]

        for sensor in data:
            readings = data[sensor]

            # Median Filter
            median_filter = medfilt(readings, kernel_size=5)

            # Differential
            raw_diff = first_derivative(readings, time)
            med_diff = first_derivative(median_filter, time)

            # // Underlying Frequency Features // 
            # Rolling mean on MF
            tail  = median_filter[-5:]               
            mean  = sum(tail) / len(tail)    
            means.append(mean)

            # Rolling STD
            std = rolling_std(median_filter, window = 5)

            

def analyze(features: dict):
    pass


def rolling_std(data, window: int = 3):
    result = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        window_vals = data[start:i+1]
        if len(window_vals) >= 2:
            result.append(statistics.stdev(window_vals))
        else:
            result.append(None)  # not enough data for std
    return result

def remove_spikes_median(data, kernel_size:int = 5) -> list[int]:
    return medfilt(data, kernel_size=kernel_size)

def first_derivative(values: list, times: list) -> list[float]:
    return [
        (values[i+1] - values[i]) / (times[i+1] - times[i])
        for i in range(len(values) - 1)
    ]

if __name__ == '__main__':
    main()