#!/usr/bin/env python3
"""
OPC-UA Certificate Generation Tool for Unified OT Connector.

This script generates OPC-UA client certificates for secure communication
with OPC-UA servers using Sign and SignAndEncrypt security modes.

Usage:
    python scripts/generate_opcua_cert.py --generate
    python scripts/generate_opcua_cert.py --info
    python scripts/generate_opcua_cert.py --trust-server server.crt

NIS2 Compliance: Article 21.2(h) - Encryption (data in transit)
OPC UA Specification: IEC 62541 (Security)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import os


class OPCUACertificateManager:
    """Manages OPC-UA client certificates."""

    def __init__(self, cert_dir: Path = None):
        """
        Initialize certificate manager.

        Args:
            cert_dir: Directory for certificates (default: ~/.unified_connector/opcua_certs)
        """
        self.cert_dir = cert_dir or Path.home() / '.unified_connector' / 'opcua_certs'
        self.client_cert_file = self.cert_dir / 'client_cert.der'
        self.client_key_file = self.cert_dir / 'client_key.pem'
        self.trusted_dir = self.cert_dir / 'trusted'

        # Create directories
        self.cert_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.trusted_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def generate_client_certificate(
        self,
        application_uri: str = "urn:unified-ot-connector:client",
        organization: str = "Unified OT Connector",
        common_name: str = "Unified OT Connector Client",
        validity_days: int = 365,
        key_size: int = 2048
    ) -> tuple[Path, Path]:
        """
        Generate OPC-UA client certificate.

        OPC-UA certificates must follow specific requirements:
        - DER format for certificate (required by many OPC-UA servers)
        - Subject Alternative Name with Application URI
        - X509v3 extensions for OPC-UA usage

        Args:
            application_uri: OPC-UA Application URI (must be unique)
            organization: Organization name
            common_name: Certificate common name
            validity_days: Validity period in days
            key_size: RSA key size (2048 or 4096)

        Returns:
            Tuple of (cert_file, key_file) paths
        """
        print(f"🔐 Generating OPC-UA Client Certificate")
        print("=" * 60)

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        # Build subject
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        # Build certificate
        cert_builder = x509.CertificateBuilder()
        cert_builder = cert_builder.subject_name(subject)
        cert_builder = cert_builder.issuer_name(issuer)
        cert_builder = cert_builder.public_key(private_key.public_key())
        cert_builder = cert_builder.serial_number(x509.random_serial_number())
        cert_builder = cert_builder.not_valid_before(datetime.utcnow())
        cert_builder = cert_builder.not_valid_after(
            datetime.utcnow() + timedelta(days=validity_days)
        )

        # OPC-UA requires Subject Alternative Name with Application URI
        cert_builder = cert_builder.add_extension(
            x509.SubjectAlternativeName([
                x509.UniformResourceIdentifier(application_uri)
            ]),
            critical=False,
        )

        # Basic constraints (self-signed CA)
        cert_builder = cert_builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )

        # Key usage for OPC-UA
        cert_builder = cert_builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=True,
                data_encipherment=True,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )

        # Extended key usage (client authentication for OPC-UA)
        cert_builder = cert_builder.add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        )

        # Sign certificate
        certificate = cert_builder.sign(private_key, hashes.SHA256(), default_backend())

        # Save private key (PEM format)
        with open(self.client_key_file, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        os.chmod(self.client_key_file, 0o600)

        # Save certificate (DER format - required by OPC-UA)
        with open(self.client_cert_file, 'wb') as f:
            f.write(certificate.public_bytes(serialization.Encoding.DER))
        os.chmod(self.client_cert_file, 0o644)

        print(f"✅ Certificate: {self.client_cert_file}")
        print(f"✅ Private Key: {self.client_key_file}")
        print(f"   Application URI: {application_uri}")
        print(f"   Valid for: {validity_days} days")
        print()

        return self.client_cert_file, self.client_key_file

    def trust_server_certificate(self, server_cert_path: Path) -> Path:
        """
        Trust a server certificate by copying to trusted directory.

        Args:
            server_cert_path: Path to server certificate (DER or PEM)

        Returns:
            Path to trusted certificate
        """
        if not server_cert_path.exists():
            raise FileNotFoundError(f"Server certificate not found: {server_cert_path}")

        # Read certificate
        with open(server_cert_path, 'rb') as f:
            cert_data = f.read()

        # Try loading as PEM or DER
        try:
            if b'-----BEGIN CERTIFICATE-----' in cert_data:
                certificate = x509.load_pem_x509_certificate(cert_data, default_backend())
            else:
                certificate = x509.load_der_x509_certificate(cert_data, default_backend())
        except Exception as e:
            raise ValueError(f"Invalid certificate format: {e}")

        # Extract common name for filename
        cn = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        safe_cn = "".join(c if c.isalnum() or c in "-_" else "_" for c in cn)

        # Save to trusted directory (DER format)
        trusted_cert_path = self.trusted_dir / f"{safe_cn}.der"
        with open(trusted_cert_path, 'wb') as f:
            f.write(certificate.public_bytes(serialization.Encoding.DER))
        os.chmod(trusted_cert_path, 0o644)

        print(f"✅ Trusted server certificate: {trusted_cert_path}")
        print(f"   Common Name: {cn}")

        return trusted_cert_path

    def print_certificate_info(self, cert_path: Path = None):
        """Print certificate information."""
        cert_path = cert_path or self.client_cert_file

        if not cert_path.exists():
            print(f"❌ Certificate not found: {cert_path}")
            return

        # Load certificate
        with open(cert_path, 'rb') as f:
            cert_data = f.read()

        try:
            if b'-----BEGIN CERTIFICATE-----' in cert_data:
                certificate = x509.load_pem_x509_certificate(cert_data, default_backend())
            else:
                certificate = x509.load_der_x509_certificate(cert_data, default_backend())
        except Exception as e:
            print(f"❌ Failed to load certificate: {e}")
            return

        # Extract information
        subject = certificate.subject
        cn = subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        org = subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value if subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME) else "N/A"

        not_valid_before = certificate.not_valid_before
        not_valid_after = certificate.not_valid_after
        days_until_expiry = (not_valid_after - datetime.utcnow()).days

        # Extract Application URI from SAN
        app_uri = "N/A"
        try:
            san_ext = certificate.extensions.get_extension_for_oid(
                ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )
            for name in san_ext.value:
                if isinstance(name, x509.UniformResourceIdentifier):
                    app_uri = name.value
                    break
        except x509.ExtensionNotFound:
            pass

        print("🔒 OPC-UA Certificate Information")
        print("=" * 60)
        print(f"Common Name: {cn}")
        print(f"Organization: {org}")
        print(f"Application URI: {app_uri}")
        print(f"Serial Number: {certificate.serial_number}")
        print(f"Valid From: {not_valid_before.isoformat()}")
        print(f"Valid Until: {not_valid_after.isoformat()}")
        print(f"Days Until Expiry: {days_until_expiry}")

        if days_until_expiry < 0:
            print("⚠️  Status: EXPIRED")
        elif days_until_expiry < 30:
            print("⚠️  Status: EXPIRING SOON")
        else:
            print("✅ Status: VALID")

        print("=" * 60)

    def list_trusted_certificates(self):
        """List all trusted server certificates."""
        trusted_certs = list(self.trusted_dir.glob('*.der'))

        print(f"📋 Trusted Server Certificates ({len(trusted_certs)})")
        print("=" * 60)

        if not trusted_certs:
            print("No trusted server certificates")
            return

        for cert_path in trusted_certs:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()

            try:
                certificate = x509.load_der_x509_certificate(cert_data, default_backend())
                cn = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                expires = certificate.not_valid_after
                days = (expires - datetime.utcnow()).days

                status = "✅" if days > 30 else "⚠️ " if days > 0 else "❌"
                print(f"{status} {cn}")
                print(f"   File: {cert_path.name}")
                print(f"   Expires: {expires.date()} ({days} days)")
                print()
            except Exception as e:
                print(f"❌ {cert_path.name} - Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='OPC-UA Certificate Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate client certificate
  python scripts/generate_opcua_cert.py --generate

  # Generate with custom Application URI
  python scripts/generate_opcua_cert.py --generate \\
    --app-uri "urn:company:unified-connector:client"

  # Show certificate information
  python scripts/generate_opcua_cert.py --info

  # Trust server certificate
  python scripts/generate_opcua_cert.py --trust-server server_cert.der

  # List trusted certificates
  python scripts/generate_opcua_cert.py --list-trusted

After generating:
  1. Update config.yaml with certificate paths
  2. Export server certificate from OPC-UA server
  3. Trust server certificate using --trust-server
  4. Test connection with security enabled

OPC-UA Security Modes:
  - Sign: Messages are signed (integrity)
  - SignAndEncrypt: Messages are signed and encrypted (confidentiality + integrity)

NIS2 Compliance: Article 21.2(h) - Encryption in transit
        """
    )

    # Action group
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--generate', action='store_true', help='Generate client certificate')
    action_group.add_argument('--info', action='store_true', help='Show certificate information')
    action_group.add_argument('--trust-server', type=Path, help='Trust server certificate')
    action_group.add_argument('--list-trusted', action='store_true', help='List trusted certificates')

    # Certificate options
    parser.add_argument('--app-uri', default='urn:unified-ot-connector:client',
                       help='Application URI (default: urn:unified-ot-connector:client)')
    parser.add_argument('--common-name', default='Unified OT Connector Client',
                       help='Common Name (default: Unified OT Connector Client)')
    parser.add_argument('--organization', default='Unified OT Connector',
                       help='Organization (default: Unified OT Connector)')
    parser.add_argument('--days', type=int, default=365, help='Validity in days (default: 365)')
    parser.add_argument('--key-size', type=int, default=2048, choices=[2048, 4096],
                       help='Key size in bits (default: 2048)')

    args = parser.parse_args()

    cert_manager = OPCUACertificateManager()

    try:
        if args.generate:
            cert_file, key_file = cert_manager.generate_client_certificate(
                application_uri=args.app_uri,
                organization=args.organization,
                common_name=args.common_name,
                validity_days=args.days,
                key_size=args.key_size
            )

            cert_manager.print_certificate_info()

            print()
            print("📝 Next Steps:")
            print("=" * 60)
            print("1. Update config.yaml:")
            print("   sources:")
            print("     - name: my-opcua-server")
            print("       protocol: opcua")
            print("       endpoint: opc.tcp://server:4840")
            print("       security:")
            print("         enabled: true")
            print("         security_policy: Basic256Sha256")
            print("         security_mode: SignAndEncrypt")
            print(f"         client_cert_path: {cert_file}")
            print(f"         client_key_path: {key_file}")
            print()
            print("2. Export server certificate from OPC-UA server")
            print("3. Trust server certificate:")
            print("   python scripts/generate_opcua_cert.py --trust-server server_cert.der")
            print()

        elif args.info:
            cert_manager.print_certificate_info()

        elif args.trust_server:
            cert_manager.trust_server_certificate(args.trust_server)

        elif args.list_trusted:
            cert_manager.list_trusted_certificates()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
