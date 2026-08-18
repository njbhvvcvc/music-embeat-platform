import os
import json
import logging
import torch
import torch.nn as nn

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeatMLP(nn.Module):
    def __init__(self, config: dict = None):
        super().__init__()
        cfg = config or {}
        discrete_input = cfg.get("discrete_input_dim", 20)
        acoustic_input = cfg.get("acoustic_input_dim", 7)
        hidden_dim = cfg.get("hidden_dim", 64)
        output_dim = cfg.get("output_dim", 64)

        self.discrete_emb = nn.Sequential(
            nn.Linear(discrete_input, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.PReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
        )
        self.acoustic_emb = nn.Sequential(
            nn.Linear(acoustic_input, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.PReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
        )
        self.backbone = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim * 2),
            nn.BatchNorm1d(hidden_dim * 2),
            nn.PReLU(),
            nn.Linear(hidden_dim * 2, output_dim),
        )

    def forward(self, discrete: torch.Tensor, acoustic: torch.Tensor) -> torch.Tensor:
        d = self.discrete_emb(discrete)
        a = self.acoustic_emb(acoustic)
        x = torch.cat([d, a], dim=1)
        x = self.backbone(x)
        return nn.functional.normalize(x, p=2, dim=1)


class ModelLoader:
    DISCRETE_KEYS = [
        "key", "mode", "time_signature", "tempo"
    ]
    # 扩展离散特征到 20 维（one-hot 编码后的维度）
    ACOUSTIC_KEYS = [
        "energy", "valence", "danceability",
        "loudness", "speechiness", "acousticness", "instrumentalness"
    ]

    def __init__(self):
        self.model: EmbeatMLP | None = None
        self.config: dict = {}
        self._loaded = False

    def load(self):
        model_path = settings.embeat_model_path
        weights_path = os.path.join(model_path, "model.pt")
        config_path = os.path.join(model_path, "config.json")

        if not os.path.exists(weights_path):
            logger.warning(f"Model weights not found at {weights_path}, running without model")
            self._loaded = False
            return

        try:
            # 加载配置
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "discrete_input_dim": 20,
                    "acoustic_input_dim": 7,
                    "hidden_dim": 64,
                    "output_dim": 64,
                }

            self.model = EmbeatMLP(self.config)
            self.model.eval()
            state_dict = torch.load(weights_path, map_location="cpu", weights_only=True)
            self.model.load_state_dict(state_dict, strict=False)
            self._loaded = True
            logger.info(f"EmbeatMLP loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def encode(self, discrete: list[float], acoustic: list[float]) -> list[float]:
        if self.model is None:
            raise RuntimeError("Model not loaded")
        with torch.no_grad():
            d = torch.tensor([discrete], dtype=torch.float32)
            a = torch.tensor([acoustic], dtype=torch.float32)
            vec = self.model(d, a)
            return vec[0].tolist()

    def encode_from_features(self, features: dict) -> list[float]:
        """从 Spotify 音频特征字典生成向量"""
        discrete = self._extract_discrete(features)
        acoustic = self._extract_acoustic(features)
        return self.encode(discrete, acoustic)

    def _extract_discrete(self, features: dict) -> list[float]:
        """提取离散特征（20 维）"""
        # key: 0-11 -> one-hot 12
        # mode: 0/1 -> 2
        # time_signature: 3-7 -> 5
        # tempo: 离散化到 1 维
        vec = [0.0] * 20

        key = features.get("key", 0)
        if 0 <= key <= 11:
            vec[key] = 1.0

        mode = features.get("mode", 0)
        vec[12 + mode] = 1.0

        ts = features.get("time_signature", 4)
        if 3 <= ts <= 7:
            vec[14 + (ts - 3)] = 1.0

        tempo = features.get("tempo", 120)
        # tempo 归一化到 0-1
        vec[19] = min(max(tempo / 200.0, 0.0), 1.0)

        return vec

    def _extract_acoustic(self, features: dict) -> list[float]:
        """提取连续特征（7 维）"""
        return [
            features.get("energy", 0.5),
            features.get("valence", 0.5),
            features.get("danceability", 0.5),
            (features.get("loudness", -10.0) + 60.0) / 60.0,  # -60 到 0 -> 0-1
            features.get("speechiness", 0.0),
            features.get("acousticness", 0.5),
            features.get("instrumentalness", 0.0),
        ]