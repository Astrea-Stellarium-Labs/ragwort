"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development
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

import copy
import functools
import inspect
from collections import OrderedDict

import discord
import typing_extensions as typing
from discord.ext import bridge, commands
from discord.ext.bridge.core import AttachmentConverter

from . import slash_commands, slash_param

__all__ = (
    "BridgeCommand",
    "BridgeCommandGroup",
    "BridgeExtCommand",
    "BridgeExtGroup",
    "BridgeSlashCommand",
    "BridgeSlashGroup",
    "RagwortBridgeCommand",
    "RagwortBridgeCommandGroup",
    "RagwortBridgeExtCommand",
    "RagwortBridgeExtGroup",
    "RagwortBridgeSlashCommand",
    "RagwortBridgeSlashGroup",
    "bridge_command",
    "bridge_group",
    "ragwort_bridge_command",
    "ragwort_bridge_group",
)

_C = typing.TypeVar("_C", bound=typing.Callable)


def _overwrite_defaults(
    func: _C,
    parameters: typing.Mapping[str, inspect.Parameter],
) -> _C:
    func_copy = copy.copy(func)
    func_to_parse = func_copy

    partial_func = False

    if isinstance(func_copy, functools.partial):
        func_to_parse = func_copy.func
        partial_func = True

    old_kwarg_defaults = func_to_parse.__kwdefaults__ or {}

    new_defaults = []
    new_kwarg_defaults = {}

    for name, param in parameters.items():
        default = param.default

        if default is param.empty:
            continue

        if (
            old_kwarg_defaults.get(name)
            or param.kind == inspect._ParameterKind.KEYWORD_ONLY
        ):
            new_kwarg_defaults[name] = default
        else:
            new_defaults.append(default)

    func_to_parse.__defaults__ = tuple(new_defaults) if new_defaults else None
    func_to_parse.__kwdefaults__ = new_kwarg_defaults or None

    if partial_func:
        func_copy = functools.partial(
            func_to_parse, *func_copy.args, **func_copy.keywords
        )
    else:
        func_copy = func_to_parse

    return func_copy


class RagwortBridgeSlashCommand(bridge.BridgeSlashCommand):
    def _get_signature_parameters(self) -> OrderedDict[str, inspect.Parameter]:
        old_parameters: OrderedDict[str, inspect.Parameter] = (
            super()._get_signature_parameters()
        )
        new_parameters: OrderedDict[str, inspect.Parameter] = OrderedDict()

        required_params = (
            2 if self.attached_to_group or "." in self.callback.__qualname__ else 1
        )

        for index, param in enumerate(old_parameters.values()):
            if index < required_params:
                new_parameters[param.name] = param
                continue

            param_info: slash_param.BridgeParamInfo = (
                param.default
                if isinstance(param.default, slash_param.BridgeParamInfo)
                else slash_param.BridgeOption(
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

            new_parameters[param.name] = param.replace(
                default=param.empty, annotation=param_info.generate_option()
            )

        return new_parameters


class RagwortBridgeExtCommand(commands.Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)

        for option in self.params.values():
            if isinstance(option.annotation, discord.Option) and not isinstance(
                option.annotation, bridge.BridgeOption
            ):
                raise TypeError(
                    f"{option.annotation.__class__.__name__} is not supported in bridge"
                    " commands. Use BridgeOption instead."
                )

        self._callback = _overwrite_defaults(self.callback, self.params)

    @property
    def params(self) -> dict[str, inspect.Parameter]:
        return self._params

    @params.setter
    def params(self, old_parameters: dict[str, inspect.Parameter]) -> None:
        new_parameters: dict[str, inspect.Parameter] = {}

        required_params = 2 if "." in self.callback.__qualname__ else 1

        for index, param in enumerate(old_parameters.values()):
            if index < required_params:
                new_parameters[param.name] = param
                continue

            param_info: slash_param.BridgeParamInfo = (
                param.default
                if isinstance(param.default, slash_param.BridgeParamInfo)
                else slash_param.BridgeOption(
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

            new_parameters[param.name] = param.replace(
                default=(
                    option.default
                    if option.default is not discord.MISSING
                    else param.empty
                ),
                annotation=option,
            )

        self._params = new_parameters

    async def dispatch_error(
        self, ctx: bridge.BridgeExtContext, error: Exception
    ) -> None:
        await super().dispatch_error(ctx, error)
        ctx.bot.dispatch("bridge_command_error", ctx, error)

    async def transform(
        self, ctx: commands.Context, param: inspect.Parameter
    ) -> typing.Any:
        if param.annotation is discord.Attachment:
            # skip the parameter checks for bridge attachments
            return await commands.run_converters(ctx, AttachmentConverter, None, param)
        return await super().transform(ctx, param)


class RagwortBridgeSlashGroup(slash_commands.SlashCommandGroup):
    """A subclass of :class:`.SlashCommandGroup` that is used for bridge commands."""

    __slots__ = ("module",)

    def __init__(self, callback, *args, **kwargs):
        if perms := getattr(callback, "__default_member_permissions__", None):
            kwargs["default_member_permissions"] = perms
        super().__init__(*args, **kwargs)
        self.callback = callback
        self.__original_kwargs__["callback"] = callback
        self.__command = None

    async def _invoke(self, ctx: bridge.BridgeApplicationContext) -> None:
        if not (options := ctx.interaction.data.get("options")):
            if not self.__command:
                self.__command = RagwortBridgeSlashCommand(self.callback)
            ctx.command = self.__command
            return await ctx.command.invoke(ctx)
        option = options[0]
        resolved = ctx.interaction.data.get("resolved", None)
        command = discord.utils.find(
            lambda x: x.name == option["name"], self.subcommands
        )
        option["resolved"] = resolved
        ctx.interaction.data = option
        await command.invoke(ctx)


class RagwortBridgeExtGroup(RagwortBridgeExtCommand, commands.Group):
    pass


class RagwortBridgeCommand(bridge.BridgeCommand):
    def __init__(self, callback, **kwargs):
        kwargs["slash_variant"] = kwargs.get(
            "slash_variant", RagwortBridgeSlashCommand(callback, **kwargs)
        )
        kwargs["ext_variant"] = kwargs.get(
            "ext_variant", RagwortBridgeExtCommand(callback, **kwargs)
        )
        super().__init__(callback, **kwargs)


class RagwortBridgeCommandGroup(RagwortBridgeCommand):
    __special_attrs__ = [
        "slash_variant",
        "ext_variant",
        "parent",
        "subcommands",
        "mapped",
    ]

    ext_variant: RagwortBridgeExtGroup
    slash_variant: RagwortBridgeSlashGroup

    def __init__(self, callback, *_, **kwargs):
        ext_var = RagwortBridgeExtGroup(callback, **kwargs)
        kwargs.update({"name": ext_var.name})
        super().__init__(
            callback,
            ext_variant=ext_var,
            slash_variant=RagwortBridgeSlashGroup(callback, **kwargs),
            parent=kwargs.pop("parent", None),
        )

        self.subcommands: list[bridge.BridgeCommand] = []

        self.mapped: discord.SlashCommand | None = None
        if map_to := getattr(callback, "__custom_map_to__", None):
            kwargs.update(map_to)
            self.mapped = self.slash_variant.command(**kwargs)(callback)

    def walk_commands(self) -> typing.Iterator[bridge.BridgeCommand]:
        yield from self.subcommands

    def command(self, *args, **kwargs):
        def wrap(callback):
            slash = self.slash_variant.command(
                *args,
                **kwargs,
                cls=RagwortBridgeSlashCommand,
            )(callback)
            ext = self.ext_variant.command(
                *args,
                **kwargs,
                cls=RagwortBridgeExtCommand,
            )(callback)
            command = RagwortBridgeCommand(
                callback, parent=self, slash_variant=slash, ext_variant=ext
            )
            self.subcommands.append(command)
            return command

        return wrap


def bridge_command(**kwargs):
    def decorator(callback):
        return RagwortBridgeCommand(callback, **kwargs)

    return decorator


def bridge_group(**kwargs):
    def decorator(callback):
        return RagwortBridgeCommandGroup(callback, **kwargs)

    return decorator


BridgeSlashCommand = RagwortBridgeSlashCommand
BridgeExtCommand = RagwortBridgeExtCommand
BridgeSlashGroup = RagwortBridgeSlashGroup
BridgeExtGroup = RagwortBridgeExtGroup
BridgeCommand = RagwortBridgeCommand
BridgeCommandGroup = RagwortBridgeCommandGroup
ragwort_bridge_command = bridge_command
ragwort_bridge_group = bridge_group
