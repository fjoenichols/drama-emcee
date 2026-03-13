"""
Refresh Static Data Task

Populates the wow_classes and wow_races lookup tables from the Blizzard
game data API. These tables map the numeric IDs stored on character records
to human-readable names and faction info.

Static data (classes, races) changes only with major game patches, so this
task does not need to run nightly. Run it once at initial setup and again
whenever a new patch adds playable races or classes.

Usage (CLI):
    python -m tasks.refresh_static_data
"""

from services import blizzard, database

REGION = "us"
LOCALE = "en_US"


def _sync_classes() -> int:
    """Fetch and store all playable classes. Returns the count upserted."""
    data = blizzard.get_playable_classes_index(REGION, LOCALE)
    classes = data.get("classes", [])
    for entry in classes:
        database.upsert_class(class_id=entry["id"], name=entry["name"])
    return len(classes)


def _sync_races() -> int:
    """Fetch and store all playable races. Returns the count upserted."""
    data = blizzard.get_playable_races_index(REGION, LOCALE)
    races = data.get("races", [])
    for entry in races:
        faction_data = entry.get("faction", {})
        faction = faction_data.get("name") if isinstance(faction_data, dict) else None
        database.upsert_race(race_id=entry["id"], name=entry["name"], faction=faction)
    return len(races)


def run() -> None:
    """Sync playable classes and races from the Blizzard API to the database."""
    print("Syncing playable classes...")
    class_count = _sync_classes()
    print(f"  {class_count} classes stored.")

    print("Syncing playable races...")
    race_count = _sync_races()
    print(f"  {race_count} races stored.")

    print("\nDone. Current lookup tables:")

    classes = database.get_all_classes()
    print(f"\n  Classes ({len(classes)}):")
    for c in classes:
        print(f"    {c['id']:>3}  {c['name']}")

    races = database.get_all_races()
    print(f"\n  Races ({len(races)}):")
    for r in races:
        faction = f"  [{r['faction']}]" if r["faction"] else ""
        print(f"    {r['id']:>3}  {r['name']}{faction}")


if __name__ == "__main__":
    run()
