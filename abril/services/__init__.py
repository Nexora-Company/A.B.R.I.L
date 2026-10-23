"""Application services and business logic."""

from .actions import ActionsService, ActionError
from .chat import ChatService, InvalidConversation, SYSTEM_PROMPT
from .memory import MemoryService
from .pattern_analyzer import PatternAnalyzer
from .router import Lane, RouteDecision, route
from .hardware import HardwareProfile, detect_hardware, get_or_create_profile
from .cpu_opt import CPUOptimization, optimize_for_profile, apply_optimization
from .personality import PersonalityTemplate, TemplateConfig, build_system_prompt, suggest_template
from .policy import PermissionPolicy, PolicyDecision, ActionKind, PermissionLevel
from .privacy import enable_local_strict, is_local_strict, sanitize_ollama_env
from .untrusted import TrustLevel, ProcessedContent, process_content, tag_untrusted_in_prompt
from .sqlite_memory import SQLiteMemory, RoutineRecord
from .predictive import PredictiveEngine, Alias, Suggestion, build_predictive_engine
from .nexo_brace import NEXOBrace, NEXOBraceState, build_nexo_brace
from .nexus_lock import NEXUSLock, Device, DeviceType, AccessLevel, build_nexus_lock

__all__ = [
    "ActionsService",
    "ActionError",
    "ChatService",
    "InvalidConversation",
    "SYSTEM_PROMPT",
    "MemoryService",
    "PatternAnalyzer",
    "Lane",
    "RouteDecision",
    "route",
    "HardwareProfile",
    "detect_hardware",
    "get_or_create_profile",
    "CPUOptimization",
    "optimize_for_profile",
    "apply_optimization",
    "PersonalityTemplate",
    "TemplateConfig",
    "build_system_prompt",
    "suggest_template",
    "PermissionPolicy",
    "PolicyDecision",
    "ActionKind",
    "PermissionLevel",
    "enable_local_strict",
    "is_local_strict",
    "sanitize_ollama_env",
    "TrustLevel",
    "ProcessedContent",
    "process_content",
    "tag_untrusted_in_prompt",
    "SQLiteMemory",
    "RoutineRecord",
    "PredictiveEngine",
    "Alias",
    "Suggestion",
    "build_predictive_engine",
    "NEXOBrace",
    "NEXOBraceState",
    "build_nexo_brace",
    "NEXUSLock",
    "Device",
    "DeviceType",
    "AccessLevel",
    "build_nexus_lock",
]
