"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development
Copyright (c) 2023-present LordOfPolls
Copyright (c) 2026-present AstreaTSS

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import inspect
from collections import OrderedDict

import discord
import typing_extensions as typing
from discord.ext import commands

from . import slash_param

__all__ = (
    "RagwortSlashCommand",
    "RagwortSlashCommandGroup",
    "SlashCommand",
    "SlashCommandGroup",
    "application_command",
    "command",
    "ragwort_application_command",
    "ragwort_command",
    "ragwort_slash_command",
    "slash_command",
)


_T = typing.TypeVar("_T")
_AC = typing.TypeVar("_AC", bound=typing.Callable[..., typing.Coroutine])


class RagwortSlashCommand(discord.SlashCommand):
    def _get_signature_parameters(self) -> OrderedDict[str, inspect.Parameter]:
        old_parameters: OrderedDict[str, inspect.Parameter] = (
            super()._get_signature_parameters()
        )
        new_parameters: OrderedDict[str, inspect.Parameter] = OrderedDict()

        # long time no see, qualname hack
        required_params = (
            2 if self.attached_to_group or "." in self.callback.__qualname__ else 1
        )

        for index, param in enumerate(old_parameters.values()):
            if index < required_params:
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

            if param.annotation is param.empty and param_info.input_type is None:
                raise ValueError(
                    f"No provided type for {param.name} for {self.qualified_name}"
                )

            if param.annotation is not param.empty and param_info.input_type is None:
                param_info.input_type = param.annotation

            option = param_info.generate_option()
            if self.__original_kwargs__.get(f"_{option.name}_ragwort_autocomplete"):
                option.autocomplete = self.__original_kwargs__[
                    f"_{option.name}_ragwort_autocomplete"
                ]

            new_parameters[param.name] = param.replace(
                default=param.empty, annotation=option
            )

        return new_parameters

    def autocomplete(self, option_name: str) -> typing.Callable[[_AC], _AC]:
        def wrapper(call: _AC) -> _AC:
            if not inspect.iscoroutinefunction(call):
                raise TypeError("Autocomplete must be coroutine")

            if not self.options:
                raise ValueError("No options defined for this command")

            for option in self.options:
                if option.name == option_name:
                    option.autocomplete = call
                    # silly workaround to get around pycord regenerating options each time
                    self.__original_kwargs__[f"_{option_name}_ragwort_autocomplete"] = (
                        call
                    )
                    break
            else:
                raise ValueError(f"No option found for name: {option_name}")

            return call

        return wrapper


class RagwortSlashCommandGroup(discord.SlashCommandGroup):
    def command(
        self, cls: type[_T] = RagwortSlashCommand, **kwargs
    ) -> typing.Callable[[typing.Callable], RagwortSlashCommand]:
        return super().command(cls=cls, **kwargs)

    def create_subgroup(
        self,
        name: str,
        description: str | None = None,
        guild_ids: list[int] | None = None,
        **kwargs,
    ) -> "RagwortSlashCommandGroup":
        if self.parent is not None:
            raise Exception("A subcommand group cannot be added to a subcommand group")

        sub_command_group = RagwortSlashCommandGroup(
            name, description, guild_ids, parent=self, **kwargs
        )
        self.subcommands.append(sub_command_group)
        return sub_command_group

    def subgroup(
        self,
        name: str | None = None,
        description: str | None = None,
        guild_ids: list[int] | None = None,
    ) -> "typing.Callable[[type[RagwortSlashCommandGroup]], RagwortSlashCommandGroup]":
        def inner(cls: type[RagwortSlashCommandGroup]) -> RagwortSlashCommandGroup:
            group = cls(
                name or cls.__name__,
                description
                or (
                    inspect.cleandoc(cls.__doc__).splitlines()[0]
                    if cls.__doc__ is not None
                    else "No description provided"
                ),
                guild_ids=guild_ids,
                parent=self,
            )
            self.add_command(group)
            return group

        return inner


def slash_command(
    *,
    checks: (
        list[typing.Callable[[discord.ApplicationContext], bool]] | None
    ) = discord.MISSING,
    cog: discord.Cog | None = discord.MISSING,
    contexts: set[discord.InteractionContextType] | None = discord.MISSING,
    cooldown: commands.Cooldown | None = discord.MISSING,
    default_member_permissions: discord.Permissions | None = discord.MISSING,
    description: str | None = discord.MISSING,
    description_localizations: dict[str, str] | None = discord.MISSING,
    guild_ids: list[int] | None = discord.MISSING,
    guild_only: bool | None = discord.MISSING,
    integration_types: set[discord.IntegrationType] | None = discord.MISSING,
    name: str | None = discord.MISSING,
    name_localizations: dict[str, str] | None = discord.MISSING,
    nsfw: bool | None = discord.MISSING,
    parent: discord.SlashCommandGroup | None = discord.MISSING,
    **kwargs: typing.Never,
):
    return discord.application_command(
        cls=RagwortSlashCommand,
        checks=checks,
        cog=cog,
        contexts=contexts,
        cooldown=cooldown,
        default_member_permissions=default_member_permissions,
        description=description,
        description_localizations=description_localizations,
        guild_ids=guild_ids,
        guild_only=guild_only,
        integration_types=integration_types,
        name=name,
        name_localizations=name_localizations,
        nsfw=nsfw,
        parent=parent,
        **kwargs,
    )


SlashCommand = RagwortSlashCommand
SlashCommandGroup = RagwortSlashCommandGroup
command = slash_command
application_command = slash_command
ragwort_command = slash_command
ragwort_slash_command = slash_command
ragwort_application_command = slash_command
