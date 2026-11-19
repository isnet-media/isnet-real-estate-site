import os
import re

PREVIEW = os.environ.get("ASTRO_AD_PREVIEW") == "1"
CLIENT = os.environ.get("ASTRO_ADSENSE_CLIENT", "")
SLOTS = {
    "astrology-landing": os.environ.get("ASTRO_ADSENSE_LANDING_SLOT", ""),
    "astrology-forecast": os.environ.get("ASTRO_ADSENSE_FORECAST_SLOT", ""),
}
if CLIENT or any(SLOTS.values()):
    if not re.fullmatch(r"ca-pub-[0-9]+", CLIENT) or any(
        not re.fullmatch(r"[0-9]+", unit) for unit in SLOTS.values()
    ) or len(set(SLOTS.values())) != len(SLOTS):
        raise ValueError("AdSense needs a valid client and two distinct numeric unit IDs")


def ad_head(enabled):
    if not CLIENT or not enabled:
        return ""
    # Set this when the Ashdod Net page template already supplies the loader.
    if os.environ.get("ASTRO_ADSENSE_EXISTING_LOADER") == "1":
        return ""
    return ('<script async src="https://pagead2.googlesyndication.com/pagead/js/'
            f'adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>')


def ad_slot(placement):
    if CLIENT:
        return (
            f'<aside class="astro-ad" data-placement="{placement}" aria-label="פרסומת">'
            f'<ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" '
            f'data-ad-slot="{SLOTS[placement]}" data-ad-format="horizontal"></ins>'
            '<script>(window.adsbygoogle = window.adsbygoogle || []).push({});</script></aside>'
        )
    preview = ' class="astro-ad astro-ad--preview"' if PREVIEW else ' hidden'
    return (f'<aside{preview} data-placement="{placement}" aria-label="מיקום פרסום לדוגמה">'
            + ('<span>מיקום לבאנר Google</span>' if PREVIEW else '') + '</aside>')
