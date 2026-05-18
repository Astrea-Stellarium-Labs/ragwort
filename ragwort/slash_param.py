import typing_extensions as typing

import discord

if typing.TYPE_CHECKING:
    from discord.commands.options import InputType

__all__ = ("Option", "ParamInfo", "RagwortOption", "RagwortParamInfo")

class ParamInfo:
    __all__ = (
        "input_type",
        "name",
        "description",
        "choices",
        "default",
        "required",
        "min_value",
        "max_value",
        "min_length",
        "max_length",
        "channel_types",
        "name_localizations",
        "description_localizations",
    )

    def __init__(
        self,
        *,
        input_type: "InputType | None",
        name: str | None,
        description: str | None,
        choices: list[discord.OptionChoice | typing.Any] | None,
        default: typing.Any,
        required: bool,
        min_value: float | None,
        max_value: float | None,
        min_length: int | None,
        max_length: int | None,
        channel_types: list[discord.ChannelType] | None,
        name_localizations: dict[str, str],
        description_localizations: dict[str, str],
    ) -> None:
        self.input_type = input_type
        self.name = name
        self.description = description
        self.choices = choices
        self.default = default
        self.required = required
        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.channel_types = channel_types
        self.name_localizations = name_localizations
        self.description_localizations = description_localizations

    def generate_option(self) -> discord.Option:
        kwargs: dict[str, typing.Any] = {
            "name": self.name,
            "description": self.description,
            "choices": self.choices,
            "default": self.default,
            "required": self.required,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "channel_types": self.channel_types,
            "name_localizations": self.name_localizations,
            "description_localizations": self.description_localizations,
        }

        if self.input_type is None:
            raise ValueError(f"input_type must be provided for {self.name}.")
        else:
            if typing.get_origin(self.input_type) is typing.Annotated:
                self.input_type = typing.get_args(self.input_type)[1]

        if self.choices is None:
            kwargs.pop("choices")
        if self.default is discord.MISSING:
            kwargs.pop("default")

        return discord.Option(self.input_type, **kwargs)


def Option(
    description: str | None = None,
    *,
    input_type: "InputType | None" = None,
    name: str | None = None,
    choices: list[discord.OptionChoice | typing.Any] | None = None,
    default: typing.Any = discord.MISSING,
    required: bool = True,
    min_value: float | None = None,
    max_value: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    channel_types: list[discord.ChannelType] | None = None,
    name_localizations: dict[str, str] = discord.MISSING,
    description_localizations: dict[str, str] = discord.MISSING,
) -> typing.Any:
    return ParamInfo(
        input_type=input_type,
        name=name,
        description=description,
        choices=choices,
        default=default,
        required=required,
        min_value=min_value,
        max_value=max_value,
        min_length=min_length,
        max_length=max_length,
        channel_types=channel_types,
        name_localizations=name_localizations,
        description_localizations=description_localizations,
    )

RagwortOption = Option
RagwortParamInfo = ParamInfo