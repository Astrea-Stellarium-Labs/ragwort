# Ragwort

[![PyPI](https://img.shields.io/pypi/v/ragwort)](https://pypi.org/project/ragwort/)
[![Downloads](https://static.pepy.tech/personalized-badge/ragwort?period=total&units=abbreviation&left_color=grey&right_color=green&left_text=pip%20installs)](https://pepy.tech/project/ragwort)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Unstable experiments with pycord. An adaptation of [`tansy`](https://github.com/Astrea-Stellarium-Labs/tansy).

## Slash Commands

`ragwort` provides a unique way to define options for slash commands.

Instead of needing a decorator per option or to define the option in one huge list (or using awkward annotations), `ragwort` allows you to define each option in the function itself.
By using a special metadata function, you can specify what each argument/parameter in a function should be like as an option, with ragwort smartly handling the rest for you.

```python
import discord
import ragwort

bot = discord.Bot(...)

@ragwort.slash_command(description="Nice test command, huh?")
async def test(
    ctx: discord.ApplicationContext,
    the_user: discord.Member = ragwort.Option(name="user", description="The user to ping."),
):
    await ctx.respond(the_user.mention)

bot.add_application_command(test)  # only needed if the command is not in a cog
```

> [!TIP]
> You can also use `from ragwort import X` for individual imports if you prefer.
>
> `ragwort` frequently also aliases classes and functions to make overlap between `ragwort` and `discord` easier to avoid; for example, instead of `ragwort.slash_command`, you could use `ragwort_slash_command`.

### Subcommands

`ragwort` also supports defining subcommands in a similar way.

```python
# see imports from last example

math = ragwort.SlashCommandGroup("math", "Math related commands")
advanced = math.create_subgroup("advanced", "Advanced math commands")

@advanced.command()
async def square_root(
    ctx: discord.ApplicationContext,
    x: int = ragwort.Option(description="The number to find the square root of.")
):
    await ctx.respond(x ** 0.5)
```

### Bridge Commands

`ragwort` also provides support for [bridge commands](https://guide.pycord.dev/extensions/bridge):

```python
import discord
from discord.ext import bridge
import ragwort

bot = bridge.Bot(...)

@ragwort.bridge_command(description="Nice test command, huh?")
async def test(
    ctx: bridge.BridgeContext,
    the_user: discord.Member = ragwort.BridgeOption(name="user", description="The user to ping."),
):
    await ctx.respond(the_user.mention)

bot.add_bridge_command(test)  # only needed if the command is not in a cog
```

## Auto Defer

`ragwort` provides a way of making all slash commands automatically defer their responses, and the ability to change how said auto defer works at the bot, cog, and command levels.

To use auto defer, you can call the `setup_auto_defer` function with your bot instance:

```python
import discord
import ragwort

bot = discord.Bot(...)
ragwort.setup_auto_defer(bot)
```

### Bot Wide Auto Defer

By default, `setup_auto_defer` enables auto defer for all commands. However, you can change `ragwort.setup_auto_defer` to whatever you desire:

```python
ragwort.setup_auto_defer(bot, default=False)  # only defers extensions and commands marked to be autodeferred - see below
# or
ragwort.setup_auto_defer(
    bot,
    default=ragwort.AutoDefer(
        enabled=True,
        ephemeral=False,
        time_until_defer=0.0
    )  # allows more custom behavior
)
```

### Cog Wide Auto Defer

You can also set up auto defer at the cog level by using the `cog_auto_defer` decorator. This will apply the auto defer settings to all commands within that cog:

```python
@ragwort.cog_auto_defer(enabled=True, ephemeral=False, time_until_defer=0.0)
class MyCog(discord.Cog):
    @ragwort.slash_command()
    async def my_command(self, ctx: discord.ApplicationContext):
        await ctx.respond("Hello, World!")
```

### Command Level Auto Defer

Finally, you can set up auto defer at the command level by using the `auto_defer` decorator. This will apply the auto defer settings to that specific command:

```python
@ragwort.slash_command()
@ragwort.auto_defer(enabled=True, ephemeral=False, time_until_defer=0.0)
async def my_command(self, ctx: discord.ApplicationContext):
    await ctx.respond("Hello, World!")
```

### Other Notes

- Auto defer is applied in the following order: command level, then cog level, then bot level. This means that if a command has auto defer disabled (with `enabled=False`), but the cog or bot has it enabled, the command will *not* be deferred. This is useful for commands that send modals.
- Auto defer partially works with bridge commands; the slash variant of the command will be deferred, but the prefixed variant may not be.
