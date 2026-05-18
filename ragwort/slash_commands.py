import inspect
from collections import OrderedDict

import discord
import typing_extensions as typing
from discord.ext import commands

from . import slash_param

__all__ = (
    "SlashCommand",
    "SlashCommandGroup",
    "slash_command",
    "command",
    "application_command",
    "ragwort_command",
    "ragwort_slash_command",
    "ragwort_application_command",
    "RagwortSlashCommand",
    "RagwortSlashCommandGroup",
)

T = typing.TypeVar("T")


class RagwortCommandBase:
    def _get_signature_parameters(self) -> OrderedDict[str, inspect.Parameter]:
        old_parameters: OrderedDict[
            str, inspect.Parameter
        ] = super()._get_signature_parameters()
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


class RagwortSlashCommand(RagwortCommandBase, discord.SlashCommand):
    pass


class RagwortSlashCommandGroup(discord.SlashCommandGroup):
    def command(
        self, cls: type[T] = RagwortSlashCommand, **kwargs
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
