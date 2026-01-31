#!/usr/bin/env python3
"""
Incident Reporting and Analysis Tool.

Generates comprehensive incident reports for:
- Post-incident review
- Compliance reporting (NIS2)
- Lessons learned documentation
- Management summaries

Usage:
    python incident_report.py --incident INC-20250131-0001
    python incident_report.py --summary --month 2025-01
    python incident_report.py --compliance-report --quarter Q1-2025
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class IncidentReporter:
    """Generate incident reports and analysis."""

    def __init__(self, incident_dir: Path = Path('incidents')):
        """
        Initialize incident reporter.

        Args:
            incident_dir: Directory containing incident JSON files
        """
        self.incident_dir = incident_dir

    def generate_incident_report(self, incident_id: str) -> Dict[str, Any]:
        """
        Generate detailed report for a single incident.

        Args:
            incident_id: Incident ID

        Returns:
            Incident report
        """
        # Load incident
        incident_file = self.incident_dir / f"{incident_id}.json"
        if not incident_file.exists():
            raise FileNotFoundError(f"Incident not found: {incident_id}")

        with open(incident_file, 'r') as f:
            incident = json.load(f)

        # Calculate metrics
        created_at = self._parse_timestamp(incident['created_at'])
        updated_at = self._parse_timestamp(incident['updated_at'])

        response_time = None
        resolution_time = None

        # Find acknowledgment time
        ack_time = None
        resolution_timestamp = None

        for entry in incident.get('timeline', []):
            action = entry.get('action', '')
            if action == 'status_changed' and 'acknowledged' in entry.get('details', ''):
                ack_time = self._parse_timestamp(entry['timestamp'])
            if action == 'status_changed' and 'resolved' in entry.get('details', ''):
                resolution_timestamp = self._parse_timestamp(entry['timestamp'])

        if ack_time and created_at:
            response_time = (ack_time - created_at).total_seconds() / 60.0  # Minutes

        if resolution_timestamp and created_at:
            resolution_time = (resolution_timestamp - created_at).total_seconds() / 3600.0  # Hours

        # Generate report
        report = {
            'incident_id': incident_id,
            'title': incident['title'],
            'severity': incident['severity'],
            'category': incident['category'],
            'status': incident['status'],

            'timeline': {
                'created_at': incident['created_at'],
                'updated_at': incident['updated_at'],
                'response_time_minutes': response_time,
                'resolution_time_hours': resolution_time,
            },

            'affected': {
                'source_ip': incident.get('source_ip'),
                'affected_user': incident.get('affected_user'),
                'systems': self._extract_affected_systems(incident),
            },

            'description': incident['description'],

            'timeline_events': incident.get('timeline', []),

            'alerts': incident.get('alerts', []),

            'response_actions': incident.get('response_actions', []),

            'resolution': incident.get('resolution_notes'),

            'compliance': {
                'nis2_notifiable': self._is_nis2_notifiable(incident),
                'notification_deadline': self._get_notification_deadline(incident),
                'impact_assessment': self._assess_impact(incident),
            },

            'recommendations': self._generate_recommendations(incident),
        }

        return report

    def generate_summary_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate summary report for period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Summary report
        """
        # Default to last 30 days
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Load all incidents in date range
        incidents = self._load_incidents_in_range(start_date, end_date)

        # Calculate statistics
        total_incidents = len(incidents)

        incidents_by_severity = Counter(i['severity'] for i in incidents)
        incidents_by_category = Counter(i['category'] for i in incidents)
        incidents_by_status = Counter(i['status'] for i in incidents)

        # Calculate average response/resolution times
        response_times = []
        resolution_times = []

        for incident in incidents:
            created_at = self._parse_timestamp(incident['created_at'])

            for entry in incident.get('timeline', []):
                action = entry.get('action', '')
                if action == 'status_changed' and 'acknowledged' in entry.get('details', ''):
                    ack_time = self._parse_timestamp(entry['timestamp'])
                    if ack_time and created_at:
                        response_times.append((ack_time - created_at).total_seconds() / 60.0)

                if action == 'status_changed' and 'resolved' in entry.get('details', ''):
                    res_time = self._parse_timestamp(entry['timestamp'])
                    if res_time and created_at:
                        resolution_times.append((res_time - created_at).total_seconds() / 3600.0)

        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else None

        # Identify trends
        incidents_by_day = defaultdict(int)
        for incident in incidents:
            created_at = self._parse_timestamp(incident['created_at'])
            if created_at:
                day = created_at.date().isoformat()
                incidents_by_day[day] += 1

        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },

            'summary': {
                'total_incidents': total_incidents,
                'by_severity': dict(incidents_by_severity),
                'by_category': dict(incidents_by_category),
                'by_status': dict(incidents_by_status),
            },

            'performance_metrics': {
                'average_response_time_minutes': round(avg_response_time, 2) if avg_response_time else None,
                'average_resolution_time_hours': round(avg_resolution_time, 2) if avg_resolution_time else None,
                'incidents_resolved': incidents_by_status.get('resolved', 0) + incidents_by_status.get('closed', 0),
                'resolution_rate': round(
                    (incidents_by_status.get('resolved', 0) + incidents_by_status.get('closed', 0)) / total_incidents * 100, 1
                ) if total_incidents > 0 else 0,
            },

            'trends': {
                'incidents_by_day': dict(sorted(incidents_by_day.items())),
                'peak_day': max(incidents_by_day.items(), key=lambda x: x[1])[0] if incidents_by_day else None,
            },

            'top_incidents': [
                {
                    'incident_id': i['incident_id'],
                    'title': i['title'],
                    'severity': i['severity'],
                    'category': i['category'],
                    'created_at': i['created_at'],
                }
                for i in sorted(incidents, key=lambda x: (
                    {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['severity'], 4),
                    x['created_at']
                ))[:10]
            ],
        }

        return report

    def generate_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate NIS2 compliance report.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Compliance report
        """
        # Default to last quarter
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=90)

        # Load incidents
        incidents = self._load_incidents_in_range(start_date, end_date)

        # Categorize incidents for NIS2
        notifiable_incidents = [i for i in incidents if self._is_nis2_notifiable(i)]
        critical_incidents = [i for i in incidents if i['severity'] == 'critical']
        security_breaches = [i for i in incidents if 'breach' in i.get('category', '')]

        # Check notification compliance
        notification_compliance = []
        for incident in notifiable_incidents:
            deadline = self._get_notification_deadline(incident)
            notification_made = self._check_notification_made(incident)

            notification_compliance.append({
                'incident_id': incident['incident_id'],
                'deadline': deadline.isoformat() if deadline else None,
                'notification_made': notification_made,
                'compliant': notification_made or (deadline and datetime.utcnow() < deadline),
            })

        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },

            'nis2_compliance': {
                'total_incidents': len(incidents),
                'notifiable_incidents': len(notifiable_incidents),
                'critical_incidents': len(critical_incidents),
                'security_breaches': len(security_breaches),
            },

            'notification_compliance': {
                'total_requiring_notification': len(notifiable_incidents),
                'notifications_made': sum(1 for n in notification_compliance if n['notification_made']),
                'compliant': sum(1 for n in notification_compliance if n['compliant']),
                'compliance_rate': round(
                    sum(1 for n in notification_compliance if n['compliant']) / len(notification_compliance) * 100, 1
                ) if notification_compliance else 100,
            },

            'notification_details': notification_compliance,

            'incident_categories': {
                'authentication_attacks': len([i for i in incidents if 'authentication' in i.get('category', '')]),
                'injection_attacks': len([i for i in incidents if 'injection' in i.get('category', '')]),
                'privilege_escalations': len([i for i in incidents if 'privilege' in i.get('category', '')]),
                'data_breaches': len([i for i in incidents if 'data_breach' in i.get('category', '')]),
                'configuration_errors': len([i for i in incidents if 'configuration' in i.get('category', '')]),
                'system_errors': len([i for i in incidents if 'system' in i.get('category', '')]),
            },

            'recommendations': self._generate_compliance_recommendations(incidents),
        }

        return report

    def _load_incidents_in_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Load all incidents in date range."""
        incidents = []

        for incident_file in self.incident_dir.glob('INC-*.json'):
            try:
                with open(incident_file, 'r') as f:
                    incident = json.load(f)

                created_at = self._parse_timestamp(incident['created_at'])
                if created_at and start_date <= created_at <= end_date:
                    incidents.append(incident)

            except Exception as e:
                print(f"Warning: Failed to load {incident_file}: {e}", file=sys.stderr)

        return incidents

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse ISO 8601 timestamp."""
        try:
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            return None

    def _extract_affected_systems(self, incident: Dict[str, Any]) -> List[str]:
        """Extract affected systems from incident."""
        systems = []

        # Check details
        details = incident.get('details', {})
        if 'affected_systems' in details:
            systems.extend(details['affected_systems'])

        # Check alerts
        for alert in incident.get('alerts', []):
            if 'details' in alert and 'system' in alert['details']:
                systems.append(alert['details']['system'])

        return list(set(systems))

    def _is_nis2_notifiable(self, incident: Dict[str, Any]) -> bool:
        """Check if incident requires NIS2 notification."""
        # Critical incidents are notifiable
        if incident['severity'] == 'critical':
            return True

        # Data breaches are notifiable
        if 'data_breach' in incident.get('category', ''):
            return True

        # Security breaches are notifiable
        if 'security_breach' in incident.get('category', ''):
            return True

        return False

    def _get_notification_deadline(self, incident: Dict[str, Any]) -> Optional[datetime]:
        """Get NIS2 notification deadline (72 hours)."""
        created_at = self._parse_timestamp(incident['created_at'])
        if created_at and self._is_nis2_notifiable(incident):
            return created_at + timedelta(hours=72)
        return None

    def _check_notification_made(self, incident: Dict[str, Any]) -> bool:
        """Check if NIS2 notification was made."""
        for entry in incident.get('timeline', []):
            if 'notification' in entry.get('action', '').lower():
                return True
        return False

    def _assess_impact(self, incident: Dict[str, Any]) -> str:
        """Assess incident impact."""
        severity = incident['severity']
        category = incident.get('category', '')

        if severity == 'critical':
            if 'data_breach' in category:
                return 'HIGH - Data breach with potential regulatory impact'
            elif 'system_compromise' in category:
                return 'HIGH - System compromise requiring immediate response'
            else:
                return 'HIGH - Critical security incident'
        elif severity == 'high':
            return 'MEDIUM - Significant security event requiring investigation'
        else:
            return 'LOW - Minor security event'

    def _generate_recommendations(self, incident: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on incident."""
        recommendations = []

        category = incident.get('category', '')

        if 'injection' in category:
            recommendations.append("Implement comprehensive input validation")
            recommendations.append("Deploy Web Application Firewall (WAF)")
            recommendations.append("Conduct security code review")

        elif 'authentication' in category:
            recommendations.append("Enforce multi-factor authentication (MFA)")
            recommendations.append("Implement account lockout policies")
            recommendations.append("Enable login anomaly detection")

        elif 'privilege' in category:
            recommendations.append("Review and strengthen RBAC implementation")
            recommendations.append("Implement principle of least privilege")
            recommendations.append("Add authorization audit logging")

        elif 'configuration' in category:
            recommendations.append("Implement configuration change management")
            recommendations.append("Require peer review for changes")
            recommendations.append("Enable configuration version control")

        # General recommendations
        recommendations.append("Update incident response procedures")
        recommendations.append("Provide security awareness training")
        recommendations.append("Schedule follow-up security audit")

        return recommendations

    def _generate_compliance_recommendations(self, incidents: List[Dict[str, Any]]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []

        # Check incident patterns
        critical_count = len([i for i in incidents if i['severity'] == 'critical'])
        if critical_count > 5:
            recommendations.append("High number of critical incidents - conduct comprehensive security audit")

        auth_attacks = len([i for i in incidents if 'authentication' in i.get('category', '')])
        if auth_attacks > 3:
            recommendations.append("Multiple authentication attacks - enforce MFA for all users")

        injection_attacks = len([i for i in incidents if 'injection' in i.get('category', '')])
        if injection_attacks > 0:
            recommendations.append("Injection attacks detected - implement WAF and input validation")

        # General NIS2 recommendations
        recommendations.append("Maintain 24/7 security monitoring")
        recommendations.append("Conduct quarterly incident response drills")
        recommendations.append("Update incident response playbooks based on lessons learned")
        recommendations.append("Ensure all incidents are properly documented for regulatory compliance")

        return recommendations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Incident Reporting and Analysis Tool'
    )

    parser.add_argument(
        '--incident',
        type=str,
        help='Generate report for specific incident (e.g., INC-20250131-0001)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Generate summary report'
    )

    parser.add_argument(
        '--compliance-report',
        action='store_true',
        help='Generate NIS2 compliance report'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (ISO format: YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (ISO format: YYYY-MM-DD)'
    )

    parser.add_argument(
        '--month',
        type=str,
        help='Report for specific month (YYYY-MM)'
    )

    parser.add_argument(
        '--quarter',
        type=str,
        help='Report for specific quarter (Q1-YYYY, Q2-YYYY, etc.)'
    )

    parser.add_argument(
        '--incident-dir',
        type=str,
        default='incidents',
        help='Incident directory path (default: incidents)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file for report (default: stdout)'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    args = parser.parse_args()

    # Initialize reporter
    incident_dir = Path(args.incident_dir)
    if not incident_dir.exists():
        print(f"Error: Incident directory '{incident_dir}' does not exist", file=sys.stderr)
        sys.exit(1)

    reporter = IncidentReporter(incident_dir)

    # Parse dates
    start_date = None
    end_date = None

    if args.month:
        # Parse month (YYYY-MM)
        try:
            year, month = map(int, args.month.split('-'))
            start_date = datetime(year, month, 1)
            # Last day of month
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        except ValueError:
            print(f"Error: Invalid month format '{args.month}'", file=sys.stderr)
            sys.exit(1)

    elif args.quarter:
        # Parse quarter (Q1-YYYY, etc.)
        try:
            q, year = args.quarter.split('-')
            year = int(year)
            quarter = int(q[1])

            start_month = (quarter - 1) * 3 + 1
            start_date = datetime(year, start_month, 1)
            end_month = start_month + 2
            if end_month > 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            print(f"Error: Invalid quarter format '{args.quarter}'", file=sys.stderr)
            sys.exit(1)

    else:
        if args.start_date:
            try:
                start_date = datetime.fromisoformat(args.start_date)
            except ValueError:
                print(f"Error: Invalid start date '{args.start_date}'", file=sys.stderr)
                sys.exit(1)

        if args.end_date:
            try:
                end_date = datetime.fromisoformat(args.end_date)
            except ValueError:
                print(f"Error: Invalid end date '{args.end_date}'", file=sys.stderr)
                sys.exit(1)

    # Generate reports
    report = None

    if args.incident:
        print(f"Generating incident report for {args.incident}...", file=sys.stderr)
        report = reporter.generate_incident_report(args.incident)
        report_title = f"INCIDENT REPORT: {args.incident}"

    elif args.summary:
        print("Generating summary report...", file=sys.stderr)
        report = reporter.generate_summary_report(start_date, end_date)
        report_title = "INCIDENT SUMMARY REPORT"

    elif args.compliance_report:
        print("Generating compliance report...", file=sys.stderr)
        report = reporter.generate_compliance_report(start_date, end_date)
        report_title = "NIS2 COMPLIANCE REPORT"

    else:
        print("Error: Must specify --incident, --summary, or --compliance-report", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Output report
    if args.format == 'json':
        output = json.dumps(report, indent=2, default=str)
    else:
        # Text format
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append(report_title)
        output_lines.append("=" * 80)
        output_lines.append("")
        output_lines.append(json.dumps(report, indent=2, default=str))

        output = "\n".join(output_lines)

    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
