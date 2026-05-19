import discord
import typing_extensions as typing
from discord.ext import bridge, commands

if typing.TYPE_CHECKING:
    from discord.commands.options import AutocompleteFunction, InputType

__all__ = (
    "BridgeOption",
    "BridgeParamInfo",
    "Option",
    "ParamInfo",
    "RagwortBridgeOption",
    "RagwortBridgeParamInfo",
    "RagwortOption",
    "RagwortParamInfo",
)


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
        autocomplete: "AutocompleteFunction | None" = None,
        min_value: float | None,
        max_value: float | None,
        min_length: int | None,
        max_length: int | None,
        channel_types: list[discord.ChannelType] | None,
        name_localizations: dict[str, str],
        description_localizations: dict[str, str],
        **kwargs: typing.Any,
    ) -> None:
        self.input_type = input_type
        self.name = name
        self.description = description
        self.choices = choices
        self.default = default
        self.required = required
        self.autocomplete = autocomplete
        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.channel_types = channel_types
        self.name_localizations = name_localizations
        self.description_localizations = description_localizations
        self.kwargs = kwargs

    @property
    def option_class(self) -> type[discord.Option]:
        return discord.Option

    def generate_option(self) -> discord.Option:
        kwargs: dict[str, typing.Any] = {
            "name": self.name,
            "description": self.description,
            "choices": self.choices,
            "default": self.default,
            "required": self.required,
            "autocomplete": self.autocomplete,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "channel_types": self.channel_types,
            "name_localizations": self.name_localizations,
            "description_localizations": self.description_localizations,
        }
        kwargs.update(self.kwargs)

        if self.input_type is None:
            raise ValueError(f"input_type must be provided for {self.name}.")
        else:
            if typing.get_origin(self.input_type) is typing.Annotated:
                self.input_type = typing.get_args(self.input_type)[1]

        if self.choices is None:
            kwargs.pop("choices")
        if self.default is discord.MISSING:
            kwargs.pop("default")
        if self.kwargs.get("converter") is None:
            kwargs.pop("converter", None)

        return self.option_class(self.input_type, **kwargs)


class BridgeParamInfo(ParamInfo):
    @property
    def option_class(self) -> type[bridge.BridgeOption]:
        return bridge.BridgeOption


def Option(
    description: str | None = None,
    *,
    input_type: "InputType | None" = None,
    name: str | None = None,
    choices: list[discord.OptionChoice | typing.Any] | None = None,
    default: typing.Any = discord.MISSING,
    required: bool = True,
    autocomplete: "AutocompleteFunction | None" = None,
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
        autocomplete=autocomplete,
        min_value=min_value,
        max_value=max_value,
        min_length=min_length,
        max_length=max_length,
        channel_types=channel_types,
        name_localizations=name_localizations,
        description_localizations=description_localizations,
    )


def BridgeOption(
    description: str | None = None,
    *,
    input_type: "InputType | None" = None,
    converter: "commands.Converter | None" = None,
    name: str | None = None,
    choices: list[discord.OptionChoice | typing.Any] | None = None,
    default: typing.Any = discord.MISSING,
    required: bool = True,
    autocomplete: "AutocompleteFunction | None" = None,
    min_value: float | None = None,
    max_value: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    channel_types: list[discord.ChannelType] | None = None,
    name_localizations: dict[str, str] = discord.MISSING,
    description_localizations: dict[str, str] = discord.MISSING,
) -> typing.Any:
    return BridgeParamInfo(
        input_type=input_type,
        name=name,
        description=description,
        choices=choices,
        default=default,
        required=required,
        autocomplete=autocomplete,
        min_value=min_value,
        max_value=max_value,
        min_length=min_length,
        max_length=max_length,
        channel_types=channel_types,
        name_localizations=name_localizations,
        description_localizations=description_localizations,
        converter=converter,
    )


RagwortOption = Option
RagwortParamInfo = ParamInfo
RagwortBridgeOption = BridgeOption
RagwortBridgeParamInfo = BridgeParamInfo
