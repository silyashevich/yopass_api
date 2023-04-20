from yopass_api import Yopass

yopass = Yopass(api="https://api.yopass.se")
secret_password = yopass.generate_passphrase(length=5)
secret_id = yopass.store(
    message="test",
    password=secret_password,
    expiration="1w",
    one_time=False,
)
secret_url = yopass.secret_url(secret_id=secret_id, password=secret_password)
print(secret_url)
message = yopass.fetch(secret_id=secret_id, password=secret_password)
print(message)
