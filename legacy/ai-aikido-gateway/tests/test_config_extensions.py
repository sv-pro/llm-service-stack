from core.config import CostAlertSettings, CostThresholds, load_cost_alert_config, load_tenant_registry


def test_load_tenant_registry_empty_when_missing(tmp_path):
    registry = load_tenant_registry(path=tmp_path / "missing.yml")
    assert registry.is_empty()


def test_load_tenant_registry_parses_entries(tmp_path):
    config_path = tmp_path / "tenants.yml"
    config_path.write_text(
        """
tenants:
  - tenant_id: alpha
    display_name: Alpha
    api_keys:
      - key_id: alpha-default
        secret: secret-alpha
        status: active
  - tenant_id: beta
    display_name: Beta
    api_keys:
      - key_id: beta-default
        secret: secret-beta
        status: disabled
""",
        encoding="utf-8",
    )

    registry = load_tenant_registry(path=config_path)
    assert not registry.is_empty()
    assert registry.get("alpha").display_name == "Alpha"
    tenant, api_key = registry.find_api_key("secret-alpha")
    assert tenant.tenant_id == "alpha"
    assert api_key.key_id == "alpha-default"
    # Disabled keys should not match
    assert registry.find_api_key("secret-beta") is None


def test_load_cost_alert_config_defaults_when_missing(tmp_path):
    settings = load_cost_alert_config(path=tmp_path / "billing.yml")
    assert isinstance(settings, CostAlertSettings)
    assert settings.default == CostThresholds()


def test_load_cost_alert_config_parses_overrides(tmp_path):
    config_path = tmp_path / "billing.yml"
    config_path.write_text(
        """
default:
  daily: 100.0
  monthly: 1000.0
tenants:
  alpha:
    daily: 200.0
    weekly: 700.0
""",
        encoding="utf-8",
    )

    settings = load_cost_alert_config(path=config_path)
    assert settings.default.daily == 100.0
    assert settings.default.monthly == 1000.0
    alpha_thresholds = settings.get_thresholds_for("alpha")
    assert alpha_thresholds.daily == 200.0
    assert alpha_thresholds.weekly == 700.0
