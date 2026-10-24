from app.extensions import db
from app.models import User


def test_signup(client,monkeypatch):
    sent=[]
    monkeypatch.setattr("app.services.otp.send_code",lambda email,code:sent.append(code))
    response=client.post("/api/auth/signup",json={"email":"New@Example.test","password":"long enough password"})
    assert response.status_code == 202
    user=db.session.scalar(db.select(User).where(User.email=="new@example.test"))
    assert user.password.startswith("scrypt:")
    assert user.is_verified == 0
    assert len(sent)==1
    assert client.post("/api/auth/login",json={"email":user.email,"password":"long enough password"}).status_code == 401


def test_duplicate_does_not_replace_password(client,account,monkeypatch):
    monkeypatch.setattr("app.services.otp.send_code",lambda *args:None)
    stored=account.password
    result=client.post("/api/auth/signup",json={"email":account.email,"password":"different secure password"})
    assert result.status_code==202
    assert account.password==stored
    assert "eligible" in result.json["message"]
