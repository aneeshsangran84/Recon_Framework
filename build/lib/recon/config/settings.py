from pathlib import Path
from typing import Optional, Set
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import tomli

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RECON_",
        env_nested_delimiter="__",
        extra="allow",
    )

    # General
    workspace_dir: Path = Path("~/.recon/workspaces").expanduser()
    threads: int = 10
    timeout: int = 30
    user_agent: str = "ReconFramework/0.1"

    # Logging
    log_level: str = "INFO"
    log_format: str = "text"
    log_file_enabled: bool = True
    log_file_dir: Path = Path("~/.recon/logs").expanduser()

    # Plugins
    auto_enable_safe: bool = True
    disabled_plugins: Set[str] = Field(default_factory=set)

    # Reporting
    report_template_dir: Optional[Path] = None
    company_name: str = "Security Assessment Team"

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from default TOML, user config, and env."""
        # 1. Load built-in defaults
        default_toml = Path(__file__).parent / "default.toml"
        defaults = {}
        if default_toml.exists():
            with open(default_toml, "rb") as f:
                defaults = tomli.load(f)

        # 2. Merge user config (~/.config/recon/config.toml)
        user_cfg_path = Path("~/.config/recon/config.toml").expanduser()
        if user_cfg_path.exists():
            with open(user_cfg_path, "rb") as f:
                user_cfg = tomli.load(f)
                # deep merge could be done here for simplicity
                defaults = {**defaults, **user_cfg}

        # 3. Optionally merge a project config (passed as argument)
        if config_path and config_path.exists():
            with open(config_path, "rb") as f:
                project_cfg = tomli.load(f)
                defaults = {**defaults, **project_cfg}

        # 4. Create settings with env overrides
        return cls(**defaults)