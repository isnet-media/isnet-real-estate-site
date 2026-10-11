#!/usr/bin/env python3
"""Protect published schedules against city leakage, outages and failed metadata."""
import copy
import json
import unittest
from unittest.mock import patch
import refresh_ashdod_cinema as intake


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.original = {'movies': [{'id': 'film', 'title': 'סרט לדוגמה', 'synopsis': 'תקציר מאומת איכותי',
            'runtime_minutes': 100, 'trailer_youtube_id': 'abcdefghijk', 'is_family': False,
            'venues': [{'id': 'cinema-city', 'name': 'סינמה סיטי אשדוד',
                'schedule': {intake.TODAY: ['18:00']}, 'schedule_verified_at': 'previous'},
                {'id': 'hot-cinema', 'name': 'HOT Cinema אשדוד',
                'schedule': {intake.TODAY: ['20:00']}, 'schedule_verified_at': 'previous'}]}]}

    def row(self):
        return {'title': 'סרט לדוגמה', 'source_id': '1', 'source_url': 'https://www.cinema-city.co.il/movie/1',
            'schedule': {intake.TODAY: {'19:00'}}, 'sessions': [], 'synopsis': '', 'genres': []}

    def test_partial_outage_preserves_other_venue_and_richer_metadata(self):
        updated, _ = intake.merge(self.original, {'cinema-city': {'status': 'ok', 'movies': [self.row()]},
                                                'hot-cinema': {'status': 'failed'}})
        film = updated['movies'][0]
        self.assertEqual(film['synopsis'], 'תקציר מאומת איכותי')
        self.assertEqual(film['runtime_minutes'], 100)
        self.assertEqual(film['trailer_youtube_id'], 'abcdefghijk')
        self.assertEqual(film['venues'][0]['schedule'][intake.TODAY], ['19:00'])
        self.assertEqual(film['venues'][1]['schedule'][intake.TODAY], ['20:00'])

    def test_successful_snapshot_archives_absent_films_without_deleting_metadata(self):
        row = self.row(); row.update(title='סרט חדש', source_id='2')
        updated, _ = intake.merge(self.original, {'cinema-city': {'status': 'ok', 'movies': [row]}})
        self.assertEqual(updated['movies'][0]['venues'][0]['schedule'], {})
        self.assertEqual(updated['movies'][0]['synopsis'], 'תקציר מאומת איכותי')
        self.assertEqual(len(updated['movies']), 2)

    def test_language_merge_preserves_failed_source_schedules_and_deep_links(self):
        other = copy.deepcopy(self.original['movies'][0])
        other.update(id='film-russian', title='סרט לדוגמה מדובב לרוסית')
        other['venues'][0]['schedule'] = {intake.TODAY: ['21:00']}
        self.original['movies'].append(other)
        updated, _ = intake.merge(self.original, {'cinema-city': {'status': 'failed'}})
        self.assertEqual(len(updated['movies']), 1)
        self.assertIn('film-russian', updated['movies'][0]['aliases'])
        self.assertEqual(updated['movies'][0]['venues'][0]['schedule'][intake.TODAY], ['18:00', '21:00'])

    def test_non_ashdod_session_is_rejected(self):
        session = {'featureId': 1, 'featureName': 'סרט', 'locationName': 'סינמה סיטי אשדוד',
                   'payloadJson': json.dumps({'venueLocationId': 999}), 'dateTime': intake.TODAY + ' 18:00'}
        with patch.object(intake, 'request', return_value=json.dumps({'apps': {
                '675bbcef-18d8-41f5-800e-131ec9e08762': {'instance': 'public-visitor'}}})), \
             patch.object(intake, 'city_query', side_effect=[[
                {'hebrewName': 'סינמה סיטי אשדוד', 'locationId': 1181}], [session], []]):
            with self.assertRaisesRegex(ValueError, 'Non-Ashdod'):
                intake.collect_city()

    def test_verified_official_poster_is_published_with_provenance(self):
        row = self.row()
        row['poster_verified'] = {'url': 'https://hotcinema.co.il/images/film.jpg',
            'source_url': row['source_url'], 'verified_at': intake.STAMP}
        updated, report = intake.merge(self.original, {'cinema-city': {'status': 'ok', 'movies': [row]}})
        self.assertEqual(updated['movies'][0]['poster_url'], row['poster_verified']['url'])
        self.assertEqual(report['counts']['official_poster'], 1)

    def test_failed_poster_refresh_keeps_verified_image(self):
        self.original['movies'][0]['poster_url'] = 'https://hotcinema.co.il/images/film.jpg'
        row = self.row(); row['poster_error'] = 'Network timeout'
        updated, _ = intake.merge(self.original, {'cinema-city': {'status': 'ok', 'movies': [row]}})
        self.assertEqual(updated['movies'][0]['poster_url'], self.original['movies'][0]['poster_url'])

    def test_poster_candidate_does_not_become_published_image(self):
        row = self.row(); row['poster_source_url'] = 'https://example.com/poster.jpg'
        updated, report = intake.merge(self.original, {'cinema-city': {'status': 'ok', 'movies': [row]}})
        self.assertNotIn('poster_url', updated['movies'][0])
        self.assertEqual(report['counts']['official_poster'], 0)


if __name__ == '__main__':
    unittest.main()
