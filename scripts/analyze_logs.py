#!/usr/bin/env python3
"""
Log Analysis Utility for Unified OT Zerobus Connector.

Provides tools for analyzing logs for:
- Security event analysis
- Audit trail reporting
- Performance metrics analysis
- Error pattern detection
- Compliance reporting

Usage:
    python analyze_logs.py --log-file logs/unified_connector.log --report security
    python analyze_logs.py --audit-report --start-date 2025-01-01 --end-date 2025-01-31
    python analyze_logs.py --performance-summary --component bridge
"""

import argparse
import gzip
import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys


class LogAnalyzer:
    """Log analysis utility."""

    def __init__(self, log_dir: Path = Path('logs')):
        """
        Initialize log analyzer.

        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = log_dir

    def _read_log_file(self, log_file: Path) -> List[str]:
        """
        Read log file (handles gzip compression).

        Args:
            log_file: Path to log file

        Returns:
            List of log lines
        """
        if log_file.suffix == '.gz':
            with gzip.open(log_file, 'rt', encoding='utf-8') as f:
                return f.readlines()
        else:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.readlines()

    def _parse_json_log(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON log line.

        Args:
            line: Log line

        Returns:
            Parsed log entry or None
        """
        try:
            return json.loads(line.strip())
        except (json.JSONDecodeError, ValueError):
            return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse ISO 8601 timestamp.

        Args:
            timestamp_str: Timestamp string

        Returns:
            Datetime object or None
        """
        try:
            # Remove 'Z' suffix if present
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            return None

    def analyze_security_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze security events from logs.

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Security analysis report
        """
        # Find all log files
        log_files = list(self.log_dir.glob('unified_connector.log*'))
        log_files.extend(list(self.log_dir.glob('audit.log*')))

        # Event counters
        event_counts = Counter()
        auth_failures = []
        authz_denials = []
        injection_attempts = []
        config_changes = []

        for log_file in sorted(log_files):
            for line in self._read_log_file(log_file):
                entry = self._parse_json_log(line)
                if not entry:
                    continue

                # Parse timestamp
                timestamp = self._parse_timestamp(entry.get('timestamp', ''))
                if not timestamp:
                    continue

                # Apply date filter
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue

                # Categorize event
                event_category = entry.get('event_category', '')
                if event_category:
                    event_counts[event_category] += 1

                    # Track specific security events
                    if 'auth.failure' in event_category:
                        auth_failures.append({
                            'timestamp': entry.get('timestamp'),
                            'user': entry.get('user'),
                            'source_ip': entry.get('source_ip'),
                            'reason': entry.get('details', {}).get('reason', 'unknown'),
                        })

                    elif 'authz.denied' in event_category:
                        authz_denials.append({
                            'timestamp': entry.get('timestamp'),
                            'user': entry.get('user'),
                            'action': entry.get('action'),
                            'resource': entry.get('details', {}).get('resource', 'unknown'),
                        })

                    elif 'injection' in event_category:
                        injection_attempts.append({
                            'timestamp': entry.get('timestamp'),
                            'user': entry.get('user'),
                            'source_ip': entry.get('source_ip'),
                            'attack_type': entry.get('details', {}).get('attack_type', 'unknown'),
                        })

                    elif 'config.changed' in event_category:
                        config_changes.append({
                            'timestamp': entry.get('timestamp'),
                            'user': entry.get('user'),
                            'config_type': entry.get('details', {}).get('config_type', 'unknown'),
                        })

        return {
            'summary': {
                'total_events': sum(event_counts.values()),
                'event_categories': dict(event_counts),
                'analysis_period': {
                    'start': start_date.isoformat() if start_date else 'all',
                    'end': end_date.isoformat() if end_date else 'all',
                },
            },
            'security_incidents': {
                'authentication_failures': len(auth_failures),
                'authorization_denials': len(authz_denials),
                'injection_attempts': len(injection_attempts),
                'config_changes': len(config_changes),
            },
            'details': {
                'recent_auth_failures': auth_failures[-10:],
                'recent_authz_denials': authz_denials[-10:],
                'recent_injection_attempts': injection_attempts[-10:],
                'recent_config_changes': config_changes[-10:],
            },
        }

    def generate_audit_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate audit trail report (NIS2 compliance).

        Args:
            start_date: Start date filter
            end_date: End date filter
            user: User filter

        Returns:
            Audit report
        """
        # Find audit log files
        log_files = list(self.log_dir.glob('audit.log*'))

        # Audit entry counters
        actions_by_user = defaultdict(list)
        actions_by_type = Counter()
        actions_by_result = Counter()

        for log_file in sorted(log_files):
            for line in self._read_log_file(log_file):
                entry = self._parse_json_log(line)
                if not entry or entry.get('log_type') != 'audit':
                    continue

                # Parse timestamp
                timestamp = self._parse_timestamp(entry.get('timestamp', ''))
                if not timestamp:
                    continue

                # Apply filters
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                if user and entry.get('user') != user:
                    continue

                # Track actions
                user_id = entry.get('user', 'unknown')
                action = entry.get('action', 'unknown')
                result = entry.get('result', 'unknown')

                actions_by_user[user_id].append({
                    'timestamp': entry.get('timestamp'),
                    'action': action,
                    'resource': entry.get('resource'),
                    'result': result,
                })

                actions_by_type[action] += 1
                actions_by_result[result] += 1

        return {
            'summary': {
                'total_actions': sum(actions_by_type.values()),
                'unique_users': len(actions_by_user),
                'analysis_period': {
                    'start': start_date.isoformat() if start_date else 'all',
                    'end': end_date.isoformat() if end_date else 'all',
                },
            },
            'actions_by_type': dict(actions_by_type),
            'actions_by_result': dict(actions_by_result),
            'user_activity': {
                user: len(actions) for user, actions in actions_by_user.items()
            },
            'details': {
                user: actions[-10:] for user, actions in list(actions_by_user.items())[:5]
            },
        }

    def analyze_performance_metrics(
        self,
        component: Optional[str] = None,
        metric_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze performance metrics.

        Args:
            component: Component filter
            metric_name: Metric name filter
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Performance analysis report
        """
        # Find performance log files
        log_files = list(self.log_dir.glob('performance.log*'))

        # Metric aggregation
        metrics_by_name = defaultdict(list)
        metrics_by_component = defaultdict(list)

        for log_file in sorted(log_files):
            for line in self._read_log_file(log_file):
                entry = self._parse_json_log(line)
                if not entry or entry.get('log_type') != 'performance':
                    continue

                # Parse timestamp
                timestamp = self._parse_timestamp(entry.get('timestamp', ''))
                if not timestamp:
                    continue

                # Apply filters
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                if component and entry.get('component') != component:
                    continue
                if metric_name and entry.get('metric_name') != metric_name:
                    continue

                # Collect metrics
                name = entry.get('metric_name')
                comp = entry.get('component')
                value = entry.get('metric_value')

                metrics_by_name[name].append(value)
                metrics_by_component[comp].append({
                    'name': name,
                    'value': value,
                    'unit': entry.get('metric_unit'),
                })

        # Calculate statistics
        stats_by_name = {}
        for name, values in metrics_by_name.items():
            if values:
                stats_by_name[name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'p50': self._percentile(values, 50),
                    'p95': self._percentile(values, 95),
                    'p99': self._percentile(values, 99),
                }

        return {
            'summary': {
                'total_metrics': sum(len(v) for v in metrics_by_name.values()),
                'unique_metric_names': len(metrics_by_name),
                'components': list(metrics_by_component.keys()),
                'analysis_period': {
                    'start': start_date.isoformat() if start_date else 'all',
                    'end': end_date.isoformat() if end_date else 'all',
                },
            },
            'statistics': stats_by_name,
            'by_component': {
                comp: len(metrics) for comp, metrics in metrics_by_component.items()
            },
        }

    def _percentile(self, values: List[float], percentile: int) -> float:
        """
        Calculate percentile.

        Args:
            values: List of values
            percentile: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100.0)
        f = int(k)
        c = f + 1

        if c >= len(sorted_values):
            return sorted_values[-1]

        d0 = sorted_values[f] * (c - k)
        d1 = sorted_values[c] * (k - f)

        return d0 + d1

    def detect_error_patterns(self) -> Dict[str, Any]:
        """
        Detect common error patterns in logs.

        Returns:
            Error pattern analysis
        """
        # Find all log files
        log_files = list(self.log_dir.glob('unified_connector.log*'))

        # Error tracking
        error_counts = Counter()
        error_messages = defaultdict(list)

        for log_file in sorted(log_files):
            for line in self._read_log_file(log_file):
                # Try JSON format first
                entry = self._parse_json_log(line)
                if entry:
                    level = entry.get('level', '')
                    if level in ('ERROR', 'CRITICAL'):
                        message = entry.get('message', '')
                        error_type = self._categorize_error(message)
                        error_counts[error_type] += 1
                        error_messages[error_type].append({
                            'timestamp': entry.get('timestamp'),
                            'message': message[:200],  # Limit length
                        })
                else:
                    # Plain text format
                    if ' - ERROR - ' in line or ' - CRITICAL - ' in line:
                        error_type = self._categorize_error(line)
                        error_counts[error_type] += 1
                        # Extract timestamp if present
                        match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        timestamp = match.group(1) if match else 'unknown'
                        error_messages[error_type].append({
                            'timestamp': timestamp,
                            'message': line[:200],
                        })

        return {
            'summary': {
                'total_errors': sum(error_counts.values()),
                'error_types': len(error_counts),
            },
            'error_counts': dict(error_counts.most_common(10)),
            'recent_errors': {
                error_type: messages[-5:]
                for error_type, messages in list(error_messages.items())[:5]
            },
        }

    def _categorize_error(self, message: str) -> str:
        """
        Categorize error by message content.

        Args:
            message: Error message

        Returns:
            Error category
        """
        message_lower = message.lower()

        if 'connection' in message_lower or 'connect' in message_lower:
            return 'connection_error'
        elif 'timeout' in message_lower:
            return 'timeout_error'
        elif 'authentication' in message_lower or 'auth' in message_lower:
            return 'authentication_error'
        elif 'permission' in message_lower or 'denied' in message_lower:
            return 'permission_error'
        elif 'certificate' in message_lower or 'tls' in message_lower or 'ssl' in message_lower:
            return 'certificate_error'
        elif 'configuration' in message_lower or 'config' in message_lower:
            return 'configuration_error'
        elif 'database' in message_lower or 'databricks' in message_lower:
            return 'database_error'
        elif 'network' in message_lower:
            return 'network_error'
        elif 'file' in message_lower or 'path' in message_lower:
            return 'file_error'
        else:
            return 'general_error'


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Log Analysis Utility for Unified OT Zerobus Connector'
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        default='logs',
        help='Log directory path (default: logs)'
    )

    parser.add_argument(
        '--report',
        type=str,
        choices=['security', 'audit', 'performance', 'errors', 'all'],
        help='Report type to generate'
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
        '--user',
        type=str,
        help='Filter by user (for audit reports)'
    )

    parser.add_argument(
        '--component',
        type=str,
        help='Filter by component (for performance reports)'
    )

    parser.add_argument(
        '--metric',
        type=str,
        help='Filter by metric name (for performance reports)'
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

    # Initialize analyzer
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Error: Log directory '{log_dir}' does not exist", file=sys.stderr)
        sys.exit(1)

    analyzer = LogAnalyzer(log_dir)

    # Parse dates
    start_date = None
    end_date = None

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
    reports = {}

    if args.report in ('security', 'all'):
        print("Analyzing security events...", file=sys.stderr)
        reports['security'] = analyzer.analyze_security_events(start_date, end_date)

    if args.report in ('audit', 'all'):
        print("Generating audit report...", file=sys.stderr)
        reports['audit'] = analyzer.generate_audit_report(start_date, end_date, args.user)

    if args.report in ('performance', 'all'):
        print("Analyzing performance metrics...", file=sys.stderr)
        reports['performance'] = analyzer.analyze_performance_metrics(
            args.component, args.metric, start_date, end_date
        )

    if args.report in ('errors', 'all'):
        print("Detecting error patterns...", file=sys.stderr)
        reports['errors'] = analyzer.detect_error_patterns()

    if not reports:
        print("Error: No report type specified. Use --report", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Output report
    if args.format == 'json':
        output = json.dumps(reports, indent=2, default=str)
    else:
        # Text format
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("LOG ANALYSIS REPORT")
        output_lines.append("=" * 80)
        output_lines.append("")

        for report_type, report_data in reports.items():
            output_lines.append(f"\n{report_type.upper()} REPORT")
            output_lines.append("-" * 80)
            output_lines.append(json.dumps(report_data, indent=2, default=str))
            output_lines.append("")

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
