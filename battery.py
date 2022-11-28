class Battery:
    def __init__(self, usable_energy):
        self.max_capacity = usable_energy #kWh
        self.capacity = 0
        self.total_energy_supplied = 0

    def charge(self, energy):
        if self.capacity > self.max_capacity:
            return energy
        self.capacity += energy
        return 0

    def discharge(self, energy):
        if self.capacity > 0:
            self.capacity -= energy
            self.total_energy_supplied += energy
            return energy
        else:
            return 0