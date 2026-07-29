from pathlib import Path

from overhead.config import load_config


def test_load_config_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "does-not-exist.yaml")

    assert config.overhead.radius_nm == 5
    assert config.cache.origin_dest_ttl_s == 86400
    assert config.cache.position_ttl_s == 60


def test_load_config_reads_values_from_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
overhead:
  radius_nm: 10

cache:
  origin_dest_ttl_s: 3600
  position_ttl_s: 30
"""
    )

    config = load_config(config_path)

    assert config.overhead.radius_nm == 10
    assert config.cache.origin_dest_ttl_s == 3600
    assert config.cache.position_ttl_s == 30
