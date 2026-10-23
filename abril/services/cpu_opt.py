"""Optimizaciones CPU para inferencia local.

Ajustes de entorno y parámetros de Ollama para maximizar rendimiento
en CPU según el perfil de hardware detectado.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .hardware import HardwareProfile


@dataclass
class CPUOptimization:
    """Configuración de optimización para el proceso actual."""
    env_vars: dict[str, str]
    ollama_options: dict[str, int | float | bool]
    num_threads: int


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def optimize_for_profile(profile: HardwareProfile) -> CPUOptimization:
    """
    Genera variables de entorno y opciones de Ollama optimizadas para el perfil.

    Respeta variables de entorno ya definidas por el usuario.
    """
    # Threads: usa num_threads del perfil o auto-detección conservadora
    threads = profile.num_threads or min(profile.cpu_threads, 8)

    env_vars = {
        # OpenMP / MKL / BLAS
        "OMP_NUM_THREADS": str(_get_env_int("OMP_NUM_THREADS", threads)),
        "MKL_NUM_THREADS": str(_get_env_int("MKL_NUM_THREADS", threads)),
        "OPENBLAS_NUM_THREADS": str(_get_env_int("OPENBLAS_NUM_THREADS", threads)),
        "NUMEXPR_NUM_THREADS": str(_get_env_int("NUMEXPR_NUM_THREADS", threads)),
        # Evita contención de hilos en Python
        "PYTHON_THREADS": str(threads),
    }

    # Opciones Ollama (num_thread, num_batch, use_mmap, etc.)
    ollama_options: dict[str, int | float | bool] = {
        "num_thread": threads,
        "num_batch": profile.batch_size,
        "use_mmap": profile.use_mmap,
        "num_keep": 0,
    }

    # Ajustes específicos por tier
    if profile.tier == "low":
        ollama_options["num_thread"] = max(1, threads // 2)
        ollama_options["num_batch"] = min(256, profile.batch_size)
    elif profile.tier == "gpu":
        # En GPU, menos threads CPU, más batch
        ollama_options["num_thread"] = max(1, threads // 4)
        ollama_options["num_gpu"] = -1  # todas las capas a GPU

    return CPUOptimization(
        env_vars=env_vars,
        ollama_options=ollama_options,
        num_threads=threads,
    )


def apply_optimization(opt: CPUOptimization) -> None:
    """Aplica variables de entorno al proceso actual (idempotente)."""
    for k, v in opt.env_vars.items():
        if k not in os.environ:
            os.environ[k] = v


__all__ = ["CPUOptimization", "optimize_for_profile", "apply_optimization"]