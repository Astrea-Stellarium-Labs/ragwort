"""
Ragwort
A different way of defining slash commands in pycord."
:copyright: (c) 2026-present AstreaTSS
:license: MIT, see LICENSE for more details.
"""

__version__ = "0.1.0"


from .slash_commands import *
from .slash_param import *

__all__ = (
    "__version__",
    "SlashCommand",
    "slash_command",
    "command",
    "application_command",
    "ragwort_command",
    "ragwort_slash_command",
    "ragwort_application_command",
    "RagwortSlashCommand",
    "Option",
    "ParamInfo",
    "RagwortOption",
    "RagwortParamInfo",
)
