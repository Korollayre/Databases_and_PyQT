import unittest

from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, PORT
from client import user_request, server_response


class TestClient(unittest.TestCase):

    def test_presense(self):
        test_data = user_request(8888)
        self.assertEqual(test_data, {ACTION: PRESENCE, TIME: test_data[TIME], PORT: 8888, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_incorrect_presense(self):
        test_data = user_request(8888)
        self.assertNotEqual(test_data, {ACTION: PRESENCE, TIME: test_data[TIME], PORT: 8888})

    def test_server_response_200(self):
        self.assertEqual(server_response({RESPONSE: 200}), '200 : OK')

    def test_server_incorrect_response_200(self):
        self.assertNotEqual(server_response({RESPONSE: 200}), '200 : Not')

    def test_server_response_400(self):
        self.assertEqual(server_response({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_server_incorrect_response_400(self):
        self.assertNotEqual(server_response({RESPONSE: 400, ERROR: 'Bad Request'}), '401: Unauthorized')

    def test_no_response(self):
        self.assertRaises(ValueError, server_response, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
