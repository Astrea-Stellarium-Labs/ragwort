from collections import OrderedDict
import inspect

import discord

from . import slash_param

__all__ = (
    "SlashCommand",
    "slash_command",
    "command",
    "application_command",
    "ragwort_command",
    "ragwort_slash_command",
    "ragwort_application_command",
    "RagwortSlashCommand",
)


class RagwortSlashCommand(discord.SlashCommand):
    def _get_signature_parameters(self) -> OrderedDict[str, inspect.Parameter]:
        old_parameters = super()._get_signature_parameters()
        new_parameters: OrderedDict[str, inspect.Parameter] = OrderedDict()

        required_params = (
            ["self", "context"] if self.attached_to_group or self.cog else ["context"]
        )

        for index, param in enumerate(old_parameters.values()):
            if index < len(required_params):
                new_parameters[param.name] = param
                continue

            param_info: slash_param.ParamInfo = (
                param.default
                if isinstance(param.default, slash_param.ParamInfo)
                else slash_param.Option(
                    default=(
                        param.default
                        if param.default is not param.empty
                        else discord.MISSING
                    )
                )
            )

            if param.annotation is param.empty:
                if param_info.input_type is None:
                    raise ValueError(
                        f"No provided type for {param.name} for {self.qualified_name}"
                    )

            if param.annotation is not param.empty and param_info.input_type is None:
                param_info.input_type = param.annotation

            new_parameters[param.name] = param.replace(
                default=param.empty, annotation=param_info.generate_option()
            )

        return new_parameters


SlashCommand = RagwortSlashCommand


def slash_command(**kwargs):
    return discord.application_command(RagwortSlashCommand, **kwargs)


command = slash_command
application_command = slash_command
ragwort_command = slash_command
ragwort_slash_command = slash_command
ragwort_application_command = slash_command
