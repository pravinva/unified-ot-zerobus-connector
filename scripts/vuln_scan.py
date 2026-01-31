#!/usr/bin/env python3
"""
Vulnerability Scanning Tool.

Scans for vulnerabilities in:
- Python dependencies (pip packages)
- OS packages
- Container images

Usage:
    python vuln_scan.py --full
    python vuln_scan.py --python
    python vuln_scan.py --os
    python vuln_scan.py --summary
    python vuln_scan.py --priority
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_connector.core.vulnerability_management import (
    get_vulnerability_system,
    VulnerabilityStatus,
    VulnerabilitySeverity
)


async def main_async(args):
    """Async main function."""
    # Initialize vulnerability system
    vuln_system = get_vulnerability_system()

    if args.full:
        # Run full scan
        print("Running full vulnerability scan...")
        print("=" * 80)

        results = await vuln_system.run_full_scan()

        # Print results
        print("\nScan Results:")
        print("-" * 80)
        for scanner, vulns in results.items():
            print(f"\n{scanner}: {len(vulns)} vulnerabilities")
            for vuln in vulns[:5]:  # Show first 5
                print(f"  - {vuln.vuln_id}: {vuln.title} ({vuln.severity.value})")
            if len(vulns) > 5:
                print(f"  ... and {len(vulns) - 5} more")

        # Print summary
        print("\n" + "=" * 80)
        print("Summary:")
        summary = vuln_system.get_summary()
        print(json.dumps(summary, indent=2))

    elif args.python:
        # Scan Python dependencies only
        print("Scanning Python dependencies...")
        print("=" * 80)

        vulns_pip = await vuln_system.scanner.scan_python_dependencies()
        vulns_safety = await vuln_system.scanner.scan_with_safety()

        print(f"\npip-audit found: {len(vulns_pip)} vulnerabilities")
        print(f"safety found: {len(vulns_safety)} vulnerabilities")

        # Add to manager
        for vuln in vulns_pip + vulns_safety:
            vuln_system.manager.add_vulnerability(vuln)

        # Print details
        all_vulns = vulns_pip + vulns_safety
        for vuln in all_vulns:
            print(f"\n{vuln.vuln_id}")
            print(f"  Package: {vuln.component_name} {vuln.component_version}")
            print(f"  Severity: {vuln.severity.value}")
            print(f"  Fix: {vuln.fixed_version if vuln.fix_available else 'No fix available'}")

    elif args.os:
        # Scan OS packages only
        print("Scanning OS packages...")
        print("=" * 80)

        vulns = await vuln_system.scanner.scan_os_packages()

        print(f"\nFound: {len(vulns)} outdated packages")

        for vuln in vulns:
            vuln_system.manager.add_vulnerability(vuln)
            print(f"  - {vuln.component_name}: {vuln.component_version} → {vuln.fixed_version}")

    elif args.summary:
        # Print summary
        print("Vulnerability Summary")
        print("=" * 80)

        summary = vuln_system.get_summary()

        print(f"\nTotal Vulnerabilities: {summary['total']}")
        print(f"\nBy Severity:")
        for severity, count in summary['by_severity'].items():
            print(f"  {severity.upper()}: {count}")

        print(f"\nBy Status:")
        for status, count in summary['by_status'].items():
            if count > 0:
                print(f"  {status}: {count}")

        print(f"\nFixable: {summary['fixable']} ({summary['fix_rate']}%)")

    elif args.priority:
        # Print prioritized list
        print("Prioritized Vulnerability List")
        print("=" * 80)

        vulns = vuln_system.get_prioritized_list()

        if not vulns:
            print("\nNo active vulnerabilities found!")
        else:
            print(f"\nTotal active vulnerabilities: {len(vulns)}")
            print("\nTop 20 (highest priority):")
            print("-" * 80)

            for i, vuln in enumerate(vulns[:20], 1):
                fix_status = f"Fix: {vuln.fixed_version}" if vuln.fix_available else "No fix"
                print(f"{i}. {vuln.vuln_id} - {vuln.severity.value.upper()}")
                print(f"   {vuln.component_name} {vuln.component_version}")
                print(f"   {fix_status}")
                print()

    elif args.update:
        # Update vulnerability status
        vuln_system.manager.update_vulnerability(
            vuln_id=args.vuln_id,
            status=VulnerabilityStatus(args.status) if args.status else None,
            patch_deployed_at=args.patch_deployed if args.patch_deployed else None,
            mitigation_notes=args.notes,
        )
        print(f"Updated vulnerability {args.vuln_id}")

    elif args.details:
        # Show vulnerability details
        vuln = vuln_system.manager.get_vulnerability(args.vuln_id)
        if vuln:
            print("Vulnerability Details")
            print("=" * 80)
            print(json.dumps(vuln.to_dict(), indent=2, default=str))
        else:
            print(f"Vulnerability not found: {args.vuln_id}")

    else:
        print("Error: Must specify an action (--full, --python, --os, --summary, --priority)")
        return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Vulnerability Scanning Tool'
    )

    # Scan actions
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full vulnerability scan (all scanners)'
    )

    parser.add_argument(
        '--python',
        action='store_true',
        help='Scan Python dependencies only'
    )

    parser.add_argument(
        '--os',
        action='store_true',
        help='Scan OS packages only'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show vulnerability summary'
    )

    parser.add_argument(
        '--priority',
        action='store_true',
        help='Show prioritized vulnerability list'
    )

    # Update action
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update vulnerability status'
    )

    parser.add_argument(
        '--vuln-id',
        type=str,
        help='Vulnerability ID (for --update or --details)'
    )

    parser.add_argument(
        '--status',
        type=str,
        choices=['detected', 'assessed', 'patching_available', 'patching_scheduled', 'patched', 'mitigated', 'accepted_risk', 'false_positive'],
        help='New status (for --update)'
    )

    parser.add_argument(
        '--patch-deployed',
        type=str,
        help='Patch deployment timestamp (for --update)'
    )

    parser.add_argument(
        '--notes',
        type=str,
        help='Mitigation notes (for --update)'
    )

    # Details action
    parser.add_argument(
        '--details',
        action='store_true',
        help='Show vulnerability details'
    )

    args = parser.parse_args()

    # Run async main
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
