"""Perfiles de hardware para selección automática de modelo y latencia objetivo.

Detecta CPU/RAM/GPU y sugiere configuración óptima. No instala nada;
solo expone información para que el router y la fábrica de proveedores la usen.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HardwareProfile:
    cpu_cores: int
    cpu_threads: int
    ram_gb: float
    has_gpu: bool = False
    gpu_name: str | None = None
    gpu_vram_gb: float | None = None
    platform: str = field(default_factory=lambda: platform.system().lower())
    arch: str = field(default_factory=lambda: platform.machine().lower())

    # Sugerencias derivadas
    suggested_model: str = ""
    target_latency_ms: int = 0
    max_context: int = 4096
    use_mmap: bool = True
    num_threads: int = 0
    batch_size: int = 512

    @property
    def tier(self) -> str:
        """Clasificación grosera: low / mid / high / gpu."""
        if self.has_gpu and self.gpu_vram_gb and self.gpu_vram_gb >= 6:
            return "gpu"
        if self.ram_gb < 8 or self.cpu_threads < 4:
            return "low"
        if self.ram_gb <= 16 or self.cpu_threads <= 8:
            return "mid"
        if self.ram_gb <= 32 or self.cpu_threads <= 16:
            return "high"
        return "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "ram_gb": self.ram_gb,
            "has_gpu": self.has_gpu,
            "gpu_name": self.gpu_name,
            "gpu_vram_gb": self.gpu_vram_gb,
            "platform": self.platform,
            "arch": self.arch,
            "suggested_model": self.suggested_model,
            "target_latency_ms": self.target_latency_ms,
            "max_context": self.max_context,
            "use_mmap": self.use_mmap,
            "num_threads": self.num_threads,
            "batch_size": self.batch_size,
            "tier": self.tier,
        }


# ── Detección ──────────────────────────────────────────────────────

def _read_cpuinfo() -> dict[str, str]:
    info: dict[str, str] = {}
    try:
        if sys.platform == "linux":
            content = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    info[k.strip()] = v.strip()
    except Exception:
        pass
    return info


def _detect_cpu() -> tuple[int, int]:
    """Devuelve (cores_physical, threads_logical)."""
    cores = 0
    threads = 0
    cpuinfo = _read_cpuinfo()
    if "cpu cores" in cpuinfo:
        try:
            cores = int(cpuinfo["cpu cores"])
        except ValueError:
            pass
    if "siblings" in cpuinfo:
        try:
            threads = int(cpuinfo["siblings"])
        except ValueError:
            pass
    # Fallback
    if threads == 0:
        threads = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
    if cores == 0:
        cores = threads // 2 or 1
    return cores, threads


def _detect_ram_gb() -> float:
    """RAM total en GB."""
    try:
        if sys.platform == "linux":
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / 1024 / 1024, 1)
    except Exception:
        pass
    # Fallback genérico
    return 8.0


def _detect_gpu() -> tuple[bool, str | None, float | None]:
    """Detecta GPU NVIDIA (nvidia-smi) o AMD (rocm-smi). Devuelve (has, name, vram_gb)."""
    # NVIDIA
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3,
        )
        if out.returncode == 0 and out.stdout.strip():
            name, mem = out.stdout.strip().split(",", 1)
            vram_mb = int(mem.strip())
            return True, name.strip(), round(vram_mb / 1024, 1)
    except Exception:
        pass
    # AMD (rocm-smi)
    try:
        out = subprocess.run(
            ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
            capture_output=True, text=True, timeout=3,
        )
        if out.returncode == 0 and "GPU" in out.stdout:
            lines = out.stdout.strip().splitlines()
            name = lines[0].split(":")[-1].strip() if lines else "AMD GPU"
            vram = 0.0
            for line in lines:
                if "VRAM" in line and "Total" in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p.isdigit():
                            vram = int(p) / 1024 / 1024
                            break
            return True, name, round(vram, 1) if vram else None
    except Exception:
        pass
    return False, None, None


# ── Perfiles sugeridos por tier ────────────────────────────────────

_TIER_CONFIG = {
    "low": {
        "suggested_model": "qwen2.5:0.5b",
        "target_latency_ms": 2000,
        "max_context": 2048,
        "num_threads": 2,
        "batch_size": 256,
    },
    "mid": {
        "suggested_model": "qwen2.5:1.5b",
        "target_latency_ms": 1200,
        "max_context": 4096,
        "num_threads": 4,
        "batch_size": 512,
    },
    "high": {
        "suggested_model": "qwen2.5:3b",
        "target_latency_ms": 800,
        "max_context": 8192,
        "num_threads": 8,
        "batch_size": 1024,
    },
    "gpu": {
        "suggested_model": "qwen2.5:7b",
        "target_latency_ms": 400,
        "max_context": 16384,
        "num_threads": 0,  # 0 = auto
        "batch_size": 2048,
    },
}


def _apply_tier(profile: HardwareProfile) -> None:
    """Rellena sugerencias basadas en tier y GPU."""
    tier = profile.tier
    if profile.has_gpu and profile.gpu_vram_gb and profile.gpu_vram_gb >= 6:
        tier = "gpu"
    cfg = _TIER_CONFIG.get(tier, _TIER_CONFIG["mid"])
    for k, v in cfg.items():
        setattr(profile, k, v)
    # Ajuste de threads si no hay GPU
    if not profile.has_gpu and profile.num_threads == 0:
        profile.num_threads = min(profile.cpu_threads, 8)


# Modelo ligero (router carril 2) y pesado (carril 3) por tier.
_TIER_MODELS = {
    "low": ("qwen2.5:0.5b", "qwen2.5:1.5b"),
    "mid": ("qwen2.5:1.5b", "qwen2.5:3b"),
    "high": ("qwen2.5:1.5b", "qwen2.5:3b"),
    "gpu": ("qwen2.5:3b", "qwen2.5:7b"),
}


def recommended_models(tier: str) -> tuple[str, str]:
    """Devuelve ``(ligero, pesado)`` según el tier de hardware detectado."""
    return _TIER_MODELS.get(tier, _TIER_MODELS["mid"])


def detect_hardware() -> HardwareProfile:
    """Detecta hardware y devuelve perfil con sugerencias."""
    cores, threads = _detect_cpu()
    ram = _detect_ram_gb()
    has_gpu, gpu_name, gpu_vram = _detect_gpu()

    profile = HardwareProfile(
        cpu_cores=cores,
        cpu_threads=threads,
        ram_gb=ram,
        has_gpu=has_gpu,
        gpu_name=gpu_name,
        gpu_vram_gb=gpu_vram,
    )
    _apply_tier(profile)
    return profile


def load_profile(path: Path) -> HardwareProfile | None:
    """Carga perfil guardado desde JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return HardwareProfile(**data)
    except Exception:
        return None


def save_profile(profile: HardwareProfile, path: Path) -> None:
    """Guarda perfil en JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def get_or_create_profile(data_dir: Path, force_refresh: bool = False) -> HardwareProfile:
    """Obtiene perfil guardado o detecta y guarda uno nuevo."""
    profile_path = data_dir / "hardware_profile.json"
    if not force_refresh:
        cached = load_profile(profile_path)
        if cached:
            return cached
    profile = detect_hardware()
    save_profile(profile, profile_path)
    return profile


__all__ = [
    "HardwareProfile",
    "detect_hardware",
    "load_profile",
    "save_profile",
    "get_or_create_profile",
    "recommended_models",
]