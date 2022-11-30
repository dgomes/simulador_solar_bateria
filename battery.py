class Battery:
    def __init__(self, usable_energy, max_input_output_energy):
        self.max_capacity = usable_energy  # kWh
        self.capacity = 0
        self.total_energy_supplied = 0
        self.max_energy = max_input_output_energy

    def charge(self, energy):
        if self.capacity >= self.max_capacity:
            return energy

        if energy > self.max_energy:
            self.capacity += self.max_energy
            return energy - self.max_energy

        self.capacity += energy
        return 0

    def discharge(self, energy):
        if self.capacity > 0:

            if energy > self.capacity:
                provided = self.capacity
            else:
                provided = energy

            self.capacity -= provided
            self.total_energy_supplied += provided
            return provided
        else:
            return 0
