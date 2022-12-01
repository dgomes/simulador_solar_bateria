import argparse
import pandas as pd
from itertools import pairwise
from statistics import mean, stdev
from battery import Battery
import concurrent.futures

# DEFAULTS:
OPCAO_HORARIA = {"vazio": (22, 8), "fora_de_vazio": (8, 22)}  # Bi-Horario
CSV_FILE_DATA_INTERVAL = 2  # csv files, time between entries
ENERGY_SAMPLE_WINDOW = 10  # impacts speed of the program
BAT_INPUT_OUTPUT_POWER = 3500  # Watt


def between_times(hour, start, stop):
    if start < stop and start < hour < stop:
        return True
    if start > stop and (hour < stop or hour > start):
        return True
    return False


def get_data(filename, interval):
    df = pd.read_csv(
        filename,
        dtype={"name": "str", "time": "int", "value": "int"},
        parse_dates=["time"],
        date_parser=pd.to_datetime,
    )

    # Clean not relevant columns
    if "name" in df:
        del df["name"]

    # Sample first 5 entries to determine data intervals
    sample = [row["time"].timestamp() for _, row in df.head(5).iterrows()]
    intervals = [b - a for (a, b) in pairwise(sample)]
    if stdev(intervals) <= 1:
        interval = round(mean(intervals))

    df = df.set_index("time").resample(str(interval) + "S").ffill()

    return interval, df


def calculate_energy(df, interval):
    df["energy"] = df.apply(
        lambda x: x * interval * 2.7778e-7
    ).bfill()  # PERIOD is the delta x (see resample above), last convert Ws to kWh
    df = df.resample(str(ENERGY_SAMPLE_WINDOW) + "S").sum()
    return df


def main(to_install_solar, battery_size, battery_power, csvs, installed_solar):
    store = {}
    dataframe_interval = CSV_FILE_DATA_INTERVAL

    print(f"LOADING CSV {[f for f in csvs.values()]}...", end="", flush=True)
    for key, filename in csvs.items():
        interval, store[key] = get_data(filename, dataframe_interval)
        if interval < dataframe_interval:
            dataframe_interval = interval
    print("done")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        print("ReIndex Solar...", end="", flush=True)
        store["solar"] = store["solar"].reindex_like(store["grid"])
        print("done")

        print("Calculating Energy...", end="", flush=True)
        future_to_key = {
            executor.submit(calculate_energy, store[key], dataframe_interval): key
            for key in csvs
        }
        for future in concurrent.futures.as_completed(future_to_key):
            store[future_to_key[future]] = future.result()
        print("done")

    # Process Energy Only
    house_needs = {opcao: 0 for opcao in OPCAO_HORARIA.keys()}
    meter = {opcao: 0 for opcao in OPCAO_HORARIA.keys()}
    solar_original = 0
    solar_total = 0
    export_total = 0
    batt = Battery(
        battery_size, battery_power * dataframe_interval * 2.7778e-7
    )  # 5.9 kWh capacity

    print("Simulation running...", end="", flush=True)
    for i in store["grid"].index:
        solar = store["solar"].at[i, "energy"]
        grid = store["grid"].at[i, "energy"]
        solar_original += solar

        new_solar = to_install_solar * solar / installed_solar
        solar_total += new_solar

        for tarifa in OPCAO_HORARIA.keys():
            if between_times(i.hour, *OPCAO_HORARIA[tarifa]):
                consumption = grid + solar
                house_needs[tarifa] += consumption

                if (consumption - new_solar) > 0:
                    meter[tarifa] += (
                        consumption
                        - new_solar
                        - batt.discharge(battery_power * dataframe_interval * 2.7778e-7)
                    )

                if (new_solar - consumption) > 0:
                    export_total += batt.charge(
                        new_solar - consumption
                    )  # if battery full export energy
                break
    print("done\n")

    print(f"Energia Solar Actualmente Produzida,    {solar_original:.2f}")
    print(f"Consumo em Vazio,   {house_needs['vazio']:.2f},")
    print(f"Consumo Fora de Vazio,  {house_needs['fora_de_vazio']:.2f},")
    print(
        f"Energia Solar Produzida ({to_install_solar}W instalados),   {solar_total:.2f}"
    )
    print(f"Energia Solar Exportada,    {export_total:.2f}")
    print(f"Energia Importada em Vazio, {meter['vazio']:.2f}")
    print(f"Energia Importada em Fora de Vazio, {meter['fora_de_vazio']:.2f}")
    print(
        f"Energia Consumida da Bateria ({battery_size}kWh instalados),    {batt.total_energy_supplied:.2f}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("solar", help="Potencia Fotovoltaico a instalar", type=int)
    parser.add_argument(
        "installed_solar", help="Potencia Fotovoltaico instalada", type=int
    )
    parser.add_argument(
        "csv_rede", help="Ficheiro CSV com medidas de potência da rede", type=str
    )
    parser.add_argument(
        "csv_solar",
        help="Ficheiro CSV com medidas de potência da produção solar",
        type=str,
    )
    parser.add_argument(
        "--bateria", help="Capacidade da Bateria a instalar", type=float, default=0
    )
    parser.add_argument(
        "--potencia-bateria",
        help="Potencia Bateria a instalar",
        type=float,
        default=BAT_INPUT_OUTPUT_POWER,
    )

    args = parser.parse_args()

    csvs = {"grid": args.csv_rede, "solar": args.csv_solar}

    main(args.solar, args.bateria, args.potencia_bateria, csvs, args.installed_solar)
