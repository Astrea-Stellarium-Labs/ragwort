# Ragwort

[![PyPI](https://img.shields.io/pypi/v/ragwort)](https://pypi.org/project/ragwort/)
[![Downloads](https://static.pepy.tech/personalized-badge/ragwort?period=total&units=abbreviation&left_color=grey&right_color=green&left_text=pip%20installs)](https://pepy.tech/project/ragwort)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Unstable experiments with pycord. An adaptation of [`tansy`](https://github.com/Astrea-Stellarium-Labs/tansy).

## Installation

```bash
pip install ragwort
```

## Slash Commands

### Options

`ragwort` provides a different way to define options for slash commands.

Instead of needing a decorator per option or to define the option in one huge list (or using awkward annotations), `ragwort` allows you to define each option in the function itself in a sensible, typehinter-friendly way.[^1]
By using a special function, you can specify what each argument/parameter in a function should be like as an option, with `ragwort` smartly handling the rest for you.

```python
import discord
import ragwort

@ragwort.slash_command()
async def test(
    ctx: discord.ApplicationContext,
    user: discord.Member = ragwort.Option("The user to ping."),
):
    await ctx.respond(user.mention)

# bot.add_application_command(test) - only needed if the command is not in a cog
```

> [!TIP]
> You can also use `from ragwort import X` for individual imports if you prefer.
>
> `ragwort` frequently also aliases classes and functions to make overlap between `ragwort` and `discord` easier to avoid; for example, instead of `ragwort.slash_command`, you could use `ragwort_slash_command`.

#### Subcommands

`ragwort` also supports defining subcommands in a similar way.

```python
math = ragwort.SlashCommandGroup("math", "Math related commands")
advanced = math.create_subgroup("advanced", "Advanced math commands")

@advanced.command()
async def square_root(
    ctx: discord.ApplicationContext,
    x: int = ragwort.Option("The number to find the square root of.")
):
    await ctx.respond(x ** 0.5)
```

#### Bridge Commands

`ragwort` also provides support for [bridge commands](https://guide.pycord.dev/extensions/bridge):

```python
from discord.ext import bridge

@ragwort.bridge_command()
async def test_bridge(
    ctx: bridge.BridgeContext,
    user: discord.Member = ragwort.BridgeOption("The user to ping."),
):
    await ctx.respond(user.mention)

# bot.add_bridge_command(test_bridge) - only needed if the command is not in a cog
```

> [!NOTE]
> Bridge groups are also supported through `@ragwort.bridge_group`.

### Autocomplete

If you're using any of the above[^2], `ragwort` also adds a new way of handling autocomplete functions for slash commands and bridge commands:

```python
@ragwort.slash_command()
async def animal(
    ctx: discord.ApplicationContext,
    animal_type: str = ragwort.Option(
        "The type of animal.", choices=["Marine", "Land"]
    ),
    animal: str = ragwort.Option("The animal you want to pick."),
):
    await ctx.respond(
        f"You picked an animal type of `{animal_type}` that led you to pick `{animal}`!"
    )


@animal.autocomplete("animal")
async def animal_autocomplete(ctx: discord.AutocompleteContext):
    animal_type = ctx.options["animal_type"]
    if animal_type == "Marine":
        options = ["Whale", "Shark", "Fish", "Octopus", "Turtle"]
    else:
        options = ["Snake", "Wolf", "Lizard", "Lion", "Bird"]

    return [o for o in options if o.lower().startswith(ctx.value.lower())]
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
# only defers extensions and commands marked
# to be autodeferred - see the next sections
ragwort.setup_auto_defer(bot, default=False)

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
@ragwort.slash_command()  # works for normal slash commands too
@ragwort.auto_defer(enabled=True, ephemeral=False, time_until_defer=0.0)
async def my_command(self, ctx: discord.ApplicationContext):
    await ctx.respond("Hello, World!")
```

### Other Notes

- Auto defer is applied in the following order: command level, then cog level, then bot level. This means that if a command has auto defer disabled (with `enabled=False`), but the cog or bot has it enabled, the command will *not* be deferred. This is useful for commands that send modals.
- Auto defer partially works with bridge commands; the slash variant of the command will be deferred, but the prefixed variant will not be.


[^1]: While not documented anywhere, Pycord allows using `discord.Option` as a default value for parameters in a slash command function, like what `ragwort` does, and it will be properly parsed. However, this comes with a number of drawbacks; `discord.Option` expects a type to be provided to it, thus ruining much of the point of this style, typehinters will likely complain about `discord.Option` not being the correct type as a default, and bridge commands will fail. `ragwort` has none of these drawbacks.
[^2]: This type of autocomplete only works for `RagwortSlashCommand`, `RagwortSlashCommandGroup`, and the bridge command variants.