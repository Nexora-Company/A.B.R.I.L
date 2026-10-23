"""Perfiles de hardware tests."""

from __future__ import annotations

from unittest.mock import patch

from abril.services.hardware import HardwareProfile, detect_hardware, recommended_models, _TIER_CONFIG


def test_hardware_profile_tier_classification():
    # low
    p = HardwareProfile(cpu_cores=2, cpu_threads=2, ram_gb=4.0)
    assert p.tier == "low"
    # mid
    p = HardwareProfile(cpu_cores=4, cpu_threads=8, ram_gb=12.0)
    assert p.tier == "mid"
    # high
    p = HardwareProfile(cpu_cores=8, cpu_threads=16, ram_gb=32.0)
    assert p.tier == "high"


def test_hardware_profile_gpu_tier():
    p = HardwareProfile(cpu_cores=4, cpu_threads=8, ram_gb=16.0, has_gpu=True, gpu_vram_gb=8.0)
    assert p.tier == "gpu"


def test_detect_hardware_returns_profile():
    with patch("abril.services.hardware._detect_gpu", return_value=(False, None, None)):
        profile = detect_hardware()
    assert isinstance(profile, HardwareProfile)
    assert profile.cpu_cores > 0
    assert profile.cpu_threads > 0
    assert profile.ram_gb > 0
    assert profile.suggested_model != ""
    assert profile.target_latency_ms > 0


def test_tier_config_completeness():
    for tier in ("low", "mid", "high", "gpu"):
        cfg = _TIER_CONFIG[tier]
        assert "suggested_model" in cfg
        assert "target_latency_ms" in cfg
        assert "max_context" in cfg
        assert "num_threads" in cfg
        assert "batch_size" in cfg


def test_hardware_profile_to_dict():
    p = HardwareProfile(cpu_cores=4, cpu_threads=8, ram_gb=16.0)
    d = p.to_dict()
    assert d["cpu_cores"] == 4
    assert d["tier"] == "mid"
    assert "suggested_model" in d


def test_recommended_models_by_tier():
    assert recommended_models("low") == ("qwen2.5:0.5b", "qwen2.5:1.5b")
    assert recommended_models("mid") == ("qwen2.5:1.5b", "qwen2.5:3b")
    assert recommended_models("gpu") == ("qwen2.5:3b", "qwen2.5:7b")
    # Tier desconocido cae en mid
    assert recommended_models("desconocido") == recommended_models("mid")
