import random
import time

class BinSimulator:
    def __init__(self, bin_id="bin_node_1", total_height=30.0, full_threshold=5.0):
        self.bin_id = bin_id
        self.total_height = total_height
        self.full_threshold = full_threshold
        
        # State: 'empty', 'half-full', 'nearly-full', 'full', 'dynamic'
        self.mode = "dynamic" 
        self.current_fill_percentage = 10.0 # start at 10%
        
        # Environment baseline
        self.base_temp = 25.0
        self.base_humidity = 60.0
        self.base_gas = 10.0

    def set_mode(self, mode):
        """Sets the simulation mode."""
        valid_modes = ["empty", "half-full", "nearly-full", "full", "dynamic"]
        if mode in valid_modes:
            self.mode = mode
            if mode == "empty":
                self.current_fill_percentage = random.uniform(5.0, 15.0)
            elif mode == "half-full":
                self.current_fill_percentage = random.uniform(45.0, 55.0)
            elif mode == "nearly-full":
                self.current_fill_percentage = random.uniform(75.0, 84.0)
            elif mode == "full":
                self.current_fill_percentage = random.uniform(85.0, 100.0)
        else:
            raise ValueError(f"Invalid mode. Choose from {valid_modes}")

    def update(self):
        """Simulates one time-step update of the sensor readings."""
        if self.mode == "dynamic":
            # Gradually increase fill percentage (simulate trash being thrown)
            self.current_fill_percentage += random.uniform(0.5, 3.0)
            if self.current_fill_percentage > 100.0:
                self.current_fill_percentage = 100.0
        
        # Calculate distance based on fill percentage
        # fill % = (total_height - distance) / (total_height - full_threshold) * 100
        # distance = total_height - (fill % * (total_height - full_threshold) / 100)
        usable_range = self.total_height - self.full_threshold
        distance = self.total_height - (self.current_fill_percentage / 100.0 * usable_range)
        # Add slight measurement noise
        distance += random.uniform(-0.2, 0.2)
        distance = max(self.full_threshold, min(self.total_height, distance))
        
        # Recalculate percentage based on noisy distance
        fill_percentage = ((self.total_height - distance) / usable_range) * 100.0
        fill_percentage = max(0.0, min(100.0, fill_percentage))
        
        # Environmental conditions fluctuate based on fill level (organic decomposition)
        temp_modifier = (fill_percentage / 100.0) * 5.0 # up to +5 degrees
        hum_modifier = (fill_percentage / 100.0) * 15.0 # up to +15% humidity
        gas_modifier = (fill_percentage / 100.0) * 60.0 # up to +60% foul gases (CO2/ammonia proxy)

        temperature = self.base_temp + temp_modifier + random.uniform(-0.5, 0.5)
        humidity = self.base_humidity + hum_modifier + random.uniform(-1.0, 1.0)
        gas_level = self.base_gas + gas_modifier + random.uniform(-2.0, 2.0)
        
        humidity = min(100.0, max(0.0, humidity))
        gas_level = min(100.0, max(0.0, gas_level))

        # Status categorization
        if fill_percentage < 50.0:
            status = "Empty"
        elif fill_percentage >= 50.0 and fill_percentage < 80.0:
            status = "Half Full"
        else:
            status = "Full"

        alert_triggered = fill_percentage >= 80.0

        return {
            "bin_id": self.bin_id,
            "distance": round(distance, 1),
            "fill_percentage": round(fill_percentage, 1),
            "status": status,
            "temp": round(temperature, 1),
            "humidity": round(humidity, 1),
            "gas_level": round(gas_level, 1),
            "alert_triggered": alert_triggered
        }

if __name__ == "__main__":
    sim = BinSimulator()
    print("Testing Simulator:")
    for _ in range(5):
        print(sim.update())
        time.sleep(0.5)
