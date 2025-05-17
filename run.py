import sys

from HillBootr import HillBootr

verbose = False
if len(sys.argv) > 1:
    verbose = '-v' in sys.argv

DATA_PATH = 'resources/thermal_data.csv'

def main() -> None:
    hb = HillBootr(DATA_PATH)
    hb.run(verbose)

if __name__ == '__main__':
    main()