import unittest

from playlist_logic import (
    build_playlists,
    compute_playlist_stats,
    lucky_pick,
    merge_playlists,
    search_songs,
)

class PlaylistLogicTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "hype_min_energy": 7,
            "chill_max_energy": 3,
            "favorite_genre": "rock",
        }

    def test_search_is_case_insensitive_partial_match(self):
        songs = [{"artist": "AC/DC"}, {"artist": "Queen"}]
        self.assertEqual(search_songs(songs, "AC", "artist"), [songs[0]])
        self.assertEqual(search_songs(songs, "c/d", "artist"), [songs[0]])

    def test_search_blank_query_returns_every_song(self):
        songs = [{"artist": "AC/DC"}, {"artist": "Queen"}]
        self.assertEqual(search_songs(songs, "  ", "artist"), songs)

    def test_classification_normalizes_favorite_genre(self):
        songs = [{"title": "middle", "artist": "X", "genre": " ROCK ", "energy": 5}]
        playlists = build_playlists(songs, {**self.profile, "favorite_genre": " Rock "})
        self.assertEqual(len(playlists["Hype"]), 1)

    def test_stats_use_all_unique_songs(self):
        hype = {"title": "Loud", "artist": "A", "energy": 8}
        chill = {"title": "Quiet", "artist": "B", "energy": 2}
        mixed = {"title": "Mid", "artist": "C", "energy": 5}
        playlists = {"Hype": [hype], "Chill": [chill], "Mixed": [mixed, hype]}
        stats = compute_playlist_stats(playlists)
        self.assertEqual(stats["total_songs"], 3)
        self.assertAlmostEqual(stats["avg_energy"], 5.0)
        self.assertAlmostEqual(stats["hype_ratio"], 1 / 3)

    def test_lucky_pick_respects_mode_and_any_includes_mixed(self):
        hype = {"title": "H", "mood": "Hype"}
        chill = {"title": "C", "mood": "Chill"}
        mixed = {"title": "M", "mood": "Mixed"}
        playlists = {"Hype": [hype], "Chill": [chill], "Mixed": [mixed]}
        self.assertIs(lucky_pick(playlists, "hype"), hype)
        self.assertIs(lucky_pick(playlists, "chill"), chill)
        self.assertIn(lucky_pick(playlists), [hype, chill, mixed])

    def test_lucky_pick_empty_pool_returns_none(self):
        self.assertIsNone(lucky_pick({"Hype": [], "Chill": [], "Mixed": []}, "hype"))

    def test_merge_does_not_mutate_inputs(self):
        original = {"Hype": [{"title": "A"}]}
        extra = {"Hype": [{"title": "B"}]}
        merged = merge_playlists(original, extra)
        self.assertEqual(len(merged["Hype"]), 2)
        self.assertEqual(len(original["Hype"]), 1)

if __name__ == "__main__":
    unittest.main()
