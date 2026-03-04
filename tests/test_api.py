import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.index import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health_ok(self) -> None:
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_convert_rejects_invalid_casa(self) -> None:
        response = self.client.get('/api/convert', params={'ars': 1000, 'casa': 'fantasy'})
        self.assertEqual(response.status_code, 422)

    def test_convert_promedio(self) -> None:
        async def fake_fetch_quote(casa: str):
            return {
                'casa': casa,
                'nombre': 'Dólar Test',
                'compra': 1000,
                'venta': 1200,
                'fechaActualizacion': '2026-01-01T00:00:00.000Z',
            }

        with patch('api.index._fetch_quote', new=fake_fetch_quote):
            response = self.client.get('/api/convert', params={'ars': 2400, 'casa': 'oficial', 'lado': 'promedio'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['rate'], 1100)
        self.assertAlmostEqual(data['usd'], 2400 / 1100, places=6)

    def test_rate_translates_upstream_failure(self) -> None:
        async def fake_fetch_quote(casa: str):
            raise HTTPException(status_code=502, detail='No se pudo contactar')

        with patch('api.index._fetch_quote', new=fake_fetch_quote):
            response = self.client.get('/api/rate', params={'casa': 'blue'})

        self.assertEqual(response.status_code, 502)

    def test_convert_fx_for_eur(self) -> None:
        async def fake_fetch_fx_rates(base: str = 'ARS'):
            return {'rates': {'EUR': 0.00095}, 'time_last_update_utc': 'Fri, 01 Jan 2026 00:00:00 +0000'}

        with patch('api.index._fetch_fx_rates', new=fake_fetch_fx_rates):
            response = self.client.get('/api/convert-fx', params={'ars': 100000, 'target': 'EUR'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['target'], 'EUR')
        self.assertAlmostEqual(data['amount'], 95.0, places=6)


    def test_convert_fx_for_mxn(self) -> None:
        async def fake_fetch_fx_rates(base: str = 'ARS'):
            return {'rates': {'MXN': 0.021}, 'time_last_update_utc': 'Fri, 01 Jan 2026 00:00:00 +0000'}

        with patch('api.index._fetch_fx_rates', new=fake_fetch_fx_rates):
            response = self.client.get('/api/convert-fx', params={'ars': 10000, 'target': 'MXN'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['target'], 'MXN')
        self.assertAlmostEqual(data['amount'], 210.0, places=6)

    def test_convert_fx_rejects_unknown_target(self) -> None:
        response = self.client.get('/api/convert-fx', params={'ars': 1000, 'target': 'XYZ'})
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
