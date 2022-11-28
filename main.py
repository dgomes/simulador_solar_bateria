import csv
from datetime import datetime, timedelta
from pprint import pprint as pp
from dateutil.parser import parse

def readfile(filename, limit=None):
    out = []
    lines = 0
    with open(filename, "r") as file_csv:
        csv_reader = csv.reader(file_csv)
        
        for row in csv_reader:
            if row[1] == 'time':
                continue

            lines += 1
            ts = datetime.fromtimestamp(int(row[1])/1000000000)

            out.append((ts, int(row[2])))
            if lines == limit:
                return out
    return out

def power2energy(power, period):
    """Convert Power W to Energy kWh"""
    if period:
        return (power/1000) * (period.seconds/3600)
    else:
        return 0

class Battery:
    def __init__(self, usable_energy, max_power):
        self.max_capacity = usable_energy #kWh
        self.capacity = 0
        self.max_power = max_power #W

    def charge(self, energy):
        if self.capacity > self.max_capacity:
            return
        self.capacity += energy

    
    def discharge(self, energy):
        if self.capacity > 0:
            self.capacity -= energy
            return energy
        else:
            return 0


grid = readfile("grid.csv")
solar = readfile("solar.csv")

resu_6_5 = Battery(5.9, 4200)

s = iter(solar)
g = iter(grid)
stats = {
    "total_grid_vazio": 0,
    "total_grid_fora_de_vazio": 0,
    "total_batt_vazio": 0,
    "total_batt_fora_de_vazio": 0,
    "total_solar": 0,
    "current_grid_vazio": 0,
    "current_grid_fora_de_vazio": 0,
    "current_solar": 0
}


ts_g = ts_s = grid[0][0]
print("From: ", ts_g)

while True:
    try:
        if (ts_s - ts_g) > timedelta(seconds=2):
            ts_g, p_g = next(g)
        elif (ts_g - ts_s) > timedelta(seconds=2):
            ts_s, p_s = next(s)
        else:
            ts_g, p_g = next(g)
            ts_s, p_s = next(s)

        e_g = power2energy(p_g, timedelta(seconds=2))
        e_s = power2energy(p_s, timedelta(seconds=2))

        consumo = e_g + e_s
        
        extra = e_s * 4 - consumo

        if extra > 0:
            resu_6_5.charge(extra)

        else:
            batt_energy = resu_6_5.discharge(-extra)

            if batt_energy > 0:
                if ts_g.hour < 8 or ts_g.hour >= 22:
                    stats["total_batt_vazio"] += batt_energy
                else:
                    stats["total_batt_fora_de_vazio"] += batt_energy

            if batt_energy <= 0:
                if ts_g.hour < 8 or ts_g.hour >= 22:
                    stats["total_grid_vazio"] += -extra
                else:
                    stats["total_grid_fora_de_vazio"] += -extra



        if ts_g.hour < 8 or ts_g.hour >= 22:
            stats["current_grid_vazio"] += e_g
        else:
            stats["current_grid_fora_de_vazio"] += e_g

        stats["current_solar"] += e_s


    except StopIteration:
        break

price_vazio = 0.0924*1.21
price_fora_de_vazio = 0.1836*1.21

print("To: ", ts_s)
print("Solar Currently: ", stats["current_solar"] )
print("Grid Vazio Currently: ", stats["current_grid_vazio"], round(stats["current_grid_vazio"]*price_vazio, 2))
print("Grid Fora de Vazio Currently: ", stats["current_grid_fora_de_vazio"], round(stats["current_grid_fora_de_vazio"]*price_fora_de_vazio, 2))
current_cost = round(stats["current_grid_vazio"]*price_vazio, 2) + round(stats["current_grid_fora_de_vazio"]*price_fora_de_vazio, 2)
print("Current Cost = ", current_cost)
print()
print("Estimated Grid Vazio: ", stats["total_grid_vazio"], round(stats["total_grid_vazio"]*price_vazio, 2))
print("Estimated Grid Fora de Vazio: ", stats["total_grid_fora_de_vazio"], round(stats["total_grid_fora_de_vazio"]*price_fora_de_vazio, 2))
print("Estimated Cost = ", round(stats["total_grid_vazio"]*price_vazio, 2) + round(stats["total_grid_fora_de_vazio"]*price_fora_de_vazio, 2))
estimated_cost = round(stats["total_grid_vazio"]*price_vazio, 2) + round(stats["total_grid_fora_de_vazio"]*price_fora_de_vazio, 2)
print()
print("Estimated Batt Vazio: ", stats["total_batt_vazio"], round(stats["total_batt_vazio"]*price_vazio, 2))
print("Estimated Batt Fora de Vazio: ", stats["total_batt_fora_de_vazio"], round(stats["total_batt_fora_de_vazio"]*price_fora_de_vazio, 2))
print()
print("Estimated Savings:", (current_cost-estimated_cost)*10)