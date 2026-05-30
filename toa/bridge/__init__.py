"""TOA ↔ CPOS bridge (optional — requires context-pointer-os installed)"""
try:
    from .cpos_bridge import CPOSBridge
    __all__ = ["CPOSBridge"]
except ImportError:
    __all__ = []
