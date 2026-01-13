#!/usr/bin/env python3
"""Update ZeroBus OAuth credentials securely via command line.

Usage:
    python update_credentials.py <protocol> <client_id> <client_secret>

Example:
    python update_credentials.py opcua your-client-id your-client-secret

Protocols: opcua, mqtt, modbus
"""

import sys
import json
from pathlib import Path
from ot_simulator.credential_manager import CredentialManager


def main():
    if len(sys.argv) < 4:
        print("Usage: python update_credentials.py <protocol> <client_id> <client_secret>")
        print("\nProtocols: opcua, mqtt, modbus")
        print("\nExample:")
        print("  python update_credentials.py opcua your-client-id your-client-secret")
        sys.exit(1)

    protocol = sys.argv[1].lower()
    client_id = sys.argv[2]
    client_secret = sys.argv[3]

    if protocol not in ["opcua", "mqtt", "modbus"]:
        print(f"Error: Unknown protocol '{protocol}'. Must be one of: opcua, mqtt, modbus")
        sys.exit(1)

    # Initialize credential manager
    config_dir = Path("ot_simulator") / "zerobus_configs"
    cred_manager = CredentialManager(config_dir)

    # Load existing config
    config_file = config_dir / f"{protocol}_zerobus.json"
    if not config_file.exists():
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)

    with open(config_file, "r") as f:
        config = json.load(f)

    # Update credentials
    if "auth" not in config:
        config["auth"] = {}

    config["auth"]["client_id"] = client_id
    config["auth"]["client_secret"] = client_secret

    # Save with encryption
    saved_path = cred_manager.save_config(protocol, config)

    print(f"✅ Successfully updated OAuth credentials for {protocol.upper()}")
    print(f"   Config saved to: {saved_path}")
    print(f"   Client ID: {client_id}")
    print(f"   Client Secret: {'*' * len(client_secret)} (encrypted)")
    print("\nNext steps:")
    print(f"  1. Test connection via Web UI: http://localhost:8989")
    print(f"  2. Or test via CLI: curl -X POST http://localhost:8989/api/zerobus/load?protocol={protocol}")


if __name__ == "__main__":
    main()
