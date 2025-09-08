from __future__ import annotations

import torch
import torch.nn as nn


class TinyUNet(nn.Module):
    def __init__(self, in_ch: int = 3, out_ch: int = 1, base: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(in_ch, base, 3, padding=1), nn.ReLU(),
            nn.Conv2d(base, base, 3, padding=1), nn.ReLU())
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = nn.Sequential(
            nn.Conv2d(base, base * 2, 3, padding=1), nn.ReLU())
        self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False)
        self.out = nn.Conv2d(base * 2, out_ch, 1)

    def forward(self, x):
        e = self.encoder(x)
        b = self.bottleneck(self.pool(e))
        u = self.up(b)
        cat = torch.cat([u, e], dim=1)
        return self.out(cat)

