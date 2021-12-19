import unittest

from client import user_request
from common.variables import (ACCOUNT_NAME, ACTION, ERROR, PORT, PRESENCE,
                              RESPONDEFAULT_IP_ADDRESSSE, RESPONSE, TIME, USER)
from server import process_user_message


class TestClient(unittest.TestCase):
    error_response = {
        RESPONDEFAULT_IP_ADDRESSSE: 400,
        ERROR: 'Bad Request'
    }

    correct_response = {RESPONSE: 200}

    # Equal - Корректный запрос
    def test_presense(self):
        self.assertEqual(process_user_message(user_request(8888)), self.correct_response)

    # NoEqual - некорректный запрос, так как отсутствует порт
    def test_incorrect_presense(self):
        self.assertNotEqual(process_user_message({ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}),
                            self.correct_response)

    # Equal - Корректный запрос, так как отсутствует порт
    def test_correct_incorrect_presense(self):
        self.assertEqual(process_user_message({ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}),
                         self.error_response)


if __name__ == '__main__':
    unittest.main()
