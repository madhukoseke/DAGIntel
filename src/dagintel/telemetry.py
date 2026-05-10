from dataclasses import dataclass

@dataclass  
class GPUStats:
    @property
    def display(self):
        return {"GPU util": "n/a", "VRAM util": "n/a"}

def read_gpu_stats():
    return GPUStats()
