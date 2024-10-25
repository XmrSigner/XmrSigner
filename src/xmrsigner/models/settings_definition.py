from dataclasses import dataclass
from typing import Any, List, Tuple, Union
from monero.const import NET_MAIN, NET_TEST, NET_STAGE, NETS


class SettingsConstants:
    # Basic defaults
    OPTION__ENABLED = "E"
    OPTION__DISABLED = "D"
    OPTION__PROMPT = "P"
    OPTION__REQUIRED = "R"
    OPTIONS__ENABLED_DISABLED = [
        (OPTION__ENABLED, "Enabled"),
        (OPTION__DISABLED, "Disabled"),
    ]
    OPTIONS__ONLY_DISABLED = [
        (OPTION__DISABLED, "Disabled"),
    ]
    OPTIONS__PROMPT_REQUIRED_DISABLED = [
        (OPTION__PROMPT, "Prompt"),
        (OPTION__REQUIRED, "Required"),
        (OPTION__DISABLED, "Disabled"),
    ]
    OPTIONS__ENABLED_DISABLED_REQUIRED = OPTIONS__ENABLED_DISABLED +[
        (OPTION__REQUIRED, "Required"),
    ]
    OPTIONS__ENABLED_DISABLED_PROMPT = OPTIONS__ENABLED_DISABLED + [
        (OPTION__PROMPT, "Prompt"),
    ]
    ALL_OPTIONS = OPTIONS__ENABLED_DISABLED_PROMPT + [
        (OPTION__REQUIRED, "Required"),
    ]

    LANGUAGE__ENGLISH = "en"
    ALL_LANGUAGES = [
        (LANGUAGE__ENGLISH, "English"),
    ]

    XMR_DENOMINATION__XMR = "XMR"
    XMR_DENOMINATION__ATOMICUNITS = "pXMR"
    XMR_DENOMINATION__THRESHOLD = "thr"
    XMR_DENOMINATION__XMRATOMICUNITSHYBRID = "hyb"
    ALL_XMR_DENOMINATIONS = [
        (XMR_DENOMINATION__XMR, "XMR-only"),
        (XMR_DENOMINATION__ATOMICUNITS, "AtomicUnits-only"),
        (XMR_DENOMINATION__THRESHOLD, "Threshold at 0.01"),
        (XMR_DENOMINATION__XMRATOMICUNITSHYBRID, "XMR | pXMR hybrid"),
    ]

    CAMERA_ROTATION__0 = 0
    CAMERA_ROTATION__90 = 90
    CAMERA_ROTATION__180 = 180
    CAMERA_ROTATION__270 = 270
    ALL_CAMERA_ROTATIONS = [
        (CAMERA_ROTATION__0, '0°'),
        (CAMERA_ROTATION__90, '90°'),
        (CAMERA_ROTATION__180, '180°'),
        (CAMERA_ROTATION__270, '270°'),
    ]

    PERSISTENT_SETTINGS__SD_INSERTED__HELP_TEXT = 'Store Settings on SD card'
    PERSISTENT_SETTINGS__SD_REMOVED__HELP_TEXT = 'Insert SD card to enable'

    # QR code constants
    DENSITY__LOW = 'L'
    DENSITY__MEDIUM = 'M'
    DENSITY__HIGH = 'H'
    ALL_DENSITIES = [
        (DENSITY__LOW, 'Low'),
        (DENSITY__MEDIUM, 'Medium'),
        (DENSITY__HIGH, 'High'),
    ]

    # View Only Wallet QR Code Format
    VIEW_ONLY_WALLET_FORMAT_URI = 'U'
    VIEW_ONLY_WALLET_FORMAT_JSON = 'J'
    ALL_VIEW_ONLY_WALLET_FORMATS = [
        (VIEW_ONLY_WALLET_FORMAT_URI, 'WALLET URI'),
        (VIEW_ONLY_WALLET_FORMAT_JSON, 'JSON')
    ]

    # Seed-related constants
    MAINNET = NET_MAIN[0].upper()  # M
    TESTNET = NET_TEST[0].upper()  # T
    STAGENET = NET_STAGE[0].upper()  # S
    ALL_NETWORKS = [
        (MAINNET, NET_MAIN.capitalize()),
        (TESTNET, NET_TEST.capitalize()),
        (STAGENET, NET_STAGE.capitalize())
    ]

    @classmethod
    def network_name(cls, network_constant: str) -> str:
        if network == SettingsConstants.MAINNET:
            return NET_MAIN
        if network == SettingsConstants.TESTNET:
            return NET_TEST
        if network == SettingsConstants.STAGENET:
            return NET_STAGE

    WORDLIST_LANGUAGE__ENGLISH = 'en'
    WORDLIST_LANGUAGE__CHINESE_SIMPLIFIED = 'zh_Hans_CN'
    WORDLIST_LANGUAGE__CHINESE_TRADITIONAL = 'zh_Hant_TW'
    WORDLIST_LANGUAGE__FRENCH = 'fr'
    WORDLIST_LANGUAGE__ITALIAN = 'it'
    WORDLIST_LANGUAGE__JAPANESE = 'jp'
    WORDLIST_LANGUAGE__KOREAN = 'kr'
    WORDLIST_LANGUAGE__PORTUGUESE = 'pt'
    WORDLIST_LANGUAGE__DUTCH = 'nl'
    WORDLIST_LANGUAGE__GERMAN = 'de'
    WORDLIST_LANGUAGE__RUSSIAN = 'ru'
    WORDLIST_LANGUAGE__CZECH = 'cs'
    WORDLIST_LANGUAGE__SPANISH = 'es'
    WORDLIST_LANGUAGE__LOJBAN = 'lojban'
    WORDLIST_LANGUAGE__ESPERANTO = 'esperanto'
    ALL_WORDLIST_LANGUAGE_ENGLISH__NAMES = {
        WORDLIST_LANGUAGE__ENGLISH: 'English',
        WORDLIST_LANGUAGE__CHINESE_SIMPLIFIED: 'Chinese (simplified)',
        WORDLIST_LANGUAGE__CHINESE_TRADITIONAL: 'Chinese Traditional',
        WORDLIST_LANGUAGE__FRENCH: 'French',
        WORDLIST_LANGUAGE__ITALIAN: 'Italian',
        WORDLIST_LANGUAGE__JAPANESE: 'Japanese',
        WORDLIST_LANGUAGE__PORTUGUESE: 'Portuguese',
        WORDLIST_LANGUAGE__DUTCH: 'Dutch',
        WORDLIST_LANGUAGE__GERMAN: 'German',
        WORDLIST_LANGUAGE__RUSSIAN: 'Russian',
        WORDLIST_LANGUAGE__CZECH: 'Czech',
        WORDLIST_LANGUAGE__SPANISH: 'Spanish',
        WORDLIST_LANGUAGE__LOJBAN: 'Lojban',
        WORDLIST_LANGUAGE__ESPERANTO: 'Esperanto'
    }

    ALL_WORDLIST_LANGUAGE_NAMES = {
        WORDLIST_LANGUAGE__ENGLISH: 'English',
        WORDLIST_LANGUAGE__CHINESE_SIMPLIFIED: '简体中文',
        WORDLIST_LANGUAGE__CHINESE_TRADITIONAL: '繁體中文',
        WORDLIST_LANGUAGE__FRENCH: 'Français',
        WORDLIST_LANGUAGE__ITALIAN: 'Italiano',
        WORDLIST_LANGUAGE__JAPANESE: '日本語',
        WORDLIST_LANGUAGE__KOREAN: '한국어',
        WORDLIST_LANGUAGE__PORTUGUESE: 'Português',
        WORDLIST_LANGUAGE__DUTCH: 'Nederlands',
        WORDLIST_LANGUAGE__GERMAN: 'Deutsch',
        WORDLIST_LANGUAGE__RUSSIAN: 'Русский',
        WORDLIST_LANGUAGE__CZECH: 'Čeština',
        WORDLIST_LANGUAGE__SPANISH: 'Español',
        WORDLIST_LANGUAGE__LOJBAN: 'Lojban',
        WORDLIST_LANGUAGE__ESPERANTO: 'Esperanto'
    }

    MONERO_SUPPORTED_LANGUAGES = [
        WORDLIST_LANGUAGE__ENGLISH, 
        # WORDLIST_LANGUAGE__CHINESE_SIMPLIFIED, # disabled because of font
        WORDLIST_LANGUAGE__DUTCH,
        WORDLIST_LANGUAGE__ESPERANTO, 
        WORDLIST_LANGUAGE__FRENCH, 
        WORDLIST_LANGUAGE__GERMAN, 
        WORDLIST_LANGUAGE__ITALIAN, 
        # WORDLIST_LANGUAGE__JAPANESE, # disabled because of font
        WORDLIST_LANGUAGE__LOJBAN, 
        WORDLIST_LANGUAGE__PORTUGUESE, 
        WORDLIST_LANGUAGE__RUSSIAN, 
        WORDLIST_LANGUAGE__SPANISH
    ]

    @classmethod
    @property
    def MONERO_LANGUAGE_NAMES(cls) -> List[Tuple[str, str]]:
        return [(lang, cls.ALL_WORDLIST_LANGUAGE_NAMES[lang]) for lang in cls.MONERO_SUPPORTED_LANGUAGES]

    POLYSEED_SUPPORTED_LANGUAGES = [
        WORDLIST_LANGUAGE__ENGLISH,
        # WORDLIST_LANGUAGE__JAPANESE,  # disabled because of font
        # WORDLIST_LANGUAGE__KOREAN,  # disabled because of font
        WORDLIST_LANGUAGE__SPANISH,
        # WORDLIST_LANGUAGE__CHINESE_SIMPLIFIED,  # disabled because of font
        # WORDLIST_LANGUAGE__CHINESE_TRADITIONAL,  # disabled because of font
        WORDLIST_LANGUAGE__FRENCH,
        WORDLIST_LANGUAGE__ITALIAN,
        WORDLIST_LANGUAGE__GERMAN,
        WORDLIST_LANGUAGE__LOJBAN,
        WORDLIST_LANGUAGE__PORTUGUESE,
        WORDLIST_LANGUAGE__RUSSIAN,
        WORDLIST_LANGUAGE__SPANISH,
        WORDLIST_LANGUAGE__CZECH
    ]

    @classmethod
    @property
    def POLYSEED_LANGUAGE_NAMES(cls) -> List[Tuple[str, str]]:
        return [(lang, cls.ALL_WORDLIST_LANGUAGE_NAMES[lang]) for lang in cls.POLYSEED_SUPPORTED_LANGUAGES]
    
    # Individual SettingsEntry attr_names
    SETTING__LANGUAGE = "language"
    SETTING__MONERO_WORDLIST_LANGUAGE = "monero_wordlist_language"
    SETTING__POLYSEED_WORDLIST_LANGUAGE = "monero_wordlist_language"
    SETTING__PERSISTENT_SETTINGS = "persistent_settings"
    SETTING__XMR_DENOMINATION = "denomination"

    SETTING__LOW_SECURITY = 'low_security'
    SETTING__VIEW_WALLET_QR_FORMAT = 'wallet_qr_format'
    SETTING__NETWORKS = "networks"
    SETTING__QR_DENSITY = "qr_density"
    SETTING__SIG_TYPES = "sig_types"
    SETTING__MONERO_SEED_PASSPHRASE = "monero_seed_passphrase"
    SETTING__POLYSEED_PASSPHRASE = "polyseed_passphrase"
    SETTING__CAMERA_ROTATION = "camera_rotation"
    SETTING__COMPACT_SEEDQR = "compact_seedqr"
    SETTING__MESSAGE_SIGNING = "message_signing"
    SETTING__PRIVACY_WARNINGS = "privacy_warnings"
    SETTING__DIRE_WARNINGS = "dire_warnings"
    SETTING__QR_BRIGHTNESS_TIPS = "qr_brightness_tips"
    SETTING__PARTNER_LOGOS = "partner_logos"

    SETTING__DEBUG = "debug"

    # Hidden settings
    SETTING__QR_BRIGHTNESS = "qr_background_color"


    # Structural constants
    CATEGORY__SYSTEM = "system"
    CATEGORY__DISPLAY = "display"
    CATEGORY__WALLET = "wallet"
    CATEGORY__FEATURES = "features"

    VISIBILITY__GENERAL = "general"
    VISIBILITY__ADVANCED = "advanced"
    VISIBILITY__HIDDEN = "hidden"   # For data-only (e.g. custom_derivation), not configurable by the user

    TYPE__ENABLED_DISABLED = "enabled_disabled"
    TYPE__ENABLED_DISABLED_PROMPT = "enabled_disabled_prompt"
    TYPE__ENABLED_DISABLED_PROMPT_REQUIRED = "enabled_disabled_prompt_required"
    TYPE__SELECT_1 = "select_1"
    TYPE__MULTISELECT = "multiselect"
    TYPE__FREE_ENTRY = "free_entry"

    ALL_ENABLED_DISABLED_TYPES = [
        TYPE__ENABLED_DISABLED,
        TYPE__ENABLED_DISABLED_PROMPT,
        TYPE__ENABLED_DISABLED_PROMPT_REQUIRED,
    ]


@dataclass
class SettingsEntry:
    """
    Defines all the parameters for a single settings entry.

    * category: Mostly for organizational purposes when displaying options in the
        SettingsQR UI. Potentially an additional sub-level breakout in the menus
        on the device itself, too.
    
    * selection_options: May be specified as a List(Any) or List(tuple(Any, str)).
        The tuple form is to provide a human-readable display_name. Probably all
        entries should shift to using the tuple form.
    """
    category: str
    attr_name: str
    display_name: str
    abbreviated_name: str = None
    visibility: str = SettingsConstants.VISIBILITY__GENERAL
    type: str = SettingsConstants.TYPE__ENABLED_DISABLED
    help_text: str = None
    selection_options: List[Union[Tuple[Union[str, int]], str]] = None
    default_value: Any = None

    def __post_init__(self):
        if self.type == SettingsConstants.TYPE__ENABLED_DISABLED:
            self.selection_options = SettingsConstants.OPTIONS__ENABLED_DISABLED

        elif self.type == SettingsConstants.TYPE__ENABLED_DISABLED_PROMPT:
            self.selection_options = SettingsConstants.OPTIONS__ENABLED_DISABLED_PROMPT

        elif self.type == SettingsConstants.TYPE__ENABLED_DISABLED_PROMPT_REQUIRED:
            self.selection_options = SettingsConstants.ALL_OPTIONS

        # Account for List[tuple] and tuple formats as default_value        
        if type(self.default_value) == list and type(self.default_value[0]) == tuple:
            self.default_value = [v[0] for v in self.default_value]
        elif type(self.default_value) == tuple:
            self.default_value = self.default_value[0]


    @property
    def selection_options_display_names(self) -> List[str]:
        if type(self.selection_options[0]) == tuple:
            return [v[1] for v in self.selection_options]
        else:
            # Always return a copy so the original can't be altered
            return list(self.selection_options)


    def get_selection_option_value(self, i: int) -> Union[str, int, None]:
        """ Returns the value of the selection option at index `i` """
        if i >= len(self.selection_options):
            return None
        value = self.selection_options[i]
        if type(value) == tuple:
            value = value[0]
        return value
    
    def get_selection_option_display_name_by_value(self, value) -> str:
        for option in self.selection_options:
            if type(option) == tuple:
                option_value = option[0]
                display_name = option[1]
            else:
                option_value = option
                display_name = option
            if option_value == value:
                return display_name

    def get_selection_option_value_by_display_name(self, display_name: str):
        for option in self.selection_options:
            if type(option) == tuple:
                option_value = option[0]
                option_display_name = option[1]
            else:
                option_value = option
                option_display_name = option
            if option_display_name == display_name:
                return option_value

    def to_dict(self) -> dict:
        if self.selection_options:
            selection_options = []
            for option in self.selection_options:
                if type(option) == tuple:
                    value = option[0]
                    display_name = option[1]
                else:
                    display_name = option
                    value = option
                selection_options.append({
                    "display_name": display_name,
                    "value": value
                })
        else:
            selection_options = None

        return {
            "category": self.category,
            "attr_name": self.attr_name,
            "abbreviated_name": self.abbreviated_name,
            "display_name": self.display_name,
            "visibility": self.visibility,
            "type": self.type,
            "help_text": self.help_text,
            "selection_options": selection_options,
            "default_value": self.default_value,
        }



class SettingsDefinition:
    """
    Master list of all settings, their possible options, their defaults, on-device
    display strings, and enriched SettingsQR UI options.

    Used to auto-build the Settings UI menuing with no repetitive boilerplate code.

    Defines the on-disk persistent storage structure and can read that format back
    and validate the values.

    Used to generate a master json file that documents all these params which can
    then be read in by the SettingsQR UI to auto-generate the necessary html inputs.
    """
    # Increment if there are any breaking changes; write migrations to bridge from
    # incompatible prior versions.
    version: int = 1

    settings_entries: List[SettingsEntry] = [
        # General options

        SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                      attr_name=SettingsConstants.SETTING__LANGUAGE,
                      abbreviated_name="lang",
                      display_name="Language",
                      type=SettingsConstants.TYPE__SELECT_1,
                      visibility=SettingsConstants.VISIBILITY__HIDDEN,  # HIDDEN/DISABLED
                      selection_options=SettingsConstants.ALL_LANGUAGES,
                      default_value=SettingsConstants.LANGUAGE__ENGLISH),

        SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                      attr_name=SettingsConstants.SETTING__MONERO_WORDLIST_LANGUAGE,
                      abbreviated_name="m_wl_lang",
                      display_name="Mnemonic language",
                      type=SettingsConstants.TYPE__SELECT_1,
                      visibility=SettingsConstants.VISIBILITY__HIDDEN,  # HIDDEN/DISABLED
                      selection_options=SettingsConstants.MONERO_LANGUAGE_NAMES,
                      default_value=SettingsConstants.WORDLIST_LANGUAGE__ENGLISH),

        SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                      attr_name=SettingsConstants.SETTING__POLYSEED_WORDLIST_LANGUAGE,
                      abbreviated_name="ps_wl_lang",
                      display_name="Polyseed language",
                      type=SettingsConstants.TYPE__SELECT_1,
                      visibility=SettingsConstants.VISIBILITY__HIDDEN,  # HIDDEN/DISABLED
                      selection_options=SettingsConstants.POLYSEED_LANGUAGE_NAMES,
                      default_value=SettingsConstants.WORDLIST_LANGUAGE__ENGLISH),

        SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                      attr_name=SettingsConstants.SETTING__PERSISTENT_SETTINGS,
                      abbreviated_name="persistent",
                      display_name="Persistent settings",
                      help_text=SettingsConstants.PERSISTENT_SETTINGS__SD_INSERTED__HELP_TEXT,
                      default_value=SettingsConstants.OPTION__DISABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                      attr_name=SettingsConstants.SETTING__XMR_DENOMINATION,
                      display_name="Denomination display",
                      abbreviated_name="denom",
                      type=SettingsConstants.TYPE__SELECT_1,
                      selection_options=SettingsConstants.ALL_XMR_DENOMINATIONS,
                      default_value=SettingsConstants.XMR_DENOMINATION__THRESHOLD),

        # Advanced options
        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__VIEW_WALLET_QR_FORMAT,
                      display_name="Wallet QR Format",
                      abbreviated_name="wqrfmt",
                      type=SettingsConstants.TYPE__MULTISELECT,
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      selection_options=SettingsConstants.ALL_VIEW_ONLY_WALLET_FORMATS,
                      default_value=SettingsConstants.ALL_VIEW_ONLY_WALLET_FORMATS[:1]),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__NETWORKS,
                      display_name="Monero networks",
                      type=SettingsConstants.TYPE__MULTISELECT,
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      selection_options=SettingsConstants.ALL_NETWORKS,
                      default_value=SettingsConstants.ALL_NETWORKS[:1]),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__QR_DENSITY,
                      display_name="QR code density",
                      type=SettingsConstants.TYPE__SELECT_1,
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      selection_options=SettingsConstants.ALL_DENSITIES,
                      default_value=SettingsConstants.DENSITY__MEDIUM),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__MONERO_SEED_PASSPHRASE,
                      display_name="Monero seed passphrase",
                      type=SettingsConstants.TYPE__SELECT_1,
                      visibility=SettingsConstants.VISIBILITY__HIDDEN,  # is hidden because this feature is posponed because of insane password derivation method in monero (CryptoNight, need to transpile to python, very propably other #rabbit-hole, be aware before starting!)
                      selection_options=SettingsConstants.OPTIONS__ENABLED_DISABLED_REQUIRED,
                      default_value=SettingsConstants.OPTION__DISABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__POLYSEED_PASSPHRASE,
                      display_name="Polyseed passphrase",
                      type=SettingsConstants.TYPE__SELECT_1,
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      selection_options=SettingsConstants.OPTIONS__ENABLED_DISABLED_REQUIRED,
                      default_value=SettingsConstants.OPTION__ENABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__CAMERA_ROTATION,
                      abbreviated_name="camera",
                      display_name="Camera rotation",
                      type=SettingsConstants.TYPE__SELECT_1,
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      selection_options=SettingsConstants.ALL_CAMERA_ROTATIONS,
                      default_value=SettingsConstants.CAMERA_ROTATION__180),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__COMPACT_SEEDQR,
                      display_name="CompactSeedQR",
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      default_value=SettingsConstants.OPTION__DISABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__MESSAGE_SIGNING,
                      display_name="Message signing",
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      default_value=SettingsConstants.OPTION__DISABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__PRIVACY_WARNINGS,
                      abbreviated_name="priv_warn",
                      display_name="Show privacy warnings",
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      default_value=SettingsConstants.OPTION__ENABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__LOW_SECURITY ,
                      abbreviated_name="low_sec",
                      display_name="Low security",
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      default_value=SettingsConstants.OPTION__DISABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__DIRE_WARNINGS,
                      abbreviated_name="dire_warn",
                      display_name="Show dire warnings",
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      default_value=SettingsConstants.OPTION__ENABLED),
 
        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__QR_BRIGHTNESS_TIPS,
                      display_name="Show QR brightness tips",
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      default_value=SettingsConstants.OPTION__ENABLED),

        SettingsEntry(category=SettingsConstants.CATEGORY__FEATURES,
                      attr_name=SettingsConstants.SETTING__PARTNER_LOGOS,
                      abbreviated_name="partners",
                      display_name="Show partner logos",
                      visibility=SettingsConstants.VISIBILITY__ADVANCED,
                      default_value=SettingsConstants.OPTION__DISABLED),
        
        # "Hidden" settings with no UI interaction
        SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                      attr_name=SettingsConstants.SETTING__QR_BRIGHTNESS,
                      abbreviated_name="qr_brightness",
                      display_name="QR background color",
                      type=SettingsConstants.TYPE__FREE_ENTRY,
                      visibility=SettingsConstants.VISIBILITY__HIDDEN,
                      default_value=62),
    ]


    @classmethod
    def get_settings_entries(cls, visibility: str = SettingsConstants.VISIBILITY__GENERAL) -> List[SettingsEntry]:
        entries = []
        for entry in cls.settings_entries:
            if entry.visibility == visibility:
                entries.append(entry)
        return entries


    @classmethod
    def get_settings_entry_by_abbreviated_name(cls, abbreviated_name: str) -> SettingsEntry:
        for entry in cls.settings_entries:
            if abbreviated_name in [entry.abbreviated_name, entry.attr_name]:
                return entry


    @classmethod
    def get_settings_entry(cls, attr_name) -> SettingsEntry:
        for entry in cls.settings_entries:
            if entry.attr_name == attr_name:
                return entry


    @classmethod
    def get_defaults(cls) -> dict:
        as_dict = {}
        for entry in SettingsDefinition.settings_entries:
            if type(entry.default_value) == list:
                # Must copy the default_value list, otherwise we'll inadvertently change
                # defaults when updating these attrs
                as_dict[entry.attr_name] = list(entry.default_value)
            else:
                as_dict[entry.attr_name] = entry.default_value
        return as_dict


    @classmethod
    def to_dict(cls) -> dict:
        output = {
            "settings_entries": [],
        }
        for settings_entry in cls.settings_entries:
            output["settings_entries"].append(settings_entry.to_dict())
        
        return output



if __name__ == "__main__":
    from json import dump
    from os import uname

    hostname = uname()[1]
    if hostname == "xmrsigner-os":
        output_file = "/mnt/microsd/settings_definition.json"
    else:
        output_file = "settings_definition.json"
    with open(output_file, 'w') as json_file:
        dump(SettingsDefinition.to_dict(), json_file, indent=4)
