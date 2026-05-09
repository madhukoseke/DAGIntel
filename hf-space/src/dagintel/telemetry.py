from dataclasses import dataclass

@dataclass  
class GPUStats:
    @property
    def display(self):
        return {"GPU util": "—", "VRAM util": "—"}

def read_gpu_stats():
    return GPUStats()
