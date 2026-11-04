import supplychain.auth as auth
from supplychain.auth import ALLOW_DEMO_LOGIN, ALLOW_SIGNUP, PUBLIC_DEPLOYMENT, get_auth_config


def test_auth_flags_expose_deployment_settings():
    config = get_auth_config()
    assert isinstance(config["allow_signup"], bool)
    assert isinstance(config["allow_demo_login"], bool)
    assert isinstance(config["public_mode"], bool)
    assert config["allow_signup"] == ALLOW_SIGNUP
    assert config["allow_demo_login"] == ALLOW_DEMO_LOGIN
    assert config["public_mode"] == PUBLIC_DEPLOYMENT


def test_registration_can_be_disabled(monkeypatch):
    monkeypatch.setattr(auth, "ALLOW_SIGNUP", False)
    ok, message = auth.register_user("newuser", "new@example.com", "password123")
    assert not ok
    assert "disabled" in message.lower()


def test_public_mode_disables_local_accounts_and_demo(monkeypatch):
    monkeypatch.setattr(auth, "PUBLIC_DEPLOYMENT", False)
    auth.configure_public_mode(True)
    config = auth.get_auth_config()
    assert config["public_mode"]
    assert not config["allow_signup"]
    assert not config["allow_demo_login"]


def test_oidc_identity_keeps_a_stable_workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(auth, "DB_PATH", tmp_path / "auth.sqlite")
    monkeypatch.setattr(auth, "DATABASE_URL", None)
    auth.init_auth_db()

    first = auth.provision_oidc_user(
        "https://issuer.example", "subject-123", "planner@example.com", "Supply Planner"
    )
    second = auth.provision_oidc_user(
        "https://issuer.example", "subject-123", "planner@example.com", "Supply Planner"
    )

    assert first["id"] == second["id"]
    assert first["username"] == "Supply Planner"
    auth.save_workspace(first["id"], {"view": "network"})
    assert auth.load_workspace(second["id"]) == {"view": "network"}
