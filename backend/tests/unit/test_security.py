import pytest
from datetime import datetime, timedelta, timezone
import jwt
import os

from security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

@pytest.fixture(scope="module")
def common_data():
    user_id = 900
    password = 'some_password'
    
    password_hashed = hash_password(password)
    another_password_hashed = hash_password('another_password')
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    return {
        'user_id': user_id,
        'password': password,
        'password_hashed': password_hashed,
        'another_password_hashed': another_password_hashed,
        'access_token': access_token,
        'refresh_token': refresh_token,
    }


class TestSecurity:
    def test_hash_is_a_string(self, common_data):
        assert isinstance(common_data['password_hashed'], str)

    def test_hash_difference(self, common_data):
        assert common_data['password_hashed'] != common_data['another_password_hashed']

    def test_hash_actually_hashed(self, common_data):
        assert common_data['password_hashed'] != common_data['password']

    def test_verify_password(self, common_data):
        assert verify_password(common_data['password'], common_data['password_hashed'])

    def test_verify_wrong_password(self, common_data):
        assert not verify_password(common_data['password'], common_data['another_password_hashed'])

    def test_creating_access_token(self, common_data):
        assert isinstance(common_data['access_token'], str)

    def test_create_refresh_token(self, common_data):
        assert isinstance(common_data['refresh_token'], str)

    def test_decode_token_id(self, common_data):
        decoded_id = decode_token(common_data['access_token']).get('sub')
        assert decoded_id == str(common_data['user_id'])

    def create_test_token(self, payload: dict, expires_delta: timedelta):
        expire = datetime.now(timezone.utc) + expires_delta
        payload.update({"exp": expire.timestamp(), "type": "access"}) # "iat": datetime.now(timezone.utc).timestamp(),
        
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def test_decode_token_expired(self):
        test_payload = {"sub": "123"}
        expired_token = self.create_test_token(test_payload, timedelta(minutes=-1))
        with pytest.raises(jwt.exceptions.ExpiredSignatureError):
            decode_token(expired_token)

    def test_decode_token_invalid_signature(self):
        test_payload = {"sub": "123"}
        valid_token = self.create_test_token(test_payload, timedelta(minutes=1))
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            jwt.decode(valid_token, "WRONG_SECRET", algorithms=[ALGORITHM])

    def test_decode_token_invalid_format(self):
        invalid_token = "invalid.format"
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            decode_token(invalid_token)
