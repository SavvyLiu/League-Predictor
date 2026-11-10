"""Offline checks: no Riot calls or real credentials are used."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("riot_collect", Path(__file__).resolve().parents[1] / "collect.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CollectionChecks(unittest.TestCase):
    def test_rejects_old_patch_and_wrong_platform(self):
        manifest = {"platform": "na1", "patch": "16.22", "window_start": 100, "window_end": 200}
        match = {"metadata": {"matchId": "NA1_TEST"}, "info": {"queueId": 420, "mapId": 11,
                 "gameVersion": "16.22.1", "gameStartTimestamp": 150000, "gameDuration": 1200,
                 "participants": [{"teamId": 100}] * 5 + [{"teamId": 200}] * 5,
                 "teams": [{"teamId": 100, "win": True}, {"teamId": 200, "win": False}]}}
        self.assertIsNone(collector.eligibility(match, manifest))
        match["info"]["gameVersion"] = "10.1.1"
        self.assertEqual(collector.eligibility(match, manifest), "different_patch")
        match["metadata"]["matchId"] = "EUW1_TEST"
        self.assertEqual(collector.eligibility(match, manifest), "different_platform")

    def test_short_games_and_incomplete_teams_rejected(self):
        manifest = {"platform": "na1", "patch": "16.22", "window_start": 100, "window_end": 200}
        match = {"metadata": {"matchId": "NA1_TEST"}, "info": {"queueId": 420, "mapId": 11,
                 "gameVersion": "16.22.1", "gameStartTimestamp": 150000, "gameDuration": 600}}
        self.assertEqual(collector.eligibility(match, manifest), "ended_before_ten_minutes")
        match["info"]["gameDuration"] = 1200
        self.assertEqual(collector.eligibility(match, manifest), "incomplete_teams")

    def test_cached_responses_need_no_key_or_network(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cached.json"
            collector.atomic_json(path, {"cached": True})
            client = collector.Client(1)
            client.session = Mock()
            with patch.object(collector, "read_key", side_effect=AssertionError("Key should not be read")):
                self.assertEqual(client.get("na1", "/not-called", path), {"cached": True})
            client.session.get.assert_not_called()
            self.assertEqual(client.cache_hits, 1)

    def test_key_is_reloaded_for_each_new_request(self):
        with tempfile.TemporaryDirectory() as folder:
            client = collector.Client(2)
            response = SimpleNamespace(status_code=200, headers={}, json=lambda: {"ok": True})
            client.session = Mock(get=Mock(return_value=response))
            with patch.object(collector, "read_key", side_effect=["RGAPI-FAKE-ONE", "RGAPI-FAKE-TWO"]), patch.object(collector.time, "sleep"):
                client.get("na1", "/one", Path(folder) / "one.json")
                client.get("na1", "/two", Path(folder) / "two.json")
            headers = [call.kwargs["headers"]["X-Riot-Token"] for call in client.session.get.call_args_list]
            self.assertEqual(headers, ["RGAPI-FAKE-ONE", "RGAPI-FAKE-TWO"])

    def test_auth_rejection_stops_without_retrying(self):
        with tempfile.TemporaryDirectory() as folder:
            client = collector.Client(5)
            client.session = Mock(get=Mock(return_value=SimpleNamespace(status_code=403, headers={})))
            with patch.object(collector, "read_key", return_value="RGAPI-FAKE"), patch.object(collector.time, "sleep"):
                with self.assertRaises(collector.KeyRefreshNeeded):
                    client.get("na1", "/fake", Path(folder) / "cached.json")
            self.assertEqual(client.network_requests, 1)
            self.assertFalse((Path(folder) / "cached.json").exists())

    def test_request_budget_preserves_cache_and_stops_network(self):
        client = collector.Client(0)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(collector.RequestBudgetReached):
                client.get("na1", "/fake", Path(folder) / "cached.json")
        self.assertEqual(client.network_requests, 0)

    def test_rate_limit_obeys_retry_after(self):
        with tempfile.TemporaryDirectory() as folder:
            client = collector.Client(2)
            client.session = Mock(get=Mock(side_effect=[
                SimpleNamespace(status_code=429, headers={"Retry-After": "7"}),
                SimpleNamespace(status_code=200, headers={"X-App-Rate-Limit": "100:120"}, json=lambda: {"ok": True})]))
            with patch.object(collector, "read_key", return_value="RGAPI-FAKE"), patch.object(collector.time, "sleep") as sleep:
                self.assertEqual(client.get("na1", "/fake", Path(folder) / "cached.json"), {"ok": True})
            self.assertIn(7.0, [c.args[0] for c in sleep.call_args_list])
            self.assertEqual(client.statuses, {"429": 1, "200": 1})


if __name__ == "__main__":
    unittest.main()
