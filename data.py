import pandas as pd
import numpy as np
from scipy import integrate
from battery import Battery
import threading
import concurrent.futures


FILES = {
    'grid': '2021/grid.csv', 
    'solar': '2021/solar.csv'
}


OPCAO_HORARIA = {
    'vazio': (22, 8),
    'fora_de_vazio': (8, 22)
}

MULTIPLE = 4 # multiple of 500W 
BATTERY_SIZE = 5.9

PERIOD = 2  #csv files, time between entries

store = {}


def between_times(hour, start, stop):
    if (start < stop and start < hour < stop):
        return True
    if (start > stop and (hour < stop or hour > start)):
        return True
    return False

def get_data(filename):
    df = pd.read_csv(filename, dtype={'name': 'str', 'time': 'int', 'value':'int'}, parse_dates=['time'], date_parser=pd.to_datetime)

    # Clean not relevant columns
    if 'name' in df:
        del df['name']

    df = df.set_index('time').resample(str(PERIOD)+'S').ffill()

    return df

def calculate_energy(df, key):
    df['energy'] = df.apply(lambda x: x*PERIOD*2.7778E-7).bfill() # PERIOD is the delta x (see resample above), last convert Ws to kWh
    df = df.resample('30S').sum() #TODO make configurable
    return df

def main():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        print(f"LOADING CSV {[f for f in FILES.values()]}...", end='', flush=True)
        future_to_key = {executor.submit(get_data, filename): key for key, filename in FILES.items()}
        for future in concurrent.futures.as_completed(future_to_key):
            store[future_to_key[future]] = future.result()
        print("done")

        print("ReIndex Solar...", end='', flush=True)
        store['solar'] = store['solar'].reindex_like(store['grid'] )
        print("done")

        print("Calculating Energy...", end='', flush=True)
        future_to_key = {executor.submit(calculate_energy, store[key], key): key for key in FILES}
        for future in concurrent.futures.as_completed(future_to_key):
            store[future_to_key[future]] = future.result()
        print("done")


    # Process Energy Only
    house_needs = {opcao: 0 for opcao in OPCAO_HORARIA.keys()}
    meter = {opcao: 0 for opcao in OPCAO_HORARIA.keys()}
    solar_total = 0
    export_total = 0
    batt = Battery(BATTERY_SIZE) #5.9 kWh capacity

    print("Simulation running...", end='', flush=True)
    for i in store['grid'].index:
        solar = store['solar'].at[i, 'energy']
        grid = store['grid'].at[i, 'energy']
        new_solar = MULTIPLE*solar

        for tarifa in OPCAO_HORARIA.keys():
            if(between_times(i.hour, *OPCAO_HORARIA[tarifa])):
                consumption = (grid + solar)
                house_needs[tarifa] += consumption

                if (consumption - new_solar) > 0:
                    meter[tarifa] += (consumption - new_solar - batt.discharge(4900*PERIOD*2.7778E-7))

                export = (new_solar - consumption) if (new_solar - consumption) > 0 else 0
                export = batt.charge(export)
                export_total += export 
                break
        solar_total += new_solar
    print('done')

    print(f"Solar capacity installed: {MULTIPLE*500}")
    print(f"Produced Solar Energy: {solar_total:.2f}")
    print(f"Solar Energy Exported: {export_total:.2f}")
    print(f"Meter Vazio: {meter['vazio']:.2f}")
    print(f"Meter Fora de Vazio: {meter['fora_de_vazio']:.2f}")
    print(f"Battery Energy supplied: {batt.total_energy_supplied:.2f}")

if __name__ == "__main__":
    main()