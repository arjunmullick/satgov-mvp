import os
from dataclasses import dataclass


@dataclass
class Settings:
    data_dir: str = os.getenv("DATA_DIR", "data")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    tile_size: int = int(os.getenv("TILE_SIZE", "256"))

    @property
    def aoi_dir(self) -> str:
        return os.path.join(self.data_dir, "aoi")

    @property
    def raw_dir(self) -> str:
        return os.path.join(self.data_dir, "raw")

    @property
    def interim_dir(self) -> str:
        return os.path.join(self.data_dir, "interim")

    @property
    def features_dir(self) -> str:
        return os.path.join(self.data_dir, "features")

    @property
    def labels_dir(self) -> str:
        return os.path.join(self.data_dir, "labels")

    @property
    def models_dir(self) -> str:
        return os.path.join(self.data_dir, "models")

    @property
    def tiles_dir(self) -> str:
        return os.path.join(self.data_dir, "tiles")


settings = Settings()
