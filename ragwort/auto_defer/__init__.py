"""
The MIT License (MIT)

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

import asyncio
import contextlib

import discord
import typing_extensions as typing

__all__ = ("AutoDefer", "auto_defer", "cog_auto_defer", "setup_auto_defer")


_SlashCommandT = typing.TypeVar(
    "_SlashCommandT",
    bound=discord.SlashCommand | typing.Callable[..., typing.Coroutine],
)

_CogTypeT = typing.TypeVar("_CogTypeT", bound=type[discord.Cog])


class AutoDefer:
    def __init__(
        self,
        enabled: bool = True,
        ephemeral: bool = False,
        time_until_defer: float = 0.0,
    ) -> None:
        self.enabled = enabled
        self.ephemeral = ephemeral
        self.time_until_defer = time_until_defer

    def __repr__(self) -> str:
        return (
            f"AutoDefer(enabled={self.enabled}, ephemeral={self.ephemeral},"
            f" time_until_defer={self.time_until_defer})"
        )

    async def __call__(self, ctx: discord.ApplicationContext) -> None:
        if self.enabled:
            if self.time_until_defer > 0:
                loop = asyncio.get_event_loop()
                loop.call_later(
                    self.time_until_defer, loop.create_task, self.defer(ctx)
                )
            else:
                await self.defer(ctx)

    async def defer(self, ctx: discord.ApplicationContext) -> None:
        if not ctx.response.is_done():
            with contextlib.suppress(
                discord.InteractionResponded, discord.HTTPException
            ):
                await ctx.defer(ephemeral=self.ephemeral)


def auto_defer(
    enabled: bool = True, ephemeral: bool = False, time_until_defer: float = 0.0
) -> typing.Callable[[_SlashCommandT], _SlashCommandT]:
    def wrapper(func: _SlashCommandT) -> _SlashCommandT:
        if isinstance(func, discord.SlashCommand):
            func._callback.__auto_defer__ = AutoDefer(
                enabled=enabled, ephemeral=ephemeral, time_until_defer=time_until_defer
            )
        else:
            func.__auto_defer__ = AutoDefer(
                enabled=enabled, ephemeral=ephemeral, time_until_defer=time_until_defer
            )
        return func

    return wrapper


def add_cog_auto_defer(
    cog: discord.Cog | type[discord.Cog],
    enabled: bool = True,
    ephemeral: bool = False,
    time_until_defer: float = 0.0,
) -> None:
    cog.__cog_auto_defer__ = AutoDefer(
        enabled=enabled, ephemeral=ephemeral, time_until_defer=time_until_defer
    )


def cog_auto_defer(
    enabled: bool = True, ephemeral: bool = False, time_until_defer: float = 0.0
) -> typing.Callable[[_CogTypeT], _CogTypeT]:
    def wrapper(cls: _CogTypeT) -> _CogTypeT:
        add_cog_auto_defer(
            cls, enabled=enabled, ephemeral=ephemeral, time_until_defer=time_until_defer
        )
        return cls

    return wrapper


def _wrap_invoke_application_command(
    original_invoke: typing.Callable[
        [discord.ApplicationContext], typing.Awaitable[None]
    ],
):
    async def new_invoke(ctx: discord.ApplicationContext) -> None:
        if (
            ctx.command is not None
            and (
                cmd_auto_defer := getattr(ctx.command.callback, "__auto_defer__", None)
            )
            is not None
        ):
            await cmd_auto_defer(ctx)
        elif (
            ctx.cog is not None
            and (cog_auto_defer := getattr(ctx.cog, "__cog_auto_defer__", None))
            is not None
        ):
            await cog_auto_defer(ctx)
        elif (
            default_auto_defer := getattr(ctx.bot, "__default_auto_defer__", None)
        ) is not None:
            await default_auto_defer(ctx)

        await original_invoke(ctx)

    return new_invoke


def setup_auto_defer(bot: discord.Bot, *, default: AutoDefer | bool = True) -> None:
    if default is not False:
        if default is True:
            default = AutoDefer()

        bot.__default_auto_defer__ = default

    bot.invoke_application_command = _wrap_invoke_application_command(
        bot.invoke_application_command
    )
