from typing import Dict, List, Optional, Tuple

Song = Dict[str, object]
PlaylistMap = Dict[str, List[Song]]

DEFAULT_PROFILE = {
    "name": "Default",
    "hype_min_energy": 7,
    "chill_max_energy": 3,
    "favorite_genre": "rock",
    "include_mixed": True,
}


def normalize_title(title: str) -> str:
    """Normalize a song title for comparisons."""
    if not isinstance(title, str):
        return ""
    return title.strip()


def normalize_artist(artist: str) -> str:
    """Normalize an artist name for comparisons."""
    if not artist:
        return ""
    return artist.strip().lower()


def normalize_genre(genre: str) -> str:
    """Normalize a genre name for comparisons."""
    return genre.lower().strip()


def normalize_song(raw: Song) -> Song:
    """Return a normalized song dict with expected keys."""
    title = normalize_title(str(raw.get("title", "")))
    artist = normalize_artist(str(raw.get("artist", "")))
    genre = normalize_genre(str(raw.get("genre", "")))
    energy = raw.get("energy", 0)

    if isinstance(energy, str):
        try:
            energy = int(energy)
        except ValueError:
            energy = 0

    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return {
        "title": title,
        "artist": artist,
        "genre": genre,
        "energy": energy,
        "tags": tags,
    }


def classify_song(song: Song, profile: Dict[str, object]) -> str:
    """Return a mood label given a song and user profile."""
    energy = song.get("energy", 0)
    genre = str(song.get("genre", "")).strip().lower()
    title = str(song.get("title", "")).strip().lower()

    hype_min_energy = int(profile.get("hype_min_energy", 7))
    chill_max_energy = int(profile.get("chill_max_energy", 3))
    favorite_genre = str(profile.get("favorite_genre", "")).strip().lower()

    hype_keywords = ["rock", "punk", "party"]
    chill_keywords = ["lofi", "ambient", "sleep"]

    is_hype_keyword = any(k in genre for k in hype_keywords)
    is_chill_keyword = any(k in title for k in chill_keywords)

    # Compare normalized profile and song text so casing/spacing cannot change the mood.
    if genre == favorite_genre or energy >= hype_min_energy or is_hype_keyword:
        return "Hype"
    if energy <= chill_max_energy or is_chill_keyword:
        return "Chill"
    return "Mixed"


def build_playlists(songs: List[Song], profile: Dict[str, object]) -> PlaylistMap:
    """Group songs into playlists based on mood and profile."""
    playlists: PlaylistMap = {
        "Hype": [],
        "Chill": [],
        "Mixed": [],
    }

    for song in songs:
        normalized = normalize_song(song)
        mood = classify_song(normalized, profile)
        normalized["mood"] = mood
        playlists[mood].append(normalized)

    return playlists


def merge_playlists(a: PlaylistMap, b: PlaylistMap) -> PlaylistMap:
    """Merge two playlist maps into a new map."""
    merged: PlaylistMap = {}
    for key in set(a) | set(b):
        merged[key] = list(a.get(key, [])) + list(b.get(key, []))
    return merged


def _song_key(song: Song) -> Tuple[str, str]:
    """Return a normalized identity key for deduplicating playlist entries."""
    return (
        str(song.get("title", "")).strip().lower(),
        str(song.get("artist", "")).strip().lower(),
    )


def compute_playlist_stats(playlists: PlaylistMap) -> Dict[str, object]:
    """Compute statistics across unique songs in all playlists."""
    # Count each title/artist pair once even if it appears in multiple playlists.
    unique_songs: Dict[Tuple[str, str], Song] = {}
    for songs in playlists.values():
        for song in songs:
            unique_songs.setdefault(_song_key(song), song)

    all_songs = list(unique_songs.values())
    hype = { _song_key(song) for song in playlists.get("Hype", []) }
    chill = playlists.get("Chill", [])
    mixed = playlists.get("Mixed", [])

    total = len(all_songs)
    hype_ratio = len(hype) / total if total > 0 else 0.0
    avg_energy = (
        sum(float(song.get("energy", 0)) for song in all_songs) / total
        if total else 0.0
    )

    top_artist, top_count = most_common_artist(all_songs)

    return {
        "total_songs": len(all_songs),
        "hype_count": len(hype),
        "chill_count": len(chill),
        "mixed_count": len(mixed),
        "hype_ratio": hype_ratio,
        "avg_energy": avg_energy,
        "top_artist": top_artist,
        "top_artist_count": top_count,
    }


def most_common_artist(songs: List[Song]) -> Tuple[str, int]:
    """Return the most common artist and count."""
    counts: Dict[str, int] = {}
    for song in songs:
        artist = str(song.get("artist", ""))
        if not artist:
            continue
        counts[artist] = counts.get(artist, 0) + 1

    if not counts:
        return "", 0

    items = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return items[0]


def search_songs(
    songs: List[Song],
    query: str,
    field: str = "artist",
) -> List[Song]:
    """Return songs matching the query on a given field."""
    q = query.strip().lower()
    if not q:
        return songs

    filtered: List[Song] = []

    for song in songs:
        value = str(song.get(field, "")).lower()
        # Match the query inside the selected field to support partial searches.
        if q in value:
            filtered.append(song)

    return filtered


def lucky_pick(
    playlists: PlaylistMap,
    mode: str = "any",
) -> Optional[Song]:
    """Pick a song from the playlists according to mode."""
    if mode == "hype":
        songs = playlists.get("Hype", [])
    elif mode == "chill":
        songs = playlists.get("Chill", [])
    else:
        # "Any" includes all three categories; explicit modes remain category-specific.
        songs = (
            playlists.get("Hype", [])
            + playlists.get("Chill", [])
            + playlists.get("Mixed", [])
        )

    return random_choice_or_none(songs)


def random_choice_or_none(songs: List[Song]) -> Optional[Song]:
    """Return a random song or None."""
    import random

    # Empty pools are a normal UI state, so return None instead of raising IndexError.
    return random.choice(songs) if songs else None


def history_summary(history: List[Song]) -> Dict[str, int]:
    """Return a summary of moods seen in the history."""
    counts = {"Hype": 0, "Chill": 0, "Mixed": 0}
    for song in history:
        mood = song.get("mood", "Mixed")
        if mood not in counts:
            counts["Mixed"] += 1
        else:
            counts[mood] += 1
    return counts
