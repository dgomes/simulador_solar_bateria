# Simulador de Consumos e Produção para Habitações com paineis Fotovoltaicos e/ou Baterias

Com base em registos em CSV de consumo e produção electrica para autoconsumo, estima-se consumos e produções em caso de upgrades do sistema fotovoltaico.

# Requisitos:

2 ficheiro CSV com formato:
```csv
name,time,value
W,1546300801334963968,963
...
```

# Example:

```bash
$ python3 data.py 3200 500 2018/grid.csv 2018/solar.csv --bateria=5 --potencia-bateria=3500
LOADING CSV ['2018/grid.csv', '2018/solar.csv']...done
ReIndex Solar...done
Calculating Energy...done
Simulation running...done

Energia Solar Actualmente Produzida:    833.54
Consumo em Vazio:   3870.59:
Consumo Fora de Vazio:  3886.01:
Energia Solar Produzida (3200W instalados):   5334.64
Energia Solar Exportada:    2023.72
Energia Importada em Vazio: 3378.85
Energia Importada em Fora de Vazio: 1389.50
Energia Consumida da Bateria (5.0kWh instalados):    1416.92

```
