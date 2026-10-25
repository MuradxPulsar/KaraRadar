"""Minimal i18n dictionary for UI strings."""
STRINGS = {
    "az": {
        "menu_title": "KaraRadar — Interactive Menu",
        "opt1": "Brand monitoring (CT discovery mode)",
        "opt2": "Analyze my own domains (domain1,domain2 or .txt)",
        "opt3": "Manage brands (add / remove / list)",
        "opt4": "Settings (language AZ/EN, report format)",
        "opt5": "Watch mode (live CT stream)",
        "opt6": "History & reports (browse past scans)",
        "opt7": "Whitelist management",
        "opt8": "Exit",
        "no_banner_flag": "--no-banner: banner disabled",
    },
    "en": {
        "menu_title": "KaraRadar — Interactive Menu",
        "opt1": "Brand monitoring (CT discovery mode)",
        "opt2": "Analyze my own domains (domain1,domain2 or .txt)",
        "opt3": "Manage brands (add / remove / list)",
        "opt4": "Settings (language AZ/EN, report format)",
        "opt5": "Watch mode (live CT stream)",
        "opt6": "History & reports (browse past scans)",
        "opt7": "Whitelist management",
        "opt8": "Exit",
    },
}


def t(lang, key):
    return STRINGS.get(lang, STRINGS["az"]).get(key, key)
