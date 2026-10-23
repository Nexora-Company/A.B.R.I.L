"""Optimización CPU tests."""

from __future__ import annotations

from abril.services.hardware import HardwareProfile
from abril.services.cpu_opt import CPUOptimization, optimize_for_profile


def test_optimize_for_profile_returns_optimization():
    profile = HardwareProfile(cpu_cores=4, cpu_threads=8, ram_gb=16.0)
    opt = optimize_for_profile(profile)

    assert isinstance(opt, CPUOptimization)
    assert opt.num_threads > 0
    assert "OMP_NUM_THREADS" in opt.env_vars
    assert "num_thread" in opt.ollama_options
    assert "num_batch" in opt.ollama_options
    assert "use_mmap" in opt.ollama_options


def test_low_tier_reduces_threads_and_batch():
    profile = HardwareProfile(cpu_cores=2, cpu_threads=2, ram_gb=4.0)
    opt = optimize_for_profile(profile)

    assert opt.ollama_options["num_thread"] <= profile.cpu_threads // 2
    assert opt.ollama_options["num_batch"] <= 256


def test_gpu_tier_sets_num_gpu():
    profile = HardwareProfile(cpu_cores=8, cpu_threads=16, ram_gb=32.0, has_gpu=True, gpu_vram_gb=8.0)
    opt = optimize_for_profile(profile)

    assert opt.ollama_options.get("num_gpu") == -1
    assert opt.ollama_options["num_thread"] <= profile.cpu_threads // 4