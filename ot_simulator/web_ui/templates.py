"""HTML/CSS/JavaScript templates for the web UI.

This module contains all the front-end templates separated from the backend logic.
"""

from __future__ import annotations

from ot_simulator.web_ui.training_ui import get_training_ui_html


def get_head_html() -> str:
    """Return the HTML head section with meta tags and external resources."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Databricks OT Simulator - Professional Edition</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cdefs%3E%3ClinearGradient id='grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%23FF3621;stop-opacity:1' /%3E%3Cstop offset='100%25' style='stop-color:%23FF8A00;stop-opacity:1' /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='100' height='100' rx='20' fill='url(%23grad)'/%3E%3Cg fill='white'%3E%3Ccircle cx='30' cy='50' r='8'/%3E%3Ccircle cx='50' cy='30' r='8'/%3E%3Ccircle cx='50' cy='70' r='8'/%3E%3Ccircle cx='70' cy='50' r='8'/%3E%3Cline x1='30' y1='50' x2='50' y2='30' stroke='white' stroke-width='3'/%3E%3Cline x1='30' y1='50' x2='50' y2='70' stroke='white' stroke-width='3'/%3E%3Cline x1='50' y1='30' x2='70' y2='50' stroke='white' stroke-width='3'/%3E%3Cline x1='50' y1='70' x2='70' y2='50' stroke='white' stroke-width='3'/%3E%3C/g%3E%3C/svg%3E">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/fft.js@4.0.3/lib/fft.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/plotly.js@2.27.0/dist/plotly.min.js"></script>"""


def get_styles_html() -> str:
    """Return the CSS styles for the web UI."""
    return """    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #F7F8FA;
            color: #2E3036;
            min-height: 100vh;
            padding: 24px;
            overflow-x: hidden;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            background: white;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            padding: 32px;
            margin-bottom: 32px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .logo-section {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }

        .databricks-logo {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #FF3621 0%, #FF6B58 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 24px;
            color: white;
            box-shadow: 0 4px 16px rgba(255, 54, 33, 0.4);
        }

        h1 {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #FF3621 0%, #00A9E0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: #6B7280;
            margin-top: 8px;
            font-size: 14px;
        }

        /* Main Grid */
        .main-grid {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        /* Sidebar */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .card {
            background: white;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .protocol-selector {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .protocol-item {
            display: flex;
            flex-direction: column;
            background: #F9FAFB;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            transition: all 0.3s;
            width: 100%;
        }

        .protocol-item:hover {
            background: #F3F4F6;
            border-color: #D1D5DB;
        }

        .protocol-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 24px;
            min-height: 70px;
            gap: 24px;
            flex-wrap: nowrap;
        }

        .protocol-config-panel {
            display: none;
            padding: 0 24px 20px 24px;
            border-top: 1px solid #E3E5E8;
            background: white;
        }

        .protocol-config-panel.expanded {
            display: block;
        }

        .config-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }

        .config-field {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .config-label {
            font-size: 12px;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .config-input {
            padding: 10px 12px;
            background: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-size: 14px;
            color: #2E3036;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
        }

        .config-input:focus {
            outline: none;
            border-color: #FF3621;
            background: white;
            box-shadow: 0 0 0 2px rgba(255, 54, 33, 0.1);
        }

        .config-input::placeholder {
            color: #9CA3AF;
        }

        .config-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 8px 12px;
            background: white;
            border: 1px solid #E3E5E8;
            border-radius: 6px;
            transition: all 0.3s;
            font-size: 13px;
            color: #6B7280;
            font-weight: 500;
        }

        .config-toggle:hover {
            background: #F9FAFB;
            border-color: #D1D5DB;
        }

        .config-toggle-icon {
            transition: transform 0.3s;
        }

        .config-toggle-icon.expanded {
            transform: rotate(180deg);
        }

        .config-actions {
            display: flex;
            gap: 8px;
            margin-top: 16px;
        }

        .btn-save {
            padding: 10px 20px;
            background: #FF3621;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-save:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 54, 33, 0.3);
        }

        .btn-test {
            padding: 10px 20px;
            background: white;
            color: #6B7280;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-test:hover {
            background: #F9FAFB;
            border-color: #9CA3AF;
        }

        .btn-start-zerobus {
            padding: 10px 20px;
            background: #10B981;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s;
        }

        .btn-start-zerobus:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }

        .btn-start-zerobus:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-stop-zerobus {
            padding: 10px 20px;
            background: #EF4444;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s;
        }

        .btn-stop-zerobus:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        }

        .btn-stop-zerobus:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .protocol-badge {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #9CA3AF;
            transition: all 0.3s;
        }

        .protocol-badge.running {
            background: #10B981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }

        .protocol-name {
            font-weight: 600;
            text-transform: uppercase;
            font-size: 13px;
            letter-spacing: 0.5px;
            white-space: nowrap;
            flex-shrink: 0;
            min-width: 80px;
        }

        .protocol-endpoint {
            font-size: 11px;
            color: #6B7280;
            font-family: 'Monaco', 'Courier New', monospace;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1 1 auto;
            min-width: 0;
        }

        .protocol-endpoint a {
            color: #00A9E0;
            text-decoration: none;
            transition: all 0.2s;
        }

        .protocol-endpoint a:hover {
            color: #FF3621;
            text-decoration: underline;
        }

        .protocol-controls {
            display: flex;
            gap: 12px;
            flex-shrink: 0;
            align-self: center;
            flex-wrap: nowrap;
            margin-left: auto;
        }

        .btn {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            min-width: 70px;
            white-space: nowrap;
        }

        .btn-start {
            background: #10B981;
            color: white;
        }

        .btn-start:hover {
            background: #059669;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
        }

        .btn-stop {
            background: #FEE2E2;
            color: #DC2626;
            border: 1px solid #FCA5A5;
        }

        .btn-stop:hover {
            background: #FEF2F2;
        }

        /* Chart Section */
        .chart-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 24px;
        }

        .chart-card {
            background: white;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .chart-title {
            font-size: 14px;
            font-weight: 600;
            color: #6B7280;
            font-family: 'Monaco', 'Courier New', monospace;
        }

        .live-value {
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, #FF3621 0%, #00A9E0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .chart-container {
            position: relative;
            height: 300px;
        }

        /* Advanced Visualization Buttons */
        .btn-fft, .btn-spectrogram, .btn-spc {
            padding: 6px 12px;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-left: 8px;
        }

        .btn-fft {
            background: #00A9E0;
        }

        .btn-fft:hover {
            background: #0088B8;
            transform: translateY(-1px);
        }

        .btn-fft.active {
            background: #FF3621;
        }

        .btn-spectrogram {
            background: #8B5CF6;
        }

        .btn-spectrogram:hover {
            background: #7C3AED;
            transform: translateY(-1px);
        }

        .btn-spectrogram.active {
            background: #FF3621;
        }

        .btn-spc {
            background: #059669;
        }

        .btn-spc:hover {
            background: #047857;
            transform: translateY(-1px);
        }

        .btn-spc.active {
            background: #FF3621;
        }

        .chart-buttons {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        /* Natural Language Chat Button */
        .nlp-chat-button {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: linear-gradient(135deg, #FF3621 0%, #FF6B58 100%);
            color: white;
            border: none;
            padding: 16px 24px;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 8px 32px rgba(255, 54, 33, 0.4);
            transition: all 0.3s;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nlp-chat-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(255, 54, 33, 0.6);
        }

        /* Chat Panel */
        .nlp-chat-panel {
            position: fixed;
            top: 0;
            right: 0;
            width: 450px;
            height: 100vh;
            background: white;
            border-left: 1px solid #E3E5E8;
            box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 2000;
        }

        .nlp-chat-panel.hidden {
            transform: translateX(100%);
        }

        .chat-header {
            padding: 24px;
            border-bottom: 1px solid #E3E5E8;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header h3 {
            font-size: 18px;
            font-weight: 600;
            color: #2E3036;
        }

        .chat-close {
            background: none;
            border: none;
            color: #6B7280;
            font-size: 28px;
            cursor: pointer;
            transition: color 0.3s;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .chat-close:hover {
            color: #2E3036;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: #F3F4F6;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: #D1D5DB;
            border-radius: 4px;
        }

        .message {
            display: flex;
            gap: 12px;
            animation: fadeIn 0.3s ease-out;
        }

        .message.user {
            justify-content: flex-end;
        }

        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }

        .message.user .message-avatar {
            background: linear-gradient(135deg, #00A9E0 0%, #0088C7 100%);
            order: 2;
        }

        .message.agent .message-avatar {
            background: linear-gradient(135deg, #FF3621 0%, #FF6B58 100%);
        }

        .message-content {
            max-width: 70%;
        }

        .message-bubble {
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.5;
        }

        .message.user .message-bubble {
            background: linear-gradient(135deg, #00A9E0 0%, #0088C7 100%);
            color: white;
            border-radius: 16px 16px 4px 16px;
        }

        .message.agent .message-bubble {
            background: #F3F4F6;
            border: 1px solid #E3E5E8;
            color: #2E3036;
            border-radius: 16px 16px 16px 4px;
        }

        .message-reasoning {
            font-size: 12px;
            color: #6B7280;
            margin-top: 4px;
            font-style: italic;
            padding: 8px 12px;
            background: #FEF2F2;
            border-radius: 8px;
            border-left: 2px solid #FF3621;
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px 16px 16px 4px;
            width: fit-content;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #A0A4A8;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.7;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }

        .chat-input-container {
            padding: 24px;
            border-top: 1px solid #E3E5E8;
            display: flex;
            gap: 12px;
        }

        .chat-input {
            flex: 1;
            padding: 12px 16px;
            background: white;
            border: 1px solid #D1D5DB;
            border-radius: 8px;
            color: #2E3036;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
        }

        .chat-input:focus {
            outline: none;
            border-color: #FF3621;
            box-shadow: 0 0 0 2px rgba(255, 54, 33, 0.1);
        }

        .chat-input::placeholder {
            color: #9CA3AF;
        }

        .chat-send {
            padding: 12px 24px;
            background: #FF3621;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .chat-send:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(255, 54, 33, 0.4);
        }

        .chat-send:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                background: rgba(16, 185, 129, 0.2);
            }
            to {
                opacity: 1;
                background: transparent;
            }
        }

        .stream-record-new {
            animation: slideIn 0.4s ease-out;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Sensor Browser */
        .sensor-browser {
            max-height: 500px;
            overflow-y: auto;
        }

        .sensor-browser::-webkit-scrollbar {
            width: 8px;
        }

        .sensor-browser::-webkit-scrollbar-track {
            background: #F3F4F6;
        }

        .sensor-browser::-webkit-scrollbar-thumb {
            background: #D1D5DB;
            border-radius: 4px;
        }

        .industry-accordion {
            margin-bottom: 8px;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }

        .industry-header {
            padding: 12px 16px;
            background: linear-gradient(90deg, #F9FAFB 0%, #F3F4F6 100%);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
            border-bottom: 1px solid transparent;
        }

        .industry-header:hover {
            background: linear-gradient(90deg, #F3F4F6 0%, #E5E7EB 100%);
        }

        .industry-header.active {
            background: linear-gradient(90deg, #DBEAFE 0%, #BFDBFE 100%);
            border-bottom-color: #93C5FD;
        }

        .industry-header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .industry-title {
            font-size: 13px;
            font-weight: 600;
            color: #1F2937;
        }

        .industry-count {
            font-size: 11px;
            color: #6B7280;
            background: #F9FAFB;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 500;
        }

        .industry-chevron {
            font-size: 14px;
            color: #6B7280;
            transition: transform 0.2s;
        }

        .industry-chevron.expanded {
            transform: rotate(90deg);
        }

        .industry-sensors {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }

        .industry-sensors.expanded {
            max-height: 2000px;
            transition: max-height 0.5s ease-in;
        }

        .sensor-item {
            padding: 10px 16px;
            background: white;
            border-bottom: 1px solid #F3F4F6;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .sensor-item:hover {
            background: #F9FAFB;
            border-left: 3px solid #FF3621;
            padding-left: 13px;
        }

        .sensor-item.selected {
            background: #DBEAFE;
            border-left: 4px solid #00A9E0;
            padding-left: 12px;
        }

        .sensor-item.selected:hover {
            background: #BFDBFE;
        }

        .sensor-item:last-child {
            border-bottom: none;
        }

        .sensor-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .sensor-name {
            font-size: 12px;
            font-family: 'Monaco', 'Courier New', monospace;
            color: #1F2937;
            font-weight: 500;
        }

        .sensor-meta {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .sensor-type {
            font-size: 10px;
            color: #6B7280;
        }

        .protocol-badges {
            display: flex;
            gap: 4px;
        }

        .protocol-badge-mini {
            font-size: 9px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .protocol-badge-mini.opcua {
            background: #DBEAFE;
            color: #1E40AF;
        }

        .protocol-badge-mini.mqtt {
            background: #D1FAE5;
            color: #065F46;
        }

        .protocol-badge-mini.modbus {
            background: #FED7AA;
            color: #9A3412;
        }

        .sensor-add {
            font-size: 20px;
            color: #A0A4A8;
            transition: all 0.2s;
        }

        .sensor-item:hover .sensor-add {
            color: #FF3621;
            transform: scale(1.2);
        }

        /* OPC-UA Browser Panel */
        .opcua-browser-panel {
            position: fixed;
            top: 0;
            right: 0;
            width: 550px;
            height: 100vh;
            background: white;
            border-left: 1px solid #E3E5E8;
            box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 2000;
        }

        .opcua-browser-panel.hidden {
            transform: translateX(100%);
        }

        .opcua-browser-header {
            padding: 24px;
            border-bottom: 1px solid #E3E5E8;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #1B3139 0%, #2E4A57 100%);
            color: white;
        }

        .opcua-browser-header h3 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }

        .opcua-browser-close {
            background: none;
            border: none;
            color: white;
            font-size: 28px;
            cursor: pointer;
            transition: color 0.3s;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .opcua-browser-close:hover {
            color: #00A9E0;
        }

        .opcua-search-container {
            padding: 16px;
            border-bottom: 1px solid #E3E5E8;
            background: #F9FAFB;
        }

        .opcua-search-input {
            width: 100%;
            padding: 10px 16px;
            background: white;
            border: 1px solid #D1D5DB;
            border-radius: 8px;
            color: #2E3036;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
        }

        .opcua-search-input:focus {
            outline: none;
            border-color: #00A9E0;
            box-shadow: 0 0 0 2px rgba(0, 169, 224, 0.1);
        }

        .opcua-search-input::placeholder {
            color: #9CA3AF;
        }

        .opcua-tree-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }

        .opcua-tree-container::-webkit-scrollbar {
            width: 8px;
        }

        .opcua-tree-container::-webkit-scrollbar-track {
            background: #F3F4F6;
        }

        .opcua-tree-container::-webkit-scrollbar-thumb {
            background: #D1D5DB;
            border-radius: 4px;
        }

        .tree-node {
            margin-bottom: 4px;
        }

        .tree-node-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            user-select: none;
        }

        .tree-node-header:hover {
            background: #F3F4F6;
        }

        .tree-node-header.active {
            background: #DBEAFE;
        }

        .tree-chevron {
            font-size: 12px;
            color: #6B7280;
            transition: transform 0.2s;
            width: 16px;
            display: inline-block;
        }

        .tree-chevron.expanded {
            transform: rotate(90deg);
        }

        .tree-chevron.leaf {
            visibility: hidden;
        }

        .tree-icon {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .tree-label {
            flex: 1;
            font-size: 13px;
            color: #1F2937;
            font-weight: 500;
        }

        .tree-value {
            font-size: 12px;
            font-family: 'Monaco', 'Courier New', monospace;
            color: #00A9E0;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .tree-value.updated {
            color: #FF3621;
            transform: scale(1.1);
            animation: valueFlash 0.5s ease;
        }

        @keyframes valueFlash {
            0% {
                background: rgba(255, 54, 33, 0.2);
                border-radius: 4px;
                padding: 2px 4px;
            }
            50% {
                background: rgba(255, 54, 33, 0.4);
            }
            100% {
                background: transparent;
                padding: 0;
            }
        }

        .tree-unit {
            font-size: 11px;
            color: #6B7280;
            margin-left: 4px;
        }

        .tree-quality {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            margin-left: 8px;
        }

        .tree-quality.good {
            background: #D1FAE5;
            color: #065F46;
        }

        .tree-quality.uncertain {
            background: #FEF3C7;
            color: #92400E;
        }

        .tree-quality.bad {
            background: #FEE2E2;
            color: #991B1B;
        }

        .tree-quality.forced {
            background: #DBEAFE;
            color: #1E40AF;
        }

        .tree-children {
            margin-left: 24px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }

        .tree-children.expanded {
            max-height: 10000px;
            transition: max-height 0.5s ease-in;
        }

        .tree-properties {
            margin-left: 44px;
            margin-top: 8px;
            padding: 12px;
            background: #F9FAFB;
            border-radius: 6px;
            border-left: 3px solid #00A9E0;
        }

        .tree-property {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 12px;
        }

        .tree-property-name {
            color: #6B7280;
            font-weight: 500;
        }

        .tree-property-value {
            color: #1F2937;
            font-family: 'Monaco', 'Courier New', monospace;
            font-weight: 600;
        }

        /* Responsive */
        @media (max-width: 1200px) {
            .main-grid {
                grid-template-columns: 1fr;
            }

            .nlp-chat-panel, .opcua-browser-panel {
                width: 100%;
            }

            .chart-section {
                grid-template-columns: 1fr;
            }
        }

        /* Sensor Selection Styles */
        .btn-select-sensors {
            padding: 10px 20px;
            background: linear-gradient(135deg, #00A8E1 0%, #0088B8 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-select-sensors:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 168, 225, 0.3);
        }

        .sensor-summary {
            margin-top: 8px;
            padding: 8px 12px;
            background: #F3F4F6;
            border-radius: 6px;
            font-size: 12px;
            color: #6B7280;
        }

        /* Sensor Selector Modal */
        .sensor-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            z-index: 10000;
            justify-content: center;
            align-items: center;
        }

        .sensor-modal.active {
            display: flex;
        }

        .sensor-modal-content {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 1200px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        .sensor-modal-header {
            padding: 24px;
            border-bottom: 1px solid #E5E7EB;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .sensor-modal-title {
            font-size: 20px;
            font-weight: 700;
            color: #1B3139;
        }

        .sensor-modal-close {
            background: none;
            border: none;
            font-size: 24px;
            color: #6B7280;
            cursor: pointer;
            padding: 4px 8px;
            line-height: 1;
        }

        .sensor-modal-close:hover {
            color: #FF3621;
        }

        .sensor-modal-body {
            padding: 24px;
            overflow-y: auto;
            flex: 1;
        }

        .sensor-filter-section {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        .sensor-filter-group {
            background: #F9FAFB;
            padding: 16px;
            border-radius: 8px;
        }

        .sensor-filter-label {
            font-size: 12px;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            display: block;
        }

        .sensor-filter-options {
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 200px;
            overflow-y: auto;
        }

        .sensor-filter-option {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px;
            cursor: pointer;
        }

        .sensor-filter-option input[type="checkbox"] {
            width: 16px;
            height: 16px;
            cursor: pointer;
        }

        .sensor-filter-option label {
            font-size: 13px;
            color: #374151;
            cursor: pointer;
            flex: 1;
        }

        .sensor-list-section {
            background: #F9FAFB;
            border-radius: 8px;
            padding: 16px;
        }

        .sensor-list-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .sensor-list-title {
            font-size: 14px;
            font-weight: 600;
            color: #374151;
        }

        .sensor-list-actions {
            display: flex;
            gap: 12px;
        }

        .sensor-list-btn {
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .sensor-list-btn.select-all {
            background: #00A8E1;
            color: white;
        }

        .sensor-list-btn.select-all:hover {
            background: #0088B8;
        }

        .sensor-list-btn.clear-all {
            background: #E5E7EB;
            color: #374151;
        }

        .sensor-list-btn.clear-all:hover {
            background: #D1D5DB;
        }

        .sensor-items-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 8px;
            max-height: 300px;
            overflow-y: auto;
            padding: 8px;
            background: white;
            border-radius: 6px;
        }

        .sensor-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: #F9FAFB;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .sensor-item:hover {
            background: #F3F4F6;
        }

        .sensor-item input[type="checkbox"] {
            width: 16px;
            height: 16px;
            cursor: pointer;
        }

        .sensor-item-label {
            font-size: 12px;
            color: #374151;
            cursor: pointer;
            flex: 1;
        }

        .sensor-item-badge {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            background: #E5E7EB;
            color: #6B7280;
        }

        .sensor-modal-footer {
            padding: 24px;
            border-top: 1px solid #E5E7EB;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .sensor-selection-count {
            font-size: 14px;
            color: #6B7280;
        }

        .sensor-modal-actions {
            display: flex;
            gap: 12px;
        }

        .sensor-modal-btn {
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 600;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .sensor-modal-btn.cancel {
            background: #E5E7EB;
            color: #374151;
        }

        .sensor-modal-btn.cancel:hover {
            background: #D1D5DB;
        }

        .sensor-modal-btn.apply {
            background: #FF3621;
            color: white;
        }

        .sensor-modal-btn.apply:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 54, 33, 0.3);
        }

        /* Diagnostics panel styles */
        .diagnostics-panel {
            margin-top: 15px;
            padding: 15px;
            border-radius: 8px;
            min-height: 60px;
            font-size: 14px;
            line-height: 1.6;
        }

        .diagnostics-panel .success {
            background: #D1FAE5;
            color: #065F46;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #10B981;
        }

        .diagnostics-panel .error {
            background: #FEE2E2;
            color: #991B1B;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #EF4444;
        }

        .diagnostics-panel .info {
            background: #DBEAFE;
            color: #1E40AF;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #3B82F6;
        }

        .diagnostics-panel small {
            display: block;
            margin-top: 8px;
            font-size: 12px;
            opacity: 0.8;
        }

        /* ==================== TAB NAVIGATION ==================== */
        .tab-navigation {
            background: white;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            padding: 0;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            display: flex;
            overflow: hidden;
        }

        .tab-button {
            flex: 1;
            padding: 16px 24px;
            background: #F9FAFB;
            border: none;
            border-right: 1px solid #E3E5E8;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            color: #6B7280;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .tab-button:last-child {
            border-right: none;
        }

        .tab-button:hover {
            background: #F3F4F6;
            color: #2E3036;
        }

        .tab-button.active {
            background: white;
            color: #FF3621;
            border-bottom: 3px solid #FF3621;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* ==================== VENDOR MODE STYLES ==================== */
        .modes-container {
            display: grid;
            gap: 24px;
        }

        .mode-selector {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .mode-card {
            background: white;
            border: 2px solid #E3E5E8;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }

        .mode-card:hover {
            border-color: #00A9E0;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 169, 224, 0.15);
        }

        .mode-card.active {
            border-color: #FF3621;
            background: linear-gradient(135deg, rgba(255, 54, 33, 0.03) 0%, rgba(0, 169, 224, 0.03) 100%);
            box-shadow: 0 8px 24px rgba(255, 54, 33, 0.2);
        }

        .mode-card.disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background: #F9FAFB;
        }

        .mode-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .mode-card-title {
            font-size: 18px;
            font-weight: 700;
            color: #2E3036;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .mode-card-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .mode-card-badge.enabled {
            background: #D1FAE5;
            color: #065F46;
        }

        .mode-card-badge.disabled {
            background: #F3F4F6;
            color: #6B7280;
        }

        .mode-card-description {
            font-size: 13px;
            color: #6B7280;
            line-height: 1.6;
            margin-bottom: 12px;
        }

        .mode-card-stats {
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: #6B7280;
            padding-top: 12px;
            border-top: 1px solid #E3E5E8;
        }

        .mode-card-stat {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .mode-card-stat-label {
            text-transform: uppercase;
            font-weight: 600;
            font-size: 10px;
            letter-spacing: 0.5px;
        }

        .mode-card-stat-value {
            font-size: 16px;
            font-weight: 700;
            color: #2E3036;
        }

        .mode-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 48px;
            height: 26px;
            background: #D1D5DB;
            border-radius: 13px;
            cursor: pointer;
            transition: all 0.3s;
            border: none;
        }

        .mode-toggle.enabled {
            background: #10B981;
        }

        .mode-toggle::after {
            content: '';
            position: absolute;
            top: 3px;
            left: 3px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: all 0.3s;
        }

        .mode-toggle.enabled::after {
            transform: translateX(22px);
        }

        /* Protocol Toggle Buttons */
        .protocol-toggle-btn {
            padding: 6px 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s;
        }

        .protocol-toggle-btn.enabled {
            background: #10B981;
            color: white;
            border-color: #10B981;
        }

        .protocol-toggle-btn:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
        }

        .protocol-toggle-btn.enabled:hover {
            background: #0EA573;
        }

        /* Mode Panels */
        .mode-panel {
            display: none;
            background: white;
            border: 1px solid #E3E5E8;
            border-radius: 12px;
            padding: 0;
            overflow: hidden;
        }

        .mode-panel.active {
            display: block;
        }

        .mode-panel-header {
            background: linear-gradient(135deg, #FF3621 0%, #00A9E0 100%);
            padding: 24px;
            color: white;
        }

        .mode-panel-title {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .mode-panel-subtitle {
            font-size: 13px;
            opacity: 0.9;
        }

        .mode-panel-body {
            padding: 24px;
        }

        .mode-section {
            margin-bottom: 32px;
        }

        .mode-section-title {
            font-size: 14px;
            font-weight: 700;
            color: #2E3036;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding-bottom: 8px;
            border-bottom: 2px solid #E3E5E8;
        }

        .mode-metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .mode-metric-card {
            background: #F9FAFB;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            padding: 16px;
            transition: all 0.3s;
        }

        .mode-metric-card:hover {
            background: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .mode-metric-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: #6B7280;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .mode-metric-value {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #FF3621 0%, #00A9E0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .mode-metric-unit {
            font-size: 14px;
            color: #6B7280;
            margin-left: 4px;
        }

        .mode-metric-trend {
            font-size: 12px;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .mode-metric-trend.up {
            color: #10B981;
        }

        .mode-metric-trend.down {
            color: #EF4444;
        }

        /* Kepware Specific */
        .kepware-structure {
            display: grid;
            gap: 16px;
        }

        .kepware-channel {
            background: white;
            border: 2px solid #00A9E0;
            border-radius: 8px;
            padding: 16px;
        }

        .kepware-channel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid #E3E5E8;
        }

        .kepware-channel-name {
            font-size: 16px;
            font-weight: 700;
            color: #00A9E0;
        }

        .kepware-device {
            background: #F9FAFB;
            border: 1px solid #E3E5E8;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 8px;
        }

        .kepware-device-header {
            font-size: 14px;
            font-weight: 600;
            color: #2E3036;
            margin-bottom: 8px;
        }

        .kepware-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .kepware-tag {
            background: white;
            border: 1px solid #D1D5DB;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 12px;
            color: #6B7280;
            font-family: 'Monaco', 'Courier New', monospace;
        }

        /* Sparkplug B Specific */
        .sparkplug-edge-nodes {
            display: grid;
            gap: 16px;
        }

        .sparkplug-node {
            background: white;
            border: 2px solid #8B5CF6;
            border-radius: 8px;
            padding: 16px;
        }

        .sparkplug-node-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .sparkplug-node-name {
            font-size: 16px;
            font-weight: 700;
            color: #8B5CF6;
        }

        .sparkplug-status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }

        .sparkplug-status-badge.online {
            background: #D1FAE5;
            color: #065F46;
        }

        .sparkplug-status-badge.offline {
            background: #FEE2E2;
            color: #991B1B;
        }

        .sparkplug-device-list {
            display: grid;
            gap: 8px;
        }

        .sparkplug-device {
            background: #F9FAFB;
            border: 1px solid #E3E5E8;
            border-radius: 6px;
            padding: 10px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .sparkplug-device-name {
            font-size: 13px;
            font-weight: 600;
            color: #2E3036;
        }

        .sparkplug-seq {
            font-size: 11px;
            color: #6B7280;
            font-family: 'Monaco', 'Courier New', monospace;
        }

        /* Honeywell Specific */
        .honeywell-modules {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
        }

        .honeywell-module {
            background: white;
            border: 2px solid #F59E0B;
            border-radius: 8px;
            padding: 16px;
        }

        .honeywell-module-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid #E3E5E8;
        }

        .honeywell-module-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 14px;
        }

        .honeywell-module-name {
            font-size: 16px;
            font-weight: 700;
            color: #2E3036;
        }

        .honeywell-points {
            display: grid;
            gap: 8px;
        }

        .honeywell-point {
            background: #F9FAFB;
            border: 1px solid #E3E5E8;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-family: 'Monaco', 'Courier New', monospace;
            color: #6B7280;
        }

        /* Message Inspector */
        .message-inspector {
            background: white;
            border: 1px solid #E3E5E8;
            border-radius: 8px;
            overflow: hidden;
        }

        .message-inspector-header {
            background: #F9FAFB;
            padding: 16px 20px;
            border-bottom: 1px solid #E3E5E8;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .message-inspector-title {
            font-size: 16px;
            font-weight: 700;
            color: #2E3036;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .message-inspector-controls {
            display: flex;
            gap: 8px;
        }

        .message-inspector-body {
            max-height: 500px;
            overflow-y: auto;
            background: #1E1E1E;
        }

        .message-item {
            padding: 12px 20px;
            border-bottom: 1px solid #333;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
        }

        .message-item:hover {
            background: #252525;
        }

        .message-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .message-timestamp {
            color: #00A9E0;
            font-size: 11px;
        }

        .message-topic {
            color: #8B5CF6;
            font-size: 11px;
        }

        .message-mode {
            color: #F59E0B;
            font-size: 10px;
            background: rgba(245, 158, 11, 0.2);
            padding: 2px 8px;
            border-radius: 4px;
        }

        .message-protocol {
            font-size: 10px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 8px;
        }

        .protocol-mqtt {
            color: #10B981;
            background: rgba(16, 185, 129, 0.2);
        }

        .protocol-opcua {
            color: #3B82F6;
            background: rgba(59, 130, 246, 0.2);
        }

        .protocol-modbus {
            color: #8B5CF6;
            background: rgba(139, 92, 246, 0.2);
        }

        .message-payload {
            color: #D4D4D4;
            white-space: pre-wrap;
            word-break: break-all;
            line-height: 1.5;
        }

        .message-key {
            color: #9CDCFE;
        }

        .message-value {
            color: #CE9178;
        }

        .message-number {
            color: #B5CEA8;
        }

        /* Quality Distribution Chart */
        .quality-distribution {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .quality-bar {
            flex: 1;
            height: 32px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 600;
            color: white;
            transition: all 0.3s;
            cursor: pointer;
        }

        .quality-bar:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        .quality-bar.good {
            background: #10B981;
        }

        .quality-bar.uncertain {
            background: #F59E0B;
        }

        .quality-bar.bad {
            background: #EF4444;
        }

        /* Lifecycle Events Timeline */
        .lifecycle-timeline {
            position: relative;
            padding-left: 24px;
        }

        .lifecycle-timeline::before {
            content: '';
            position: absolute;
            left: 8px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #E3E5E8;
        }

        .lifecycle-event {
            position: relative;
            padding: 12px;
            background: #F9FAFB;
            border: 1px solid #E3E5E8;
            border-radius: 6px;
            margin-bottom: 12px;
        }

        .lifecycle-event::before {
            content: '';
            position: absolute;
            left: -20px;
            top: 50%;
            transform: translateY(-50%);
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 0 2px #E3E5E8;
        }

        .lifecycle-event.birth::before {
            background: #10B981;
        }

        .lifecycle-event.data::before {
            background: #00A9E0;
        }

        .lifecycle-event.death::before {
            background: #EF4444;
        }

        .lifecycle-event-type {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .lifecycle-event.birth .lifecycle-event-type {
            color: #10B981;
        }

        .lifecycle-event.data .lifecycle-event-type {
            color: #00A9E0;
        }

        .lifecycle-event.death .lifecycle-event-type {
            color: #EF4444;
        }

        .lifecycle-event-details {
            font-size: 12px;
            color: #6B7280;
            font-family: 'Monaco', 'Courier New', monospace;
        }

        /* Responsive Design */
        @media (max-width: 1024px) {
            .mode-selector {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            }

            .mode-metrics-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }

            .honeywell-modules {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 768px) {
            .tab-button {
                font-size: 13px;
                padding: 12px 16px;
            }

            .mode-panel-title {
                font-size: 16px;
            }

            .mode-card {
                padding: 16px;
            }
        }
    </style>
</head>"""


def get_body_html() -> str:
    """Return the HTML body structure."""
    return """<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo-section">
                <div class="databricks-logo">D</div>
                <div style="flex: 1;">
                    <h1>OT Data Simulator</h1>
                    <div class="subtitle">Real-Time Visualization • Natural Language AI • W3C WoT Discovery • ZeroBus Streaming</div>
                </div>
                <div style="display: flex; gap: 12px;">
                    <a href="/wot/browser" style="padding: 12px 24px; background: linear-gradient(135deg, #00A9E0 0%, #0080B3 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 12px rgba(0, 169, 224, 0.3); transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(0, 169, 224, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(0, 169, 224, 0.3)'">
                        
                        <span>WoT Browser</span>
                        <span style="font-size: 10px; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px;">379 sensors</span>
                    </a>
                    <button onclick="toggleOPCUABrowser()" style="padding: 12px 24px; background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%); color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3); transition: all 0.3s; cursor: pointer;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(139, 92, 246, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(139, 92, 246, 0.3)'">
                        
                        <span>Browse OPC-UA</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-navigation">
            <button class="tab-button active" onclick="switchTab('overview')" id="tab-overview">
                Overview & Protocols
            </button>
            <button class="tab-button" onclick="switchTab('modes')" id="tab-modes">
                Vendor Modes
            </button>
            <button class="tab-button" onclick="switchTab('connections')" id="tab-connections">
                Connection Info
            </button>
        </div>

        <!-- Overview Tab Content -->
        <div class="tab-content active" id="content-overview">

        <!-- Protocol Control (Full Width) -->
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-title">Protocol Simulators</div>
            <div class="protocol-selector">
                <!-- OPC-UA Protocol -->
                <div class="protocol-item">
                    <div class="protocol-header">
                        <div class="protocol-badge" id="status-opcua"></div>
                        <span class="protocol-name">OPC-UA</span>
                        <div class="protocol-endpoint">
                            opc.tcp://0.0.0.0:4840/ot-simulator/server/
                        </div>
                        <div class="protocol-controls">
                            <button class="btn btn-start" id="start-opcua" onclick="startProtocol('opcua')">Start</button>
                            <button class="btn btn-stop" id="stop-opcua" onclick="stopProtocol('opcua')">Stop</button>
                            <button class="config-toggle" onclick="toggleConfig('opcua')">
                                <span>Zero-Bus Config</span>
                                <span class="config-toggle-icon" id="toggle-opcua">▼</span>
                            </button>
                        </div>
                    </div>
                    <div class="protocol-config-panel" id="config-opcua">
                        <div class="config-row">
                            <div class="config-field">
                                <label class="config-label">Workspace Host</label>
                                <input type="text" class="config-input" id="opcua-workspace"
                                       placeholder="https://your-workspace.cloud.databricks.com" />
                            </div>
                            <div class="config-field">
                                <label class="config-label">Zero-Bus Endpoint</label>
                                <input type="text" class="config-input" id="opcua-zerobus"
                                       placeholder="xxxxx.zerobus.region.cloud.databricks.com" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field">
                                <label class="config-label">OAuth Client ID</label>
                                <input type="text" class="config-input" id="opcua-client-id"
                                       placeholder="Enter OAuth Client ID" />
                            </div>
                            <div class="config-field">
                                <label class="config-label">OAuth Client Secret</label>
                                <input type="password" class="config-input" id="opcua-client-secret"
                                       placeholder="Enter OAuth Client Secret" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field" style="flex: 2;">
                                <label class="config-label">Target Table (catalog.schema.table)</label>
                                <input type="text" class="config-input" id="opcua-target"
                                       placeholder="opcua.scada_data.opcua_events_bronze" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field" style="flex: 2;">
                                <label class="config-label">Select Sensors/Tags</label>
                                <button class="btn-select-sensors" onclick="openSensorSelector('opcua')">Choose Sensors</button>
                                <div id="opcua-sensor-summary" class="sensor-summary">All sensors selected (379 total)</div>
                            </div>
                        </div>
                        <div class="config-actions">
                            <button class="btn-save" onclick="saveZeroBusConfig('opcua')">Save Configuration</button>
                            <button class="btn-test" onclick="testZeroBusConnection('opcua')">Test Connection</button>
                            <button class="btn-start-zerobus" id="opcua-zerobus-btn" onclick="startZeroBusService('opcua')">▶️ Start Streaming</button>
                        </div>
                        <div id="opcua-diagnostics" class="diagnostics-panel"></div>

                        <!-- Connected Clients Section -->
                        <div id="opcua-clients-section" style="margin-top: 16px; padding: 16px; background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px;">
                            <div style="font-size: 14px; font-weight: 600; color: #1F2937; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                                <span>Connected OPC UA Clients</span>
                                <span id="opcua-client-count" style="font-size: 12px; font-weight: 500; color: #6B7280; background: white; padding: 4px 12px; border-radius: 12px;">0 clients</span>
                            </div>
                            <div id="opcua-clients-list" style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden;">
                                <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                                    Loading client information...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- MQTT Protocol -->
                <div class="protocol-item">
                    <div class="protocol-header">
                        <div class="protocol-badge" id="status-mqtt"></div>
                        <span class="protocol-name">MQTT</span>
                        <div class="protocol-endpoint">
                            broker: localhost:1883
                        </div>
                        <div class="protocol-controls">
                            <button class="btn btn-start" id="start-mqtt" onclick="startProtocol('mqtt')">Start</button>
                            <button class="btn btn-stop" id="stop-mqtt" onclick="stopProtocol('mqtt')">Stop</button>
                            <button class="config-toggle" onclick="toggleConfig('mqtt')">
                                <span>Zero-Bus Config</span>
                                <span class="config-toggle-icon" id="toggle-mqtt">▼</span>
                            </button>
                        </div>
                    </div>
                    <div class="protocol-config-panel" id="config-mqtt">
                        <div class="config-row">
                            <div class="config-field">
                                <label class="config-label">Workspace Host</label>
                                <input type="text" class="config-input" id="mqtt-workspace"
                                       placeholder="https://your-workspace.cloud.databricks.com" />
                            </div>
                            <div class="config-field">
                                <label class="config-label">Zero-Bus Endpoint</label>
                                <input type="text" class="config-input" id="mqtt-zerobus"
                                       placeholder="xxxxx.zerobus.region.cloud.databricks.com" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field">
                                <label class="config-label">OAuth Client ID</label>
                                <input type="text" class="config-input" id="mqtt-client-id"
                                       placeholder="Enter OAuth Client ID" />
                            </div>
                            <div class="config-field">
                                <label class="config-label">OAuth Client Secret</label>
                                <input type="password" class="config-input" id="mqtt-client-secret"
                                       placeholder="Enter OAuth Client Secret" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field" style="flex: 2;">
                                <label class="config-label">Target Table (catalog.schema.table)</label>
                                <input type="text" class="config-input" id="mqtt-target"
                                       placeholder="mqtt.scada_data.mqtt_events_bronze" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field" style="flex: 2;">
                                <label class="config-label">Select Sensors/Tags</label>
                                <button class="btn-select-sensors" onclick="openSensorSelector('mqtt')">️ Choose Sensors</button>
                                <div id="mqtt-sensor-summary" class="sensor-summary">All sensors selected (379 total)</div>
                            </div>
                        </div>
                        <div class="config-actions">
                            <button class="btn-save" onclick="saveZeroBusConfig('mqtt')">Save Configuration</button>
                            <button class="btn-test" onclick="testZeroBusConnection('mqtt')">Test Connection</button>
                            <button class="btn-start-zerobus" id="mqtt-zerobus-btn" onclick="startZeroBusService('mqtt')">▶️ Start Streaming</button>
                        </div>
                        <div id="mqtt-diagnostics" class="diagnostics-panel"></div>

                        <!-- MQTT Subscribers Section -->
                        <div id="mqtt-subscribers-section" style="margin-top: 16px; padding: 16px; background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px;">
                            <div style="font-size: 14px; font-weight: 600; color: #1F2937; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                                <span>MQTT Subscribers</span>
                                <span id="mqtt-subscriber-count" style="font-size: 12px; font-weight: 500; color: #6B7280; background: white; padding: 4px 12px; border-radius: 12px;">N/A</span>
                            </div>
                            <div id="mqtt-subscribers-list" style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden;">
                                <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                                    Loading subscriber information...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Modbus Protocol -->
                <div class="protocol-item">
                    <div class="protocol-header">
                        <div class="protocol-badge" id="status-modbus"></div>
                        <span class="protocol-name">Modbus</span>
                        <div class="protocol-endpoint">
                            tcp://0.0.0.0:5020
                        </div>
                        <div class="protocol-controls">
                            <button class="btn btn-start" id="start-modbus" onclick="startProtocol('modbus')">Start</button>
                            <button class="btn btn-stop" id="stop-modbus" onclick="stopProtocol('modbus')">Stop</button>
                            <button class="config-toggle" onclick="toggleConfig('modbus')">
                                <span>Zero-Bus Config</span>
                                <span class="config-toggle-icon" id="toggle-modbus">▼</span>
                            </button>
                        </div>
                    </div>
                    <div class="protocol-config-panel" id="config-modbus">
                        <div class="config-row">
                            <div class="config-field">
                                <label class="config-label">Workspace Host</label>
                                <input type="text" class="config-input" id="modbus-workspace"
                                       placeholder="https://your-workspace.cloud.databricks.com" />
                            </div>
                            <div class="config-field">
                                <label class="config-label">Zero-Bus Endpoint</label>
                                <input type="text" class="config-input" id="modbus-zerobus"
                                       placeholder="xxxxx.zerobus.region.cloud.databricks.com" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field">
                                <label class="config-label">OAuth Client ID</label>
                                <input type="text" class="config-input" id="modbus-client-id"
                                       placeholder="Enter OAuth Client ID" />
                            </div>
                            <div class="config-field">
                                <label class="config-label">OAuth Client Secret</label>
                                <input type="password" class="config-input" id="modbus-client-secret"
                                       placeholder="Enter OAuth Client Secret" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field" style="flex: 2;">
                                <label class="config-label">Target Table (catalog.schema.table)</label>
                                <input type="text" class="config-input" id="modbus-target"
                                       placeholder="modbus.scada_data.modbus_events_bronze" />
                            </div>
                        </div>
                        <div class="config-row">
                            <div class="config-field" style="flex: 2;">
                                <label class="config-label">Select Sensors/Tags</label>
                                <button class="btn-select-sensors" onclick="openSensorSelector('modbus')">️ Choose Sensors</button>
                                <div id="modbus-sensor-summary" class="sensor-summary">All sensors selected (379 total)</div>
                            </div>
                        </div>
                        <div class="config-actions">
                            <button class="btn-save" onclick="saveZeroBusConfig('modbus')">Save Configuration</button>
                            <button class="btn-test" onclick="testZeroBusConnection('modbus')">Test Connection</button>
                            <button class="btn-start-zerobus" id="modbus-zerobus-btn" onclick="startZeroBusService('modbus')">▶️ Start Streaming</button>
                        </div>
                        <div id="modbus-diagnostics" class="diagnostics-panel"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Training Platform -->
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-title" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between;" onclick="toggleTrainingPanel()">
                <span>Training Platform</span>
                <span id="training-toggle-icon" style="transition: transform 0.3s;">▼</span>
            </div>
            <div class="training-panel" id="training-panel" style="display: none; margin-top: 20px;">
""" + get_training_ui_html() + """
            </div>
        </div>

        <!-- Main Grid -->
        <div class="main-grid">
            <!-- Sidebar -->
            <div class="sidebar">
                <!-- Sensor Browser -->
                <div class="card">
                    <div class="card-title">Add Sensors to Chart</div>
                    <div class="sensor-browser" id="sensor-browser">
                        <!-- Populated dynamically -->
                    </div>
                </div>
            </div>

            <!-- Raw Data Stream Section -->
            <div class="card" style="margin-bottom: 24px;">
                <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>Raw Data Stream</span>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <select id="raw-protocol-filter" class="config-input" style="width: auto; padding: 6px 12px; font-size: 13px;">
                            <option value="">All Protocols</option>
                            <option value="opcua">OPC-UA</option>
                            <option value="mqtt">MQTT</option>
                            <option value="modbus">Modbus</option>
                        </select>
                        <select id="raw-industry-filter" class="config-input" style="width: auto; padding: 6px 12px; font-size: 13px;">
                            <option value="">All Industries</option>
                            <option value="mining">Mining</option>
                            <option value="oil_gas">Oil & Gas</option>
                            <option value="utilities">Utilities</option>
                            <option value="manufacturing">Manufacturing</option>
                        </select>
                        <button class="btn btn-start" id="raw-stream-toggle" onclick="toggleRawStream()">Start Stream</button>
                        <button class="btn-test" onclick="clearRawStream()">Clear</button>
                    </div>
                </div>
                <div id="raw-stream-container" style="max-height: 500px; overflow-y: auto; overflow-x: hidden; font-family: 'Monaco', 'Courier New', monospace; font-size: 12px; background: #1E1E1E; color: #D4D4D4; padding: 16px; border-radius: 6px; margin-top: 16px;">
                    <div id="raw-stream-content" style="white-space: pre-wrap; word-wrap: break-word; width: 100%;">
                        <div style="color: #6B7280; text-align: center; padding: 32px;">
                            Click "Start Stream" to begin viewing live raw sensor data
                        </div>
                    </div>
                </div>
                <div style="margin-top: 12px; padding: 12px; background: #F9FAFB; border-radius: 6px; font-size: 13px; color: #6B7280;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Records shown: <strong id="raw-record-count">0</strong></span>
                        <span>Update rate: 2 seconds</span>
                        <span>Auto-scroll: <strong>Enabled</strong></span>
                    </div>
                </div>
            </div>

            <!-- Chart Section -->
            <div class="chart-section" id="chart-section">
                <!-- Charts added dynamically -->
            </div>
        </div>
    </div>

    <!-- Operations AI Assistant Button -->
    <button class="nlp-chat-button" id="nlp-chat-toggle">
        Operations AI Assistant
    </button>

    <!-- Chat Panel -->
    <div class="nlp-chat-panel hidden" id="nlp-chat-panel">
        <div class="chat-header">
            <h3>Operations AI Assistant</h3>
            <button class="chat-close" id="chat-close">×</button>
        </div>

        <div class="chat-messages" id="chat-messages">
            <div class="message agent">
                <div class="message-avatar"></div>
                <div class="message-content">
                    <div class="message-bubble">
                        <strong>Operations AI Assistant</strong><br>
                        I understand commands in plain English. Here are examples:<br><br>

                        <strong>Protocol Control:</strong><br>
                        • "Start opcua" or "Start the OPC-UA simulator"<br>
                        • "Stop mqtt" or "Stop MQTT publishing"<br>
                        • "What's the status of all simulators?"<br><br>

                        <strong>Sensor Information:</strong><br>
                        • "Show me all sensors in mining"<br>
                        • "List utilities sensors"<br>
                        • "What sensors are available?"<br><br>

                        <strong>Fault Injection:</strong><br>
                        • "Inject fault into mining/crusher_1_motor_power for 60 seconds"<br>
                        • "Break the conveyor belt sensor for 30 seconds"<br><br>

                        <strong>General Questions:</strong><br>
                        • "How many sensors are running?"<br>
                        • "Show me the manufacturing sensors"
                    </div>
                </div>
            </div>
        </div>

        <div class="chat-input-container">
            <input
                type="text"
                class="chat-input"
                id="chat-input"
                placeholder="Type your command... (e.g., 'start opcua')"
                autocomplete="off"
            />
            <button class="chat-send" id="chat-send">Send</button>
        </div>
    </div>

    <!-- OPC-UA Browser Panel -->
    <div class="opcua-browser-panel hidden" id="opcua-browser-panel">
        <div class="opcua-browser-header">
            <h3>OPC-UA Node Hierarchy</h3>
            <button class="opcua-browser-close" id="opcua-browser-close">×</button>
        </div>

        <div class="opcua-search-container">
            <input
                type="text"
                class="opcua-search-input"
                id="opcua-search-input"
                placeholder="Search nodes... (e.g., 'crusher', 'temperature')"
                autocomplete="off"
            />
        </div>

        <div class="opcua-tree-container" id="opcua-tree-container">
            <!-- Tree will be populated dynamically -->
            <div style="text-align: center; padding: 40px; color: #6B7280;">
                Loading OPC-UA hierarchy...
            </div>
        </div>
    </div>

    <!-- Sensor Selector Modal -->
    <div class="sensor-modal" id="sensor-modal">
        <div class="sensor-modal-content">
            <div class="sensor-modal-header">
                <h2 class="sensor-modal-title">Select Sensors/Tags for <span id="sensor-modal-protocol">OPC-UA</span></h2>
                <button class="sensor-modal-close" onclick="closeSensorSelector()">&times;</button>
            </div>

            <div class="sensor-modal-body">
                <!-- Filter Section -->
                <div class="sensor-filter-section">
                    <!-- Industry Filter -->
                    <div class="sensor-filter-group">
                        <label class="sensor-filter-label">Filter by Industry</label>
                        <div class="sensor-filter-options" id="industry-filter-options">
                            <!-- Will be populated dynamically -->
                        </div>
                    </div>

                    <!-- Sensor Type Filter -->
                    <div class="sensor-filter-group">
                        <label class="sensor-filter-label">Filter by Sensor Type</label>
                        <div class="sensor-filter-options" id="sensor-type-filter-options">
                            <!-- Will be populated dynamically -->
                        </div>
                    </div>

                    <!-- PLC/System Filter -->
                    <div class="sensor-filter-group">
                        <label class="sensor-filter-label">Filter by PLC/System</label>
                        <div class="sensor-filter-options" id="plc-filter-options">
                            <!-- Will be populated dynamically -->
                        </div>
                    </div>
                </div>

                <!-- Sensor List Section -->
                <div class="sensor-list-section">
                    <div class="sensor-list-header">
                        <div class="sensor-list-title">Available Sensors (<span id="filtered-sensor-count">379</span>)</div>
                        <div class="sensor-list-actions">
                            <button class="sensor-list-btn select-all" onclick="selectAllFilteredSensors()">Select All Filtered</button>
                            <button class="sensor-list-btn clear-all" onclick="clearAllSensors()">Clear All</button>
                        </div>
                    </div>
                    <div class="sensor-items-grid" id="sensor-items-grid">
                        <!-- Will be populated dynamically -->
                    </div>
                </div>
            </div>

            <div class="sensor-modal-footer">
                <div class="sensor-selection-count">
                    <strong><span id="selected-sensor-count">379</span></strong> sensors selected
                </div>
                <div class="sensor-modal-actions">
                    <button class="sensor-modal-btn cancel" onclick="closeSensorSelector()">Cancel</button>
                    <button class="sensor-modal-btn apply" onclick="applySensorSelection()">Apply Selection</button>
                </div>
            </div>
        </div>
    </div>

        </div>
        <!-- End Overview Tab -->

        <!-- Vendor Modes Tab Content -->
        <div class="tab-content" id="content-modes">
            <div class="modes-container">

                <!-- Mode Selection Cards -->
                <div class="mode-selector">
                    <!-- Generic Mode Card -->
                    <div class="mode-card" id="mode-card-generic" onclick="selectMode('generic')">
                        <button class="mode-toggle" id="toggle-generic" onclick="event.stopPropagation(); toggleMode('generic')"></button>
                        <div class="mode-card-header">
                            <div class="mode-card-title">
                                Generic Mode
                            </div>
                        </div>
                        <div class="mode-card-badge disabled" id="badge-generic">Disabled</div>
                        <div class="mode-card-description">
                            Standard OT data format with simple industry/sensor structure. Compatible with all protocols and perfect for testing.
                        </div>
                        <div class="mode-card-stats">
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Messages</div>
                                <div class="mode-card-stat-value" id="stat-generic-messages">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Sensors</div>
                                <div class="mode-card-stat-value" id="stat-generic-sensors">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Quality</div>
                                <div class="mode-card-stat-value" id="stat-generic-quality">—</div>
                            </div>
                        </div>
                    </div>

                    <!-- Kepware Mode Card -->
                    <div class="mode-card" id="mode-card-kepware" onclick="selectMode('kepware')">
                        <button class="mode-toggle" id="toggle-kepware" onclick="event.stopPropagation(); toggleMode('kepware')"></button>
                        <div class="mode-card-header">
                            <div class="mode-card-title">
                                Kepware KEPServerEX
                            </div>
                        </div>
                        <div class="mode-card-badge disabled" id="badge-kepware">Disabled</div>
                        <div class="mode-card-description">
                            Channel.Device.Tag hierarchy with IoT Gateway JSON format. World's leading OPC server (100K+ installations).
                        </div>
                        <div class="mode-card-stats">
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Channels</div>
                                <div class="mode-card-stat-value" id="stat-kepware-channels">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Devices</div>
                                <div class="mode-card-stat-value" id="stat-kepware-devices">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Tags</div>
                                <div class="mode-card-stat-value" id="stat-kepware-tags">0</div>
                            </div>
                        </div>
                        <div class="protocol-toggles" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
                            <div style="display: flex; gap: 10px; justify-content: center;">
                                <button class="protocol-toggle-btn" id="toggle-kepware-opcua" onclick="event.stopPropagation(); toggleProtocol('kepware', 'opcua')" title="Toggle OPC UA">
                                    OPC UA
                                </button>
                                <button class="protocol-toggle-btn" id="toggle-kepware-mqtt" onclick="event.stopPropagation(); toggleProtocol('kepware', 'mqtt')" title="Toggle MQTT">
                                    MQTT
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Sparkplug B Mode Card -->
                    <div class="mode-card" id="mode-card-sparkplug_b" onclick="selectMode('sparkplug_b')">
                        <button class="mode-toggle" id="toggle-sparkplug_b" onclick="event.stopPropagation(); toggleMode('sparkplug_b')"></button>
                        <div class="mode-card-header">
                            <div class="mode-card-title">
                                Sparkplug B
                            </div>
                        </div>
                        <div class="mode-card-badge disabled" id="badge-sparkplug_b">Disabled</div>
                        <div class="mode-card-description">
                            Industrial IoT protocol with BIRTH/DATA/DEATH lifecycle, sequence numbers, and state-aware architecture.
                        </div>
                        <div class="mode-card-stats">
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Edge Nodes</div>
                                <div class="mode-card-stat-value" id="stat-sparkplug-nodes">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Devices</div>
                                <div class="mode-card-stat-value" id="stat-sparkplug-devices">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">bdSeq</div>
                                <div class="mode-card-stat-value" id="stat-sparkplug-seq">0</div>
                            </div>
                        </div>
                    </div>

                    <!-- Honeywell Mode Card -->
                    <div class="mode-card" id="mode-card-honeywell" onclick="selectMode('honeywell')">
                        <button class="mode-toggle" id="toggle-honeywell" onclick="event.stopPropagation(); toggleMode('honeywell')"></button>
                        <div class="mode-card-header">
                            <div class="mode-card-title">
                                ️ Honeywell Experion PKS
                            </div>
                        </div>
                        <div class="mode-card-badge disabled" id="badge-honeywell">Disabled</div>
                        <div class="mode-card-description">
                            Composite point structure with .PV/.SP/.OP attributes for process control. FIM/ACE/LCN module organization.
                        </div>
                        <div class="mode-card-stats">
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Modules</div>
                                <div class="mode-card-stat-value" id="stat-honeywell-modules">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Points</div>
                                <div class="mode-card-stat-value" id="stat-honeywell-points">0</div>
                            </div>
                            <div class="mode-card-stat">
                                <div class="mode-card-stat-label">Controllers</div>
                                <div class="mode-card-stat-value" id="stat-honeywell-controllers">0</div>
                            </div>
                        </div>
                        <div class="protocol-toggles" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
                            <div style="display: flex; gap: 10px; justify-content: center;">
                                <button class="protocol-toggle-btn" id="toggle-honeywell-opcua" onclick="event.stopPropagation(); toggleProtocol('honeywell', 'opcua')" title="Toggle OPC UA">
                                    OPC UA
                                </button>
                                <button class="protocol-toggle-btn" id="toggle-honeywell-mqtt" onclick="event.stopPropagation(); toggleProtocol('honeywell', 'mqtt')" title="Toggle MQTT">
                                    MQTT
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Mode Detail Panels -->

                <!-- Generic Mode Panel -->
                <div class="mode-panel" id="panel-generic">
                    <div class="mode-panel-header">
                        <div class="mode-panel-title">Generic Mode</div>
                        <div class="mode-panel-subtitle">Standard OT data format • Simple structure • Universal compatibility</div>
                    </div>
                    <div class="mode-panel-body">
                        <div class="mode-section">
                            <div class="mode-section-title">Real-Time Metrics</div>
                            <div class="mode-metrics-grid">
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Messages/Sec</div>
                                    <div class="mode-metric-value" id="generic-msg-rate">0</div>
                                    <div class="mode-metric-trend up" id="generic-msg-trend">
                                        <span>↑</span>
                                        <span>0%</span>
                                    </div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Total Sensors</div>
                                    <div class="mode-metric-value" id="generic-total-sensors">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Avg Payload Size</div>
                                    <div class="mode-metric-value" id="generic-payload-size">0</div>
                                    <span class="mode-metric-unit">bytes</span>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Quality Good %</div>
                                    <div class="mode-metric-value" id="generic-quality-pct">0</div>
                                    <span class="mode-metric-unit">%</span>
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">Message Format</div>
                            <div style="background: #1E1E1E; color: #D4D4D4; padding: 16px; border-radius: 8px; font-family: 'Monaco', 'Courier New', monospace; font-size: 12px; line-height: 1.6;">
{
  <span style="color: #9CDCFE;">"sensor"</span>: <span style="color: #CE9178;">"crusher_1_motor_power"</span>,
  <span style="color: #9CDCFE;">"industry"</span>: <span style="color: #CE9178;">"mining"</span>,
  <span style="color: #9CDCFE;">"value"</span>: <span style="color: #B5CEA8;">850.3</span>,
  <span style="color: #9CDCFE;">"unit"</span>: <span style="color: #CE9178;">"kW"</span>,
  <span style="color: #9CDCFE;">"quality"</span>: <span style="color: #CE9178;">"GOOD"</span>,
  <span style="color: #9CDCFE;">"timestamp"</span>: <span style="color: #B5CEA8;">1738851825.123</span>
}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Kepware Mode Panel -->
                <div class="mode-panel" id="panel-kepware">
                    <div class="mode-panel-header">
                        <div class="mode-panel-title">Kepware KEPServerEX Mode</div>
                        <div class="mode-panel-subtitle">Channel.Device.Tag hierarchy • IoT Gateway JSON • 100K+ global installations</div>
                    </div>
                    <div class="mode-panel-body">
                        <div class="mode-section">
                            <div class="mode-section-title">Performance Metrics</div>
                            <div class="mode-metrics-grid">
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Messages/Sec</div>
                                    <div class="mode-metric-value" id="kepware-msg-rate">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Active Channels</div>
                                    <div class="mode-metric-value" id="kepware-channels">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Active Devices</div>
                                    <div class="mode-metric-value" id="kepware-devices">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Total Tags</div>
                                    <div class="mode-metric-value" id="kepware-tags">0</div>
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">️ Channel/Device/Tag Structure</div>
                            <div id="kepware-structure" class="kepware-structure">
                                <!-- Dynamically populated -->
                                <div style="text-align: center; padding: 40px; color: #6B7280;">
                                    No channels configured. Enable Kepware mode to see structure.
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">IoT Gateway Message Format</div>
                            <div style="background: #1E1E1E; color: #D4D4D4; padding: 16px; border-radius: 8px; font-family: 'Monaco', 'Courier New', monospace; font-size: 12px; line-height: 1.6;">
{
  <span style="color: #9CDCFE;">"timestamp"</span>: <span style="color: #B5CEA8;">1738851825000</span>,
  <span style="color: #9CDCFE;">"values"</span>: [{
    <span style="color: #9CDCFE;">"id"</span>: <span style="color: #CE9178;">"Siemens_S7_Crushing.Crusher_01.MotorPower"</span>,
    <span style="color: #9CDCFE;">"v"</span>: <span style="color: #B5CEA8;">850.3</span>,
    <span style="color: #9CDCFE;">"q"</span>: <span style="color: #569CD6;">true</span>,
    <span style="color: #9CDCFE;">"t"</span>: <span style="color: #B5CEA8;">1738851825000</span>
  }]
}
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">Quality Distribution</div>
                            <div class="quality-distribution">
                                <div class="quality-bar good" style="flex: 0.85;">
                                    <span id="kepware-quality-good">85%</span> GOOD
                                </div>
                                <div class="quality-bar uncertain" style="flex: 0.10;">
                                    <span id="kepware-quality-uncertain">10%</span> UNCERTAIN
                                </div>
                                <div class="quality-bar bad" style="flex: 0.05;">
                                    <span id="kepware-quality-bad">5%</span> BAD
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Sparkplug B Mode Panel -->
                <div class="mode-panel" id="panel-sparkplug_b">
                    <div class="mode-panel-header">
                        <div class="mode-panel-title">Sparkplug B Mode</div>
                        <div class="mode-panel-subtitle">Industrial IoT Protocol • State-Aware • BIRTH/DATA/DEATH Lifecycle</div>
                    </div>
                    <div class="mode-panel-body">
                        <div class="mode-section">
                            <div class="mode-section-title">Protocol Metrics</div>
                            <div class="mode-metrics-grid">
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Messages/Sec</div>
                                    <div class="mode-metric-value" id="sparkplug-msg-rate">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Edge Nodes Online</div>
                                    <div class="mode-metric-value" id="sparkplug-nodes-online">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">bdSeq Number</div>
                                    <div class="mode-metric-value" id="sparkplug-bdseq">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">BIRTH Messages</div>
                                    <div class="mode-metric-value" id="sparkplug-births">0</div>
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">Edge Node Status</div>
                            <div id="sparkplug-nodes" class="sparkplug-edge-nodes">
                                <!-- Dynamically populated -->
                                <div style="text-align: center; padding: 40px; color: #6B7280;">
                                    No edge nodes configured. Enable Sparkplug B mode to see nodes.
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">Lifecycle Events Timeline</div>
                            <div id="sparkplug-timeline" class="lifecycle-timeline">
                                <!-- Dynamically populated -->
                                <div style="text-align: center; padding: 40px; color: #6B7280;">
                                    No lifecycle events yet.
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">Sparkplug B Message Formats</div>
                            <div style="margin-bottom: 16px;">
                                <strong style="color: #10B981;">NBIRTH (Node Birth):</strong>
                                <div style="background: #1E1E1E; color: #D4D4D4; padding: 12px; border-radius: 6px; margin-top: 8px; font-family: 'Monaco', 'Courier New', monospace; font-size: 11px;">
spBv1.0/group_id/NBIRTH/edge_node_id
{<span style="color: #9CDCFE;">"timestamp"</span>: <span style="color: #B5CEA8;">1738851825000</span>, <span style="color: #9CDCFE;">"metrics"</span>: [...], <span style="color: #9CDCFE;">"seq"</span>: <span style="color: #B5CEA8;">0</span>}
                                </div>
                            </div>
                            <div style="margin-bottom: 16px;">
                                <strong style="color: #00A9E0;">NDATA (Node Data):</strong>
                                <div style="background: #1E1E1E; color: #D4D4D4; padding: 12px; border-radius: 6px; margin-top: 8px; font-family: 'Monaco', 'Courier New', monospace; font-size: 11px;">
spBv1.0/group_id/NDATA/edge_node_id
{<span style="color: #9CDCFE;">"timestamp"</span>: <span style="color: #B5CEA8;">1738851826000</span>, <span style="color: #9CDCFE;">"metrics"</span>: [{<span style="color: #9CDCFE;">"name"</span>: <span style="color: #CE9178;">"sensor1"</span>, <span style="color: #9CDCFE;">"value"</span>: <span style="color: #B5CEA8;">123.45</span>}], <span style="color: #9CDCFE;">"seq"</span>: <span style="color: #B5CEA8;">1</span>}
                                </div>
                            </div>
                            <div>
                                <strong style="color: #EF4444;">NDEATH (Node Death):</strong>
                                <div style="background: #1E1E1E; color: #D4D4D4; padding: 12px; border-radius: 6px; margin-top: 8px; font-family: 'Monaco', 'Courier New', monospace; font-size: 11px;">
spBv1.0/group_id/NDEATH/edge_node_id
{<span style="color: #9CDCFE;">"timestamp"</span>: <span style="color: #B5CEA8;">1738851900000</span>, <span style="color: #9CDCFE;">"bdSeq"</span>: <span style="color: #B5CEA8;">5</span>}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Honeywell Mode Panel -->
                <div class="mode-panel" id="panel-honeywell">
                    <div class="mode-panel-header">
                        <div class="mode-panel-title">️ Honeywell Experion PKS Mode</div>
                        <div class="mode-panel-subtitle">Process Control • Composite Points • FIM/ACE/LCN Modules</div>
                    </div>
                    <div class="mode-panel-body">
                        <div class="mode-section">
                            <div class="mode-section-title">System Metrics</div>
                            <div class="mode-metrics-grid">
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Messages/Sec</div>
                                    <div class="mode-metric-value" id="honeywell-msg-rate">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Active Modules</div>
                                    <div class="mode-metric-value" id="honeywell-modules">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Composite Points</div>
                                    <div class="mode-metric-value" id="honeywell-points">0</div>
                                </div>
                                <div class="mode-metric-card">
                                    <div class="mode-metric-label">Controllers</div>
                                    <div class="mode-metric-value" id="honeywell-controllers">0</div>
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">️ Module Structure</div>
                            <div id="honeywell-modules-view" class="honeywell-modules">
                                <!-- Dynamically populated -->
                                <div style="text-align: center; padding: 40px; color: #6B7280;">
                                    No modules configured. Enable Honeywell mode to see structure.
                                </div>
                            </div>
                        </div>

                        <div class="mode-section">
                            <div class="mode-section-title">Composite Point Format</div>
                            <div style="background: #1E1E1E; color: #D4D4D4; padding: 16px; border-radius: 8px; font-family: 'Monaco', 'Courier New', monospace; font-size: 12px; line-height: 1.6;">
{
  <span style="color: #9CDCFE;">"point"</span>: <span style="color: #CE9178;">"FIC101.PV"</span>,
  <span style="color: #9CDCFE;">"module"</span>: <span style="color: #CE9178;">"FIM"</span>,
  <span style="color: #9CDCFE;">"controller"</span>: <span style="color: #CE9178;">"C300-1"</span>,
  <span style="color: #9CDCFE;">"attributes"</span>: {
    <span style="color: #9CDCFE;">"PV"</span>: <span style="color: #B5CEA8;">45.2</span>,
    <span style="color: #9CDCFE;">"SP"</span>: <span style="color: #B5CEA8;">50.0</span>,
    <span style="color: #9CDCFE;">"OP"</span>: <span style="color: #B5CEA8;">62.5</span>,
    <span style="color: #9CDCFE;">"MODE"</span>: <span style="color: #CE9178;">"AUTO"</span>
  },
  <span style="color: #9CDCFE;">"quality"</span>: <span style="color: #CE9178;">"GOOD"</span>,
  <span style="color: #9CDCFE;">"timestamp"</span>: <span style="color: #B5CEA8;">1738851825000</span>
}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Message Inspector -->
                <div class="mode-section" style="margin-top: 32px;">
                    <div class="message-inspector">
                        <div class="message-inspector-header">
                            <div class="message-inspector-title">Live Message Inspector</div>
                            <div class="message-inspector-controls">
                                <select id="inspector-protocol-filter" class="config-input" style="width: auto; padding: 6px 12px; font-size: 12px; margin-right: 8px;">
                                    <option value="">All Protocols</option>
                                    <option value="mqtt">MQTT</option>
                                    <option value="opcua">OPC-UA</option>
                                    <option value="modbus">Modbus</option>
                                </select>
                                <select id="inspector-mode-filter" class="config-input" style="width: auto; padding: 6px 12px; font-size: 12px; margin-right: 8px;">
                                    <option value="">All Modes</option>
                                    <option value="generic">Generic</option>
                                    <option value="kepware">Kepware</option>
                                    <option value="sparkplug_b">Sparkplug B</option>
                                    <option value="honeywell">Honeywell</option>
                                </select>
                                <select id="inspector-industry-filter" class="config-input" style="width: auto; padding: 6px 12px; font-size: 12px; margin-right: 8px;">
                                    <option value="">All Industries</option>
                                    <option value="mining">Mining</option>
                                    <option value="utilities">Utilities</option>
                                    <option value="manufacturing">Manufacturing</option>
                                    <option value="oil_gas">Oil & Gas</option>
                                </select>
                                <button class="btn-test" onclick="toggleMessageInspector()" id="inspector-toggle-btn">Start</button>
                                <button class="btn-test" onclick="clearMessageInspector()">Clear</button>
                            </div>
                        </div>
                        <div class="message-inspector-body" id="message-inspector-body">
                            <div style="text-align: center; padding: 40px; color: #6B7280;">
                                Click "Start" to begin capturing vendor mode messages
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
        <!-- End Vendor Modes Tab -->

        <!-- Connection Info Tab Content -->
        <div class="tab-content" id="content-connections">
            <div class="card" style="margin-bottom: 24px;">
                <div class="card-title">Protocol Endpoints</div>
                <div id="connection-protocols" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 16px;">
                    <!-- Protocols will be loaded here -->
                </div>
            </div>

            <div class="card" style="margin-bottom: 24px;">
                <div class="card-title">Vendor Mode Topic/Node Patterns</div>
                <div id="connection-vendor-modes" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px;">
                    <!-- Vendor modes will be loaded here -->
                </div>
            </div>

            <div class="card" style="margin-bottom: 24px;">
                <div class="card-title">PLC Controllers</div>
                <div id="connection-plcs" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                    <!-- PLCs will be loaded here -->
                </div>
            </div>

            <div class="card">
                <div class="card-title">Connection Examples</div>
                <div id="connection-examples" style="display: flex; flex-direction: column; gap: 20px;">
                    <!-- Examples will be loaded here -->
                </div>
            </div>
        </div>
        <!-- End Connection Info Tab -->

    </div>"""


def get_scripts_html() -> str:
    """Return the JavaScript code for the web UI."""
    return """    <script>
        // Register Chart.js annotation plugin
        if (typeof Chart !== 'undefined' && typeof chartAnnotation !== 'undefined') {
            Chart.register(chartAnnotation);
        }

        // WebSocket connection
        let ws = null;
        let reconnectInterval = null;
        const charts = {};
        let conversationHistory = [];

        // Multi-sensor overlay support
        let selectedSensors = new Set();
        let overlayCharts = new Map();
        const CHART_COLORS = ['#00a8e1', '#ff3621', '#10b981', '#fbbf24', '#f97316', '#8b5cf6', '#ec4899', '#06b6d4'];

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected');
                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                // Attempt to reconnect
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(() => {
                        console.log('Attempting to reconnect...');
                        connectWebSocket();
                    }, 5000);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        function handleWebSocketMessage(data) {
            if (data.type === 'sensor_data') {
                // Update charts with new data
                Object.entries(data.sensors).forEach(([sensor, value]) => {
                    updateChart(sensor, value, data.timestamp);
                });
            } else if (data.type === 'status_update') {
                // Update protocol status indicators and button states
                Object.entries(data.simulators).forEach(([protocol, status]) => {
                    const badge = document.getElementById(`status-${protocol}`);
                    const startBtn = document.getElementById(`start-${protocol}`);
                    const stopBtn = document.getElementById(`stop-${protocol}`);

                    if (badge) {
                        if (status.running) {
                            badge.classList.add('running');
                        } else {
                            badge.classList.remove('running');
                        }
                    }

                    // Update button states: if running, disable start and enable stop
                    if (startBtn && stopBtn) {
                        if (status.running) {
                            startBtn.disabled = true;
                            startBtn.style.opacity = '0.5';
                            startBtn.style.cursor = 'not-allowed';
                            stopBtn.disabled = false;
                            stopBtn.style.opacity = '1';
                            stopBtn.style.cursor = 'pointer';
                        } else {
                            startBtn.disabled = false;
                            startBtn.style.opacity = '1';
                            startBtn.style.cursor = 'pointer';
                            stopBtn.disabled = true;
                            stopBtn.style.opacity = '0.5';
                            stopBtn.style.cursor = 'not-allowed';
                        }
                    }
                });
            } else if (data.type === 'nlp_response') {
                // Handle natural language response
                console.log('NLP Response received:', data);
                removeTypingIndicator();

                let response = '';
                if (data.action === 'start') {
                    // Use backend message first, fall back to constructed message
                    response = data.message || `${data.target ? data.target.toUpperCase() : 'Protocol'} started successfully!`;
                } else if (data.action === 'stop') {
                    // Use backend message first, fall back to constructed message
                    response = data.message || `${data.target ? data.target.toUpperCase() : 'Protocol'} stopped successfully!`;
                } else if (data.action === 'inject_fault') {
                    // Use backend message first, fall back to constructed message
                    const duration = data.parameters?.duration || '?';
                    response = data.message || `Fault injected into ${data.target} for ${duration}s`;
                } else if (data.action === 'status') {
                    // Show the full status message from backend
                    response = data.message || 'Status information updated';
                } else if (data.action === 'list_sensors') {
                    // Use the formatted message from backend (contains full sensor list)
                    response = data.message || `Showing ${data.target} sensors`;
                } else if (data.action === 'chat') {
                    // Use message first, reasoning second (message is usually formatted better)
                    response = data.message || data.reasoning || 'Command processed';
                } else {
                    // Default: prefer message over reasoning
                    response = data.message || data.reasoning || 'Command executed';
                }

                // Show error if command failed
                if (!data.success) {
                    response = `${data.message || 'Command failed'}`;
                }

                // For list_sensors action, don't show reasoning separately (it's redundant)
                const showReasoning = data.action !== 'list_sensors' ? data.reasoning : null;
                addMessage('agent', response, showReasoning);

                // Add to conversation history
                conversationHistory.push({
                    role: 'assistant',
                    content: response
                });
            } else if (data.type === 'error') {
                // Handle error messages
                console.error('WebSocket error:', data);
                removeTypingIndicator();
                addMessage('agent', `Error: ${data.message}`);
            }
        }

        function updateChart(sensorPath, value, timestamp) {
            // Update overlay charts first
            updateOverlayChart(sensorPath, value, timestamp);

            if (!charts[sensorPath]) return;

            const chart = charts[sensorPath];
            const fftState = fftStates[sensorPath];
            const spectrogramState = spectrogramStates[sensorPath];
            const spcState = spcStates[sensorPath];

            // If in FFT mode, add to data buffer
            if (fftState && fftState.isFFT) {
                if (!fftState.dataBuffer) {
                    fftState.dataBuffer = [];
                }
                fftState.dataBuffer.push(value);

                // Keep only last 512 samples for FFT
                if (fftState.dataBuffer.length > 512) {
                    fftState.dataBuffer.shift();
                }
            }
            // If in Spectrogram mode, add to data buffer
            else if (spectrogramState && spectrogramState.isSpectrogram) {
                if (!spectrogramState.dataBuffer) {
                    spectrogramState.dataBuffer = [];
                }
                spectrogramState.dataBuffer.push(value);

                // Keep only last 512 samples for spectrogram FFT
                if (spectrogramState.dataBuffer.length > 512) {
                    spectrogramState.dataBuffer.shift();
                }
            }
            // If in SPC mode, add to data buffer
            else if (spcState && spcState.isSPC) {
                if (!spcState.dataBuffer) {
                    spcState.dataBuffer = [];
                }
                spcState.dataBuffer.push(value);

                // Keep only last 100 samples for SPC (manageable control chart)
                if (spcState.dataBuffer.length > 100) {
                    spcState.dataBuffer.shift();
                }
            }
            // Time-domain chart update (default mode)
            else {
                const date = new Date(timestamp * 1000);

                chart.data.labels.push(date);
                chart.data.datasets[0].data.push(value);

                // Keep only last 240 points (2 minutes at 500ms intervals)
                if (chart.data.labels.length > 240) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }

                chart.update('none'); // Update without animation for real-time
            }

            // Update live value display (works for all modes)
            const valueDisplay = document.getElementById(`value-${sensorPath.replace(/\\//g, '-')}`);
            if (valueDisplay) {
                valueDisplay.textContent = value.toFixed(2);
            }
        }

        function createChart(sensorPath, sensorInfo) {
            const chartId = `chart-${sensorPath.replace(/\\//g, '-')}`;
            const valueId = `value-${sensorPath.replace(/\\//g, '-')}`;
            const isVibration = sensorInfo.type && (sensorInfo.type.toLowerCase().includes('vibration') || sensorInfo.type.toLowerCase().includes('vib'));

            // Protocol badges HTML
            const protocolBadgesHTML = sensorInfo.protocols && sensorInfo.protocols.length > 0
                ? sensorInfo.protocols.map(proto =>
                    `<span class="protocol-badge-mini ${proto}">${proto}</span>`
                ).join('')
                : '';

            // Add FFT button for vibration sensors
            const fftButtonHTML = isVibration
                ? `<button class="btn-fft" onclick="toggleFFT('${sensorPath}')">FFT</button>`
                : '';

            // Add Spectrogram button for vibration sensors
            const spectrogramButtonHTML = isVibration
                ? `<button class="btn-spectrogram" onclick="toggleSpectrogram('${sensorPath}')">Spectrogram</button>`
                : '';

            // Add SPC button for all sensors
            const spcButtonHTML = `<button class="btn-spc" onclick="toggleSPC('${sensorPath}')">SPC</button>`;

            const chartHtml = `
                <div class="chart-card" id="card-${sensorPath.replace(/\\//g, '-')}">
                    <div class="chart-header">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div class="chart-title">${sensorPath}</div>
                                <div class="protocol-badges">${protocolBadgesHTML}</div>
                            </div>
                            <div class="live-value" id="${valueId}">--</div>
                        </div>
                        <div class="chart-buttons">
                            ${fftButtonHTML}
                            ${spectrogramButtonHTML}
                            ${spcButtonHTML}
                            <button class="btn btn-stop" onclick="removeChart('${sensorPath}')">×</button>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="${chartId}"></canvas>
                    </div>
                </div>
            `;

            document.getElementById('chart-section').insertAdjacentHTML('beforeend', chartHtml);

            const ctx = document.getElementById(chartId);
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: `${sensorPath} (${sensorInfo.unit})`,
                        data: [],
                        borderColor: '#FF3621',
                        backgroundColor: 'rgba(255, 54, 33, 0.1)',
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                displayFormats: {
                                    second: 'HH:mm:ss'
                                }
                            },
                            title: {
                                display: true,
                                text: 'Time',
                                color: '#A0A4A8',
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                color: '#A0A4A8',
                                maxRotation: 0
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        y: {
                            beginAtZero: sensorInfo.min_value >= 0,
                            min: sensorInfo.min_value,
                            max: sensorInfo.max_value,
                            title: {
                                display: true,
                                text: `${sensorInfo.type || 'Value'} (${sensorInfo.unit})`,
                                color: '#A0A4A8',
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                color: '#A0A4A8'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(26, 31, 58, 0.98)',
                            titleColor: '#E8EAED',
                            bodyColor: '#A0A4A8',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false
                        }
                    },
                    // Store sensorInfo for FFT toggle
                    sensorInfo: sensorInfo
                }
            });

            charts[sensorPath] = chart;

            // Subscribe to sensor via WebSocket
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'subscribe',
                    sensors: [sensorPath]
                }));
            }
        }

        function removeChart(sensorPath) {
            // Unsubscribe from sensor
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'unsubscribe',
                    sensors: [sensorPath]
                }));
            }

            // Clear FFT update interval if exists (but keep fftStates for toggle)
            if (fftStates[sensorPath] && fftStates[sensorPath].updateInterval) {
                clearInterval(fftStates[sensorPath].updateInterval);
                fftStates[sensorPath].updateInterval = null;
                // Don't delete fftStates - keep it for toggle back to FFT mode
            }

            // Clear Spectrogram update interval if exists (but keep spectrogramStates for toggle)
            if (spectrogramStates[sensorPath] && spectrogramStates[sensorPath].updateInterval) {
                clearInterval(spectrogramStates[sensorPath].updateInterval);
                spectrogramStates[sensorPath].updateInterval = null;
                // Don't delete spectrogramStates - keep it for toggle back
            }

            // Clear SPC update interval if exists (but keep spcStates for toggle)
            if (spcStates[sensorPath] && spcStates[sensorPath].updateInterval) {
                clearInterval(spcStates[sensorPath].updateInterval);
                spcStates[sensorPath].updateInterval = null;
                // Don't delete spcStates - keep it for toggle back
            }

            // Remove chart
            if (charts[sensorPath]) {
                charts[sensorPath].destroy();
                delete charts[sensorPath];
            }

            // Remove DOM element
            const cardId = `card-${sensorPath.replace(/\\//g, '-')}`;
            document.getElementById(cardId)?.remove();
        }

        function startProtocol(protocol) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'nlp_command',
                    text: `start ${protocol}`
                }));
            }
        }

        function stopProtocol(protocol) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'nlp_command',
                    text: `stop ${protocol}`
                }));
            }
        }

        // Multi-Sensor Overlay Functions
        function toggleSensorSelection(sensorPath, sensorInfo, sensorItem) {
            if (selectedSensors.has(sensorPath)) {
                selectedSensors.delete(sensorPath);
                sensorItem.classList.remove('selected');
            } else {
                selectedSensors.add(sensorPath);
                sensorItem.classList.add('selected');
                // Store sensor info for later use
                if (!sensorItem.dataset.sensorInfo) {
                    sensorItem.dataset.sensorInfo = JSON.stringify(sensorInfo);
                }
            }

            // Show/update overlay button
            updateOverlayButton();
        }

        function updateOverlayButton() {
            let overlayBtn = document.getElementById('create-overlay-btn');

            if (selectedSensors.size === 0) {
                // Remove button if no sensors selected
                if (overlayBtn) overlayBtn.remove();
                return;
            }

            if (!overlayBtn) {
                // Create button
                overlayBtn = document.createElement('button');
                overlayBtn.id = 'create-overlay-btn';
                overlayBtn.style.cssText = `
                    position: fixed;
                    bottom: 24px;
                    right: 24px;
                    padding: 16px 24px;
                    background: linear-gradient(135deg, #00A9E0 0%, #0080B3 100%);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0, 169, 224, 0.3);
                    z-index: 1000;
                    transition: all 0.3s;
                `;
                overlayBtn.onmouseover = function() {
                    this.style.transform = 'translateY(-2px)';
                    this.style.boxShadow = '0 6px 16px rgba(0, 169, 224, 0.4)';
                };
                overlayBtn.onmouseout = function() {
                    this.style.transform = 'translateY(0)';
                    this.style.boxShadow = '0 4px 12px rgba(0, 169, 224, 0.3)';
                };
                overlayBtn.onclick = createOverlayChart;
                document.body.appendChild(overlayBtn);
            }

            overlayBtn.textContent = `Create Overlay Chart (${selectedSensors.size} sensor${selectedSensors.size !== 1 ? 's' : ''})`;
        }

        function createOverlayChart() {
            if (selectedSensors.size === 0) return;

            const chartId = 'overlay-' + Date.now();
            const sensorsArray = Array.from(selectedSensors);

            // Get sensor metadata from DOM
            const sensorMetadata = sensorsArray.map(path => {
                const sensorItem = document.querySelector(`[onclick*="${path}"]`);
                if (sensorItem && sensorItem.dataset.sensorInfo) {
                    return { path, ...JSON.parse(sensorItem.dataset.sensorInfo) };
                }
                // Fallback - extract from path
                const parts = path.split('/');
                return {
                    path,
                    name: parts[parts.length - 1],
                    unit: 'unit',
                    type: 'sensor'
                };
            });

            // Group by unit for Y-axis assignment
            const unitGroups = {};
            sensorMetadata.forEach(s => {
                const unit = s.unit || 'unknown';
                if (!unitGroups[unit]) unitGroups[unit] = [];
                unitGroups[unit].push(s);
            });

            // Create chart container
            const chartSection = document.getElementById('chart-section');
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card';
            cardDiv.id = `card-${chartId}`;
            cardDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 style="color: #00A9E0; font-size: 18px; font-weight: 600;">Multi-Sensor Overlay (${sensorsArray.length} sensors)</h3>
                    <div>
                        <button class="btn btn-stop" onclick="removeOverlayChart('${chartId}')" style="background: #EF4444; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;">Remove</button>
                    </div>
                </div>
                <div style="position: relative; height: 400px;">
                    <canvas id="${chartId}"></canvas>
                </div>
                <div id="${chartId}-correlation" style="margin-top: 12px; padding: 12px; background: #F3F4F6; border-radius: 6px; font-size: 14px; color: #4B5563;"></div>
            `;
            chartSection.insertBefore(cardDiv, chartSection.firstChild);

            // Create datasets
            const datasets = sensorMetadata.map((sensor, i) => ({
                label: sensor.name + ' (' + sensor.unit + ')',
                data: [],
                borderColor: CHART_COLORS[i % CHART_COLORS.length],
                backgroundColor: CHART_COLORS[i % CHART_COLORS.length] + '33',
                yAxisID: 'y' + Object.keys(unitGroups).indexOf(sensor.unit || 'unknown'),
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2
            }));

            // Create Y-axes
            const scales = {
                x: {
                    type: 'time',
                    time: { unit: 'second' },
                    title: { display: true, text: 'Time', color: '#6B7280' },
                    ticks: { color: '#6B7280' },
                    grid: { color: '#E5E7EB' }
                }
            };

            Object.keys(unitGroups).forEach((unit, i) => {
                scales['y' + i] = {
                    type: 'linear',
                    position: i % 2 === 0 ? 'left' : 'right',
                    title: { display: true, text: unit, color: '#6B7280' },
                    ticks: { color: '#6B7280' },
                    grid: { drawOnChartArea: i === 0, color: '#E5E7EB' }
                };
            });

            // Create chart
            const ctx = document.getElementById(chartId).getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: { datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales,
                    plugins: {
                        legend: {
                            display: true,
                            labels: { color: '#2E3036' }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    }
                }
            });

            overlayCharts.set(chartId, { chart, sensors: sensorsArray, metadata: sensorMetadata });

            // Subscribe to all sensors
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'subscribe',
                    sensors: sensorsArray
                }));
            }

            // Clear selection
            selectedSensors.clear();
            document.querySelectorAll('.sensor-item.selected').forEach(item => {
                item.classList.remove('selected');
            });
            updateOverlayButton();
        }

        function removeOverlayChart(chartId) {
            const chartData = overlayCharts.get(chartId);
            if (chartData) {
                // Unsubscribe from sensors
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'unsubscribe',
                        sensors: chartData.sensors
                    }));
                }

                // Destroy chart
                chartData.chart.destroy();
                overlayCharts.delete(chartId);
            }

            // Remove DOM element
            document.getElementById(`card-${chartId}`)?.remove();
        }

        function updateOverlayChart(sensorPath, value, timestamp) {
            // Update all overlay charts that contain this sensor
            overlayCharts.forEach((chartData, chartId) => {
                const sensorIndex = chartData.sensors.indexOf(sensorPath);
                if (sensorIndex !== -1) {
                    const chart = chartData.chart;
                    const dataset = chart.data.datasets[sensorIndex];

                    // Add new data point
                    dataset.data.push({ x: timestamp, y: value });

                    // Keep last 100 points
                    if (dataset.data.length > 100) {
                        dataset.data.shift();
                    }

                    chart.update('none');

                    // Update correlation display
                    updateCorrelationDisplay(chartId);
                }
            });
        }

        function updateCorrelationDisplay(chartId) {
            const chartData = overlayCharts.get(chartId);
            if (!chartData || chartData.sensors.length < 2) return;

            const correlations = [];
            const datasets = chartData.chart.data.datasets;

            for (let i = 0; i < datasets.length - 1; i++) {
                for (let j = i + 1; j < datasets.length; j++) {
                    const data1 = datasets[i].data.map(d => d.y);
                    const data2 = datasets[j].data.map(d => d.y);

                    if (data1.length >= 10 && data2.length >= 10) {
                        const r = pearsonCorrelation(data1, data2);
                        if (!isNaN(r)) {
                            correlations.push({
                                pair: `${chartData.metadata[i].name} ↔ ${chartData.metadata[j].name}`,
                                correlation: r.toFixed(3)
                            });
                        }
                    }
                }
            }

            const corrDiv = document.getElementById(chartId + '-correlation');
            if (corrDiv && correlations.length > 0) {
                corrDiv.innerHTML = '<strong>Pearson Correlations:</strong> ' +
                    correlations.map(c => `${c.pair}: r=${c.correlation}`).join(' | ');
            }
        }

        function pearsonCorrelation(x, y) {
            const n = Math.min(x.length, y.length);
            if (n < 2) return 0;

            const xMean = x.slice(0, n).reduce((a, b) => a + b, 0) / n;
            const yMean = y.slice(0, n).reduce((a, b) => a + b, 0) / n;

            let num = 0, denX = 0, denY = 0;
            for (let i = 0; i < n; i++) {
                const dx = x[i] - xMean;
                const dy = y[i] - yMean;
                num += dx * dy;
                denX += dx * dx;
                denY += dy * dy;
            }

            return num / Math.sqrt(denX * denY);
        }

        // FFT Analysis Functions
        const fftStates = {}; // Track FFT state per sensor

        function toggleFFT(sensorPath) {
            const chart = charts[sensorPath];
            if (!chart) return;

            const button = document.querySelector(`[onclick="toggleFFT('${sensorPath}')"]`);
            const isFFTMode = fftStates[sensorPath]?.isFFT || false;

            if (isFFTMode) {
                // Switch back to time domain
                fftStates[sensorPath].isFFT = false;
                button.classList.remove('active');
                button.textContent = 'FFT';

                // Recreate as time-domain chart
                const cardId = `card-${sensorPath.replace(/\\//g, '-')}`;
                const card = document.getElementById(cardId);
                const sensorInfo = fftStates[sensorPath].sensorInfo;

                // Store the button HTML before removing
                const buttonsHTML = card.querySelector('.chart-buttons').innerHTML;

                // Remove and recreate
                removeChart(sensorPath);
                createChart(sensorPath, sensorInfo);
            } else {
                // Switch to FFT mode
                fftStates[sensorPath] = fftStates[sensorPath] || {};
                fftStates[sensorPath].isFFT = true;
                fftStates[sensorPath].sensorInfo = chart.options.sensorInfo || {};
                button.classList.add('active');
                button.textContent = 'Time';

                // Convert to FFT chart
                createFFTChart(sensorPath, chart);
            }
        }

        function createFFTChart(sensorPath, timeChart) {
            const chartId = `chart-${sensorPath.replace(/\\//g, '-')}`;

            // Destroy existing time-domain chart
            timeChart.destroy();

            // Create FFT chart (bar chart for frequency domain)
            const ctx = document.getElementById(chartId);
            const fftChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [], // Frequency bins (Hz)
                    datasets: [{
                        label: 'Amplitude (g RMS)',
                        data: [],
                        backgroundColor: 'rgba(255, 54, 33, 0.8)',
                        borderColor: '#FF3621',
                        borderWidth: 1,
                        barPercentage: 0.95,
                        categoryPercentage: 1.0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: {
                            type: 'category',
                            title: {
                                display: true,
                                text: 'Frequency (Hz)',
                                color: '#A0A4A8',
                                font: { size: 12, weight: 'bold' }
                            },
                            ticks: {
                                color: '#A0A4A8',
                                maxRotation: 45,
                                minRotation: 45,
                                autoSkip: true,
                                maxTicksLimit: 20
                            },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        },
                        y: {
                            type: 'logarithmic',
                            title: {
                                display: true,
                                text: 'Amplitude (g RMS)',
                                color: '#A0A4A8',
                                font: { size: 12, weight: 'bold' }
                            },
                            ticks: {
                                color: '#A0A4A8',
                                callback: function(value) {
                                    return value.toExponential(2);
                                }
                            },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            min: 0.0001
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(26, 31, 58, 0.98)',
                            titleColor: '#E8EAED',
                            bodyColor: '#A0A4A8',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {
                                title: (items) => `${items[0].label} Hz`,
                                label: (item) => `Amplitude: ${item.parsed.y.toFixed(4)} g`
                            }
                        },
                        annotation: {
                            annotations: getBearingFrequencyAnnotations()
                        }
                    }
                }
            });

            // Store FFT chart
            charts[sensorPath] = fftChart;

            // Start FFT computation interval
            startFFTUpdates(sensorPath);
        }

        function getBearingFrequencyAnnotations() {
            // Bearing defect frequencies for typical motor bearing
            // BPFO (Ball Pass Frequency Outer): 107.5 Hz
            // BPFI (Ball Pass Frequency Inner): 162.5 Hz
            // BSF (Ball Spin Frequency): 42.8 Hz
            // FTF (Fundamental Train Frequency): 16.2 Hz

            return {
                bpfo: {
                    type: 'line',
                    xMin: 107.5,
                    xMax: 107.5,
                    borderColor: '#FF3621',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: 'BPFO',
                        position: 'start',
                        backgroundColor: '#FF3621',
                        color: 'white',
                        font: { size: 10, weight: 'bold' }
                    }
                },
                bpfi: {
                    type: 'line',
                    xMin: 162.5,
                    xMax: 162.5,
                    borderColor: '#00A9E0',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: 'BPFI',
                        position: 'start',
                        backgroundColor: '#00A9E0',
                        color: 'white',
                        font: { size: 10, weight: 'bold' }
                    }
                },
                bsf: {
                    type: 'line',
                    xMin: 42.8,
                    xMax: 42.8,
                    borderColor: '#10B981',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: 'BSF',
                        position: 'start',
                        backgroundColor: '#10B981',
                        color: 'white',
                        font: { size: 10, weight: 'bold' }
                    }
                },
                ftf: {
                    type: 'line',
                    xMin: 16.2,
                    xMax: 16.2,
                    borderColor: '#FBBF24',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: 'FTF',
                        position: 'start',
                        backgroundColor: '#FBBF24',
                        color: 'white',
                        font: { size: 10, weight: 'bold' }
                    }
                }
            };
        }

        function startFFTUpdates(sensorPath) {
            // Store time-domain data buffer for FFT computation
            if (!fftStates[sensorPath]) {
                fftStates[sensorPath] = {};
            }

            // Initialize data buffer if not already exists
            if (!fftStates[sensorPath].dataBuffer) {
                fftStates[sensorPath].dataBuffer = [];
            }

            // Update FFT every 500ms
            fftStates[sensorPath].updateInterval = setInterval(() => {
                computeAndUpdateFFT(sensorPath);
            }, 500);
        }

        function computeAndUpdateFFT(sensorPath) {
            const chart = charts[sensorPath];
            const state = fftStates[sensorPath];

            if (!chart || !state || !state.dataBuffer || state.dataBuffer.length < 8) {
                console.log(`FFT: Waiting for data... Buffer size: ${state?.dataBuffer?.length || 0}`);
                return; // Need at least 8 samples for FFT (will round to power of 2)
            }

            // Get last 256 samples from buffer (power of 2 for FFT)
            const bufferSize = Math.min(256, Math.pow(2, Math.floor(Math.log2(state.dataBuffer.length))));
            const samples = state.dataBuffer.slice(-bufferSize);
            console.log(`FFT: Computing with ${bufferSize} samples from buffer of ${state.dataBuffer.length}`);

            // Compute FFT using fft.js library
            const fft = new FFTNayuki(bufferSize);
            const real = new Array(bufferSize);
            const imag = new Array(bufferSize);

            // Copy samples and apply Hanning window
            for (let i = 0; i < bufferSize; i++) {
                const window = 0.5 * (1 - Math.cos(2 * Math.PI * i / (bufferSize - 1)));
                real[i] = samples[i] * window;
                imag[i] = 0;
            }

            // Perform FFT
            fft.transform(real, imag);

            // Compute magnitudes and frequency bins
            const sampleRate = 2; // 2 Hz (500ms updates)
            const freqResolution = sampleRate / bufferSize;
            const numBins = Math.floor(bufferSize / 2); // Only positive frequencies

            const frequencies = [];
            const magnitudes = [];

            for (let i = 0; i < numBins; i++) {
                const freq = i * freqResolution;
                if (freq <= 500) { // Only show up to 500 Hz
                    frequencies.push(freq.toFixed(1));
                    const magnitude = Math.sqrt(real[i] * real[i] + imag[i] * imag[i]) / bufferSize;
                    magnitudes.push(magnitude);
                }
            }

            // Update chart
            chart.data.labels = frequencies;
            chart.data.datasets[0].data = magnitudes;
            chart.update('none');

            console.log(`FFT: Updated chart with ${frequencies.length} frequency bins (0 to ${frequencies[frequencies.length-1]} Hz)`);
            console.log(`FFT: Magnitude range: ${Math.min(...magnitudes).toExponential(2)} to ${Math.max(...magnitudes).toExponential(2)}`);
        }

        // Simple FFT implementation (Cooley-Tukey algorithm)
        class FFTNayuki {
            constructor(n) {
                this.n = n;
                this.levels = Math.log2(n);
                if (Math.pow(2, this.levels) !== n) {
                    throw new Error('FFT size must be power of 2');
                }
            }

            transform(real, imag) {
                const n = this.n;

                // Bit-reversal permutation
                for (let i = 0; i < n; i++) {
                    const j = this.reverseBits(i, this.levels);
                    if (j > i) {
                        [real[i], real[j]] = [real[j], real[i]];
                        [imag[i], imag[j]] = [imag[j], imag[i]];
                    }
                }

                // Cooley-Tukey decimation-in-time FFT
                for (let size = 2; size <= n; size *= 2) {
                    const halfsize = size / 2;
                    const tablestep = n / size;
                    for (let i = 0; i < n; i += size) {
                        for (let j = i, k = 0; j < i + halfsize; j++, k += tablestep) {
                            const tpre = real[j + halfsize] * Math.cos(2 * Math.PI * k / n) +
                                        imag[j + halfsize] * Math.sin(2 * Math.PI * k / n);
                            const tpim = -real[j + halfsize] * Math.sin(2 * Math.PI * k / n) +
                                         imag[j + halfsize] * Math.cos(2 * Math.PI * k / n);
                            real[j + halfsize] = real[j] - tpre;
                            imag[j + halfsize] = imag[j] - tpim;
                            real[j] += tpre;
                            imag[j] += tpim;
                        }
                    }
                }
            }

            reverseBits(x, bits) {
                let y = 0;
                for (let i = 0; i < bits; i++) {
                    y = (y << 1) | (x & 1);
                    x >>>= 1;
                }
                return y;
            }
        }

        // ========================================
        // SPECTROGRAM (Time-Frequency Heatmap)
        // ========================================
        const spectrogramStates = {}; // Track spectrogram state per sensor

        function toggleSpectrogram(sensorPath) {
            const chart = charts[sensorPath];
            if (!chart) return;

            const button = document.querySelector(`[onclick="toggleSpectrogram('${sensorPath}')"]`);
            const isSpectrogramMode = spectrogramStates[sensorPath]?.isSpectrogram || false;

            if (isSpectrogramMode) {
                // Switch back to time domain
                spectrogramStates[sensorPath].isSpectrogram = false;
                button.classList.remove('active');
                button.textContent = 'Spectrogram';

                // Recreate as time-domain chart
                const cardId = `card-${sensorPath.replace(/\//g, '-')}`;
                const card = document.getElementById(cardId);
                if (card && spectrogramStates[sensorPath].sensorInfo) {
                    removeChart(sensorPath);
                    createChart(sensorPath, spectrogramStates[sensorPath].sensorInfo);
                }
            } else {
                // Switch to spectrogram mode
                spectrogramStates[sensorPath] = {
                    isSpectrogram: true,
                    sensorInfo: chart.options.sensorInfo,
                    dataBuffer: [],
                    spectrogramData: [], // Array of FFT results over time
                    maxSpectrogramRows: 60 // Keep last 60 FFT computations (30 seconds @ 500ms)
                };
                button.classList.add('active');
                button.textContent = 'Time';

                createSpectrogramChart(sensorPath, chart);
            }
        }

        function createSpectrogramChart(sensorPath, timeChart) {
            const chartId = `chart-${sensorPath.replace(/\//g, '-')}`;

            // Destroy existing time-domain chart
            timeChart.destroy();

            // Create spectrogram heatmap using Chart.js matrix plugin (if available)
            // For now, we'll use a simplified approach with horizontal bars representing time slices
            const ctx = document.getElementById(chartId);
            const spectrogramChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [], // Time labels
                    datasets: [] // Will be dynamically created for each frequency bin
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: {
                            type: 'category',
                            title: {
                                display: true,
                                text: 'Time (seconds ago)',
                                color: '#fff'
                            },
                            ticks: {
                                color: '#9CA3AF',
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 10
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        },
                        y: {
                            type: 'linear',
                            title: {
                                display: true,
                                text: 'Frequency (Hz)',
                                color: '#fff'
                            },
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: true,
                            callbacks: {
                                label: function(context) {
                                    return `Frequency: ${context.label} Hz, Magnitude: ${context.parsed.y.toFixed(4)} g`;
                                }
                            }
                        },
                        annotation: {
                            annotations: {
                                info: {
                                    type: 'label',
                                    xValue: 0,
                                    yValue: 0.8,
                                    content: ['Spectrogram: Time-Frequency Evolution', 'Darker = Higher Amplitude'],
                                    color: '#9CA3AF',
                                    font: {
                                        size: 10
                                    }
                                }
                            }
                        }
                    },
                    sensorInfo: timeChart.options.sensorInfo // Preserve for toggle
                }
            });

            charts[sensorPath] = spectrogramChart;
            startSpectrogramUpdates(sensorPath);
        }

        function startSpectrogramUpdates(sensorPath) {
            const state = spectrogramStates[sensorPath];
            if (!state) return;

            // Initialize data buffer
            if (!state.dataBuffer) {
                state.dataBuffer = [];
            }

            // Update every 500ms
            state.updateInterval = setInterval(() => {
                computeAndUpdateSpectrogram(sensorPath);
            }, 500);
        }

        function computeAndUpdateSpectrogram(sensorPath) {
            const chart = charts[sensorPath];
            const state = spectrogramStates[sensorPath];

            if (!chart || !state || !state.dataBuffer || state.dataBuffer.length < 8) {
                return;
            }

            const bufferSize = Math.min(64, Math.pow(2, Math.floor(Math.log2(state.dataBuffer.length))));
            const samples = state.dataBuffer.slice(-bufferSize);

            // Compute FFT
            const real = new Array(bufferSize);
            const imag = new Array(bufferSize);

            // Apply Hanning window
            for (let i = 0; i < bufferSize; i++) {
                const window = 0.5 * (1 - Math.cos(2 * Math.PI * i / (bufferSize - 1)));
                real[i] = samples[i] * window;
                imag[i] = 0;
            }

            const fft = new FFTNayuki(bufferSize);
            fft.transform(real, imag);

            // Compute magnitudes for first half (positive frequencies)
            const freqBins = [];
            const magnitudes = [];
            const sampleRate = 2; // 2 Hz (500ms updates)
            const numBins = bufferSize / 2;

            for (let i = 0; i < numBins; i++) {
                const freq = (i * sampleRate) / bufferSize;
                const magnitude = Math.sqrt(real[i] * real[i] + imag[i] * imag[i]) / bufferSize;
                freqBins.push(freq.toFixed(3));
                magnitudes.push(magnitude);
            }

            // Add this FFT result to spectrogram history
            state.spectrogramData.push({
                timestamp: Date.now(),
                freqBins: freqBins,
                magnitudes: magnitudes
            });

            // Keep only last maxSpectrogramRows
            if (state.spectrogramData.length > state.maxSpectrogramRows) {
                state.spectrogramData.shift();
            }

            // Update chart: Create a heatmap-style visualization
            // We'll use stacked horizontal bars with color intensity based on magnitude
            updateSpectrogramChart(chart, state);
        }

        function updateSpectrogramChart(chart, state) {
            if (state.spectrogramData.length === 0) return;

            // Get the most recent FFT result
            const latestFFT = state.spectrogramData[state.spectrogramData.length - 1];

            // Create scatter plot with bubbles sized by magnitude
            const scatterData = [];
            const now = Date.now();

            state.spectrogramData.forEach((fftResult, timeIndex) => {
                const secondsAgo = ((now - fftResult.timestamp) / 1000).toFixed(1);

                fftResult.magnitudes.forEach((magnitude, freqIndex) => {
                    if (magnitude > 0.0001) { // Filter out noise
                        scatterData.push({
                            x: secondsAgo,
                            y: parseFloat(fftResult.freqBins[freqIndex]),
                            r: Math.min(10, Math.max(2, magnitude * 1000)) // Bubble size
                        });
                    }
                });
            });

            // Update chart with bubble data
            chart.data.datasets = [{
                type: 'bubble',
                label: 'Magnitude',
                data: scatterData,
                backgroundColor: 'rgba(139, 92, 246, 0.6)',
                borderColor: 'rgba(139, 92, 246, 0.9)'
            }];

            // Update time labels
            const timeLabels = state.spectrogramData.map((fft, i) => {
                const secondsAgo = ((now - fft.timestamp) / 1000).toFixed(1);
                return secondsAgo;
            });

            chart.data.labels = latestFFT.freqBins; // Use frequency bins as labels
            chart.update('none');
        }

        // ========================================
        // SPC CHARTS (Statistical Process Control)
        // ========================================
        const spcStates = {}; // Track SPC state per sensor

        function toggleSPC(sensorPath) {
            const chart = charts[sensorPath];
            if (!chart) return;

            const button = document.querySelector(`[onclick="toggleSPC('${sensorPath}')"]`);
            const isSPCMode = spcStates[sensorPath]?.isSPC || false;

            if (isSPCMode) {
                // Switch back to time domain
                spcStates[sensorPath].isSPC = false;
                button.classList.remove('active');
                button.textContent = 'SPC';

                // Recreate as time-domain chart
                const cardId = `card-${sensorPath.replace(/\//g, '-')}`;
                const card = document.getElementById(cardId);
                if (card && spcStates[sensorPath].sensorInfo) {
                    removeChart(sensorPath);
                    createChart(sensorPath, spcStates[sensorPath].sensorInfo);
                }
            } else {
                // Switch to SPC mode
                spcStates[sensorPath] = {
                    isSPC: true,
                    sensorInfo: chart.options.sensorInfo,
                    dataBuffer: [],
                    mean: null,
                    stdDev: null,
                    ucl: null, // Upper Control Limit (+3σ)
                    lcl: null, // Lower Control Limit (-3σ)
                    uwl: null, // Upper Warning Limit (+2σ)
                    lwl: null  // Lower Warning Limit (-2σ)
                };
                button.classList.add('active');
                button.textContent = 'Time';

                createSPCChart(sensorPath, chart);
            }
        }

        function createSPCChart(sensorPath, timeChart) {
            const chartId = `chart-${sensorPath.replace(/\//g, '-')}`;

            // Destroy existing time-domain chart
            timeChart.destroy();

            // Create SPC chart with control limits
            const ctx = document.getElementById(chartId);
            const spcChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Value',
                            data: [],
                            borderColor: '#00A9E0',
                            backgroundColor: 'rgba(0, 169, 224, 0.1)',
                            pointBackgroundColor: '#00A9E0',
                            pointRadius: 4,
                            tension: 0.1,
                            order: 1
                        },
                        {
                            label: 'Mean',
                            data: [],
                            borderColor: '#059669',
                            borderDash: [5, 5],
                            pointRadius: 0,
                            borderWidth: 2,
                            order: 2
                        },
                        {
                            label: 'UCL (+3σ)',
                            data: [],
                            borderColor: '#EF4444',
                            borderDash: [10, 5],
                            pointRadius: 0,
                            borderWidth: 2,
                            order: 3
                        },
                        {
                            label: 'LCL (-3σ)',
                            data: [],
                            borderColor: '#EF4444',
                            borderDash: [10, 5],
                            pointRadius: 0,
                            borderWidth: 2,
                            order: 4
                        },
                        {
                            label: 'UWL (+2σ)',
                            data: [],
                            borderColor: '#F59E0B',
                            borderDash: [5, 3],
                            pointRadius: 0,
                            borderWidth: 1,
                            order: 5
                        },
                        {
                            label: 'LWL (-2σ)',
                            data: [],
                            borderColor: '#F59E0B',
                            borderDash: [5, 3],
                            pointRadius: 0,
                            borderWidth: 1,
                            order: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: {
                            type: 'category',
                            title: {
                                display: true,
                                text: 'Sample Number',
                                color: '#fff'
                            },
                            ticks: {
                                color: '#9CA3AF',
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 15
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        },
                        y: {
                            type: 'linear',
                            title: {
                                display: true,
                                text: `Value (${timeChart.data.datasets[0].label})`,
                                color: '#fff'
                            },
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: '#9CA3AF',
                                font: {
                                    size: 10
                                },
                                filter: function(item) {
                                    return !item.text.includes('Warning'); // Hide warning limits from legend
                                }
                            }
                        },
                        tooltip: {
                            enabled: true,
                            callbacks: {
                                label: function(context) {
                                    if (context.dataset.label === 'Value') {
                                        return `Value: ${context.parsed.y.toFixed(2)}`;
                                    }
                                    return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`;
                                }
                            }
                        }
                    },
                    sensorInfo: timeChart.options.sensorInfo // Preserve for toggle
                }
            });

            charts[sensorPath] = spcChart;
            startSPCUpdates(sensorPath);
        }

        function startSPCUpdates(sensorPath) {
            const state = spcStates[sensorPath];
            if (!state) return;

            // Initialize data buffer
            if (!state.dataBuffer) {
                state.dataBuffer = [];
            }

            // Update every 500ms
            state.updateInterval = setInterval(() => {
                updateSPCChart(sensorPath);
            }, 500);
        }

        function updateSPCChart(sensorPath) {
            const chart = charts[sensorPath];
            const state = spcStates[sensorPath];

            if (!chart || !state) return;

            // Get latest data from buffer
            if (!state.dataBuffer || state.dataBuffer.length < 20) {
                // Need at least 20 samples to compute meaningful statistics
                return;
            }

            // Compute statistics (mean and standard deviation)
            const n = state.dataBuffer.length;
            state.mean = state.dataBuffer.reduce((sum, val) => sum + val, 0) / n;

            const squaredDiffs = state.dataBuffer.map(val => Math.pow(val - state.mean, 2));
            state.stdDev = Math.sqrt(squaredDiffs.reduce((sum, val) => sum + val, 0) / n);

            // Compute control limits
            state.ucl = state.mean + (3 * state.stdDev); // Upper Control Limit
            state.lcl = state.mean - (3 * state.stdDev); // Lower Control Limit
            state.uwl = state.mean + (2 * state.stdDev); // Upper Warning Limit
            state.lwl = state.mean - (2 * state.stdDev); // Lower Warning Limit

            // Update chart datasets
            const labels = state.dataBuffer.map((_, i) => i + 1);
            const meanLine = state.dataBuffer.map(_ => state.mean);
            const uclLine = state.dataBuffer.map(_ => state.ucl);
            const lclLine = state.dataBuffer.map(_ => state.lcl);
            const uwlLine = state.dataBuffer.map(_ => state.uwl);
            const lwlLine = state.dataBuffer.map(_ => state.lwl);

            // Color points based on control limits
            const pointColors = state.dataBuffer.map(val => {
                if (val > state.ucl || val < state.lcl) {
                    return '#EF4444'; // Red: Out of control
                } else if (val > state.uwl || val < state.lwl) {
                    return '#F59E0B'; // Yellow: Warning
                } else {
                    return '#00A9E0'; // Blue: In control
                }
            });

            chart.data.labels = labels;
            chart.data.datasets[0].data = state.dataBuffer;
            chart.data.datasets[0].pointBackgroundColor = pointColors;
            chart.data.datasets[1].data = meanLine;
            chart.data.datasets[2].data = uclLine;
            chart.data.datasets[3].data = lclLine;
            chart.data.datasets[4].data = uwlLine;
            chart.data.datasets[5].data = lwlLine;

            chart.update('none');
        }

        // ========================================
        // CORRELATION HEATMAP MATRIX
        // ========================================
        let correlationHeatmapVisible = false;

        function createCorrelationHeatmap() {
            if (correlationHeatmapVisible) {
                // Hide existing heatmap
                const existingCard = document.getElementById('correlation-heatmap-card');
                if (existingCard) {
                    existingCard.remove();
                    correlationHeatmapVisible = false;
                }
                return;
            }

            // Get all active sensors
            const activeSensors = Object.keys(charts);
            if (activeSensors.length < 2) {
                alert('Please create at least 2 charts to see correlation heatmap');
                return;
            }

            // Create correlation matrix
            const correlationMatrix = {};
            activeSensors.forEach(sensor1 => {
                correlationMatrix[sensor1] = {};
                activeSensors.forEach(sensor2 => {
                    if (sensor1 === sensor2) {
                        correlationMatrix[sensor1][sensor2] = 1.0;
                    } else {
                        // Compute Pearson correlation
                        const chart1 = charts[sensor1];
                        const chart2 = charts[sensor2];
                        if (chart1.data.datasets[0].data.length > 1 && chart2.data.datasets[0].data.length > 1) {
                            const r = pearsonCorrelation(
                                chart1.data.datasets[0].data,
                                chart2.data.datasets[0].data
                            );
                            correlationMatrix[sensor1][sensor2] = r;
                        } else {
                            correlationMatrix[sensor1][sensor2] = 0;
                        }
                    }
                });
            });

            // Create heatmap visualization
            const chartHtml = `
                <div class="chart-card" id="correlation-heatmap-card" style="grid-column: 1 / -1; min-height: ${activeSensors.length * 40 + 200}px;">
                    <div class="chart-header">
                        <div class="chart-title">Correlation Heatmap Matrix</div>
                        <button class="btn btn-stop" onclick="createCorrelationHeatmap()">×</button>
                    </div>
                    <div class="chart-container">
                        <canvas id="correlation-heatmap-chart"></canvas>
                    </div>
                    <div style="padding: 12px; font-size: 11px; color: #9CA3AF; border-top: 1px solid rgba(255,255,255,0.1);">
                        <strong>Interpretation:</strong>
                        <span style="color: #EF4444;">Red (1.0)</span> = Perfect positive correlation,
                        <span style="color: #F59E0B;">Yellow (0.5)</span> = Moderate correlation,
                        <span style="color: #6B7280;">Gray (0.0)</span> = No correlation,
                        <span style="color: #3B82F6;">Blue (-1.0)</span> = Perfect negative correlation
                    </div>
                </div>
            `;

            document.getElementById('chart-section').insertAdjacentHTML('beforeend', chartHtml);

            // Create matrix visualization using Chart.js
            const ctx = document.getElementById('correlation-heatmap-chart');

            // Prepare matrix data for visualization
            const matrixData = [];
            activeSensors.forEach((sensor1, i) => {
                activeSensors.forEach((sensor2, j) => {
                    const correlation = correlationMatrix[sensor1][sensor2];
                    matrixData.push({
                        x: j,
                        y: i,
                        v: correlation
                    });
                });
            });

            new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Correlation',
                        data: matrixData.map(d => ({
                            x: d.x,
                            y: d.y,
                            r: 20
                        })),
                        backgroundColor: matrixData.map(d => {
                            // Color scale: Blue (-1) -> Gray (0) -> Red (+1)
                            const val = d.v;
                            if (val > 0) {
                                const intensity = Math.floor(val * 255);
                                return `rgba(239, 68, 68, ${val})`;
                            } else if (val < 0) {
                                const intensity = Math.floor(Math.abs(val) * 255);
                                return `rgba(59, 130, 246, ${Math.abs(val)})`;
                            } else {
                                return 'rgba(107, 114, 128, 0.5)';
                            }
                        }),
                        pointStyle: 'rect'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom',
                            min: -0.5,
                            max: activeSensors.length - 0.5,
                            ticks: {
                                color: '#9CA3AF',
                                callback: function(value) {
                                    return activeSensors[Math.round(value)]?.split('/').pop() || '';
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        },
                        y: {
                            type: 'linear',
                            reverse: true,
                            min: -0.5,
                            max: activeSensors.length - 0.5,
                            ticks: {
                                color: '#9CA3AF',
                                callback: function(value) {
                                    return activeSensors[Math.round(value)]?.split('/').pop() || '';
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: true,
                            callbacks: {
                                label: function(context) {
                                    const i = Math.round(context.parsed.y);
                                    const j = Math.round(context.parsed.x);
                                    const correlation = correlationMatrix[activeSensors[i]][activeSensors[j]];
                                    return [
                                        `${activeSensors[i]}`,
                                        `vs`,
                                        `${activeSensors[j]}`,
                                        `r = ${correlation.toFixed(3)}`
                                    ];
                                }
                            }
                        }
                    }
                }
            });

            correlationHeatmapVisible = true;
        }

        // Add button to navigation for correlation heatmap
        function addCorrelationHeatmapButton() {
            const overlayButton = document.querySelector('button[onclick*="createOverlayChart"]');
            if (overlayButton && !document.getElementById('correlation-heatmap-btn')) {
                const heatmapButton = document.createElement('button');
                heatmapButton.id = 'correlation-heatmap-btn';
                heatmapButton.className = 'btn-primary';
                heatmapButton.textContent = 'Correlation Heatmap';
                heatmapButton.style.marginLeft = '12px';
                heatmapButton.onclick = createCorrelationHeatmap;
                overlayButton.parentElement.appendChild(heatmapButton);
            }
        }

        // Call this when overlay button is shown
        setTimeout(addCorrelationHeatmapButton, 1000);

        // Zero-Bus Configuration Functions
        function toggleConfig(protocol) {
            const panel = document.getElementById(`config-${protocol}`);
            const icon = document.getElementById(`toggle-${protocol}`);

            if (panel.classList.contains('expanded')) {
                panel.classList.remove('expanded');
                icon.classList.remove('expanded');
            } else {
                panel.classList.add('expanded');
                icon.classList.add('expanded');
            }
        }

        // Training Platform Toggle Function
        function toggleTrainingPanel() {
            const panel = document.getElementById('training-panel');
            const icon = document.getElementById('training-toggle-icon');

            if (panel.style.display === 'none') {
                panel.style.display = 'block';
                icon.style.transform = 'rotate(180deg)';
            } else {
                panel.style.display = 'none';
                icon.style.transform = 'rotate(0deg)';
            }
        }

        // Raw Data Stream Functions
        let rawStreamActive = false;
        let rawStreamInterval = null;
        let rawStreamRecordCount = 0;
        const MAX_STREAM_RECORDS = 200;  // Keep last 200 records

        async function toggleRawStream() {
            const button = document.getElementById('raw-stream-toggle');
            const container = document.getElementById('raw-stream-content');

            if (rawStreamActive) {
                // Stop streaming
                rawStreamActive = false;
                if (rawStreamInterval) {
                    clearInterval(rawStreamInterval);
                    rawStreamInterval = null;
                }
                button.textContent = 'Start Stream';
                button.className = 'btn btn-start';
            } else {
                // Start streaming
                rawStreamActive = true;
                rawStreamRecordCount = 0;
                button.textContent = 'Stop Stream';
                button.className = 'btn btn-stop';
                container.innerHTML = '<div style="color: #10B981; text-align: center; padding: 16px;">⏳ Loading data...</div>';

                // Initial load
                await updateRawStream();

                // Update every 2 seconds
                rawStreamInterval = setInterval(updateRawStream, 2000);
            }
        }

        async function updateRawStream() {
            const protocolFilter = document.getElementById('raw-protocol-filter').value;
            const industryFilter = document.getElementById('raw-industry-filter').value;
            const container = document.getElementById('raw-stream-content');
            const countElement = document.getElementById('raw-record-count');
            const streamContainer = document.getElementById('raw-stream-container');

            try {
                // Build query string
                const params = new URLSearchParams();
                if (protocolFilter) params.append('protocol', protocolFilter);
                if (industryFilter) params.append('industry', industryFilter);
                params.append('limit', '20');

                const response = await fetch(`/api/raw-data-stream?${params.toString()}`);
                const result = await response.json();

                if (result.success && result.data && result.data.length > 0) {
                    // Check if user is scrolled to top (within 50px)
                    const isScrolledToTop = streamContainer.scrollTop < 50;

                    // Format new data
                    let output = '';
                    result.data.forEach((record) => {
                        const timestamp = new Date(record.timestamp).toLocaleTimeString();
                        output += `<div class="stream-record stream-record-new" style="margin-bottom: 12px; padding: 12px; background: #2D2D2D; border-left: 3px solid ${getProtocolColor(record.protocol)}; border-radius: 4px; width: 100%; box-sizing: border-box;">`;
                        output += `<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">`;
                        output += `<span style="color: ${getProtocolColor(record.protocol)}; font-weight: 600;">${record.protocol.toUpperCase()}</span>`;
                        output += `<span style="color: #9CA3AF; font-size: 11px;">${timestamp}</span>`;
                        output += `</div>`;
                        output += `<div style="color: #10B981; font-size: 13px; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">`;
                        output += `${record.industry}/${record.sensor_name}`;
                        output += `</div>`;
                        output += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">`;
                        output += `<span style="color: #6B7280;">Value:</span>`;
                        output += `<span style="color: #00A9E0; font-weight: 600; overflow: hidden; text-overflow: ellipsis;">${typeof record.value === 'number' ? record.value.toFixed(2) : record.value} ${record.unit || ''}</span>`;
                        output += `<span style="color: #6B7280;">Type:</span>`;
                        output += `<span style="color: #D4D4D4; overflow: hidden; text-overflow: ellipsis;">${record.sensor_type || 'N/A'}</span>`;
                        if (record.plc_name) {
                            output += `<span style="color: #6B7280;">PLC:</span>`;
                            output += `<span style="color: #D4D4D4; overflow: hidden; text-overflow: ellipsis;">${record.plc_name}</span>`;
                        }
                        // Protocol-specific fields
                        if (record.protocol === 'opcua' && record.node_id) {
                            output += `<span style="color: #6B7280;">Node ID:</span>`;
                            output += `<span style="color: #D4D4D4; font-family: monospace; font-size: 11px; overflow: hidden; text-overflow: ellipsis;">${record.node_id}</span>`;
                        } else if (record.protocol === 'mqtt' && record.topic) {
                            output += `<span style="color: #6B7280;">Topic:</span>`;
                            output += `<span style="color: #D4D4D4; font-family: monospace; font-size: 11px; overflow: hidden; text-overflow: ellipsis;">${record.topic}</span>`;
                        } else if (record.protocol === 'modbus' && record.register_address !== undefined) {
                            output += `<span style="color: #6B7280;">Register:</span>`;
                            output += `<span style="color: #D4D4D4; overflow: hidden; text-overflow: ellipsis;">${record.register_address} (${record.register_type})</span>`;
                        }
                        output += `</div></div>`;
                    });

                    // Prepend new records to the top
                    container.insertAdjacentHTML('afterbegin', output);

                    // Remove animation class after animation completes to allow re-triggering
                    setTimeout(() => {
                        const newRecords = container.querySelectorAll('.stream-record-new');
                        newRecords.forEach(record => record.classList.remove('stream-record-new'));
                    }, 400);
                    rawStreamRecordCount += result.data.length;

                    // Trim old records from the bottom if we exceed MAX_STREAM_RECORDS
                    const records = container.querySelectorAll('.stream-record');
                    if (records.length > MAX_STREAM_RECORDS) {
                        const toRemove = records.length - MAX_STREAM_RECORDS;
                        // Remove from the end (oldest records)
                        for (let i = records.length - 1; i >= records.length - toRemove; i--) {
                            records[i].remove();
                        }
                        rawStreamRecordCount = MAX_STREAM_RECORDS;
                    }

                    countElement.textContent = rawStreamRecordCount;

                    // Auto-scroll to top only if user was already at top
                    if (isScrolledToTop) {
                        streamContainer.scrollTop = 0;
                    }
                } else if (!container.querySelector('.stream-record')) {
                    container.innerHTML = '<div style="color: #6B7280; text-align: center; padding: 32px;">No data available. Start a protocol simulator first.</div>';
                    countElement.textContent = '0';
                }
            } catch (error) {
                console.error('Error fetching raw stream data:', error);
                if (!container.querySelector('.stream-record')) {
                    container.innerHTML = `<div style="color: #EF4444; text-align: center; padding: 32px;">Error: ${error.message}</div>`;
                }
            }
        }

        function clearRawStream() {
            const container = document.getElementById('raw-stream-content');
            container.innerHTML = '<div style="color: #6B7280; text-align: center; padding: 32px;">Stream cleared. Click "Start Stream" to continue.</div>';
            rawStreamRecordCount = 0;
            document.getElementById('raw-record-count').textContent = '0';
        }

        function getProtocolColor(protocol) {
            const colors = {
                'opcua': '#00A9E0',
                'mqtt': '#10B981',
                'modbus': '#8B5CF6'
            };
            return colors[protocol] || '#6B7280';
        }

        async function saveZeroBusConfig(protocol) {
            console.log(`saveZeroBusConfig called for protocol: ${protocol}`);

            const diagnostics = document.getElementById(`${protocol}-diagnostics`);
            if (!diagnostics) {
                console.error(`Diagnostics element not found: ${protocol}-diagnostics`);
                alert(`Error: Diagnostics panel not found for ${protocol}`);
                return;
            }

            diagnostics.innerHTML = '<div class="info">⏳ Saving configuration...</div>';

            try {
                // Parse target table (format: catalog.schema.table)
                const targetField = document.getElementById(`${protocol}-target`);
                const targetParts = targetField ? targetField.value.trim().split('.') : [];

                // Get selected sensors (if any were chosen via the modal)
                const selectedSensors = window[`${protocol}_selected_sensors`] || [];

                const config = {
                    workspace_host: document.getElementById(`${protocol}-workspace`).value.trim(),
                    zerobus_endpoint: document.getElementById(`${protocol}-zerobus`).value.trim(),
                    auth: {
                        client_id: document.getElementById(`${protocol}-client-id`).value.trim(),
                        client_secret: document.getElementById(`${protocol}-client-secret`).value.trim()
                    },
                    target: {
                        catalog: targetParts[0] || '',
                        schema: targetParts[1] || '',
                        table: targetParts[2] || ''
                    },
                    // Include sensor selection (empty array = all sensors)
                    selected_sensors: selectedSensors
                };

                console.log('Config object:', config);

                // Validate required fields
                if (!config.workspace_host || !config.zerobus_endpoint ||
                    !config.target.catalog || !config.target.schema || !config.target.table) {
                    diagnostics.innerHTML = '<div class="error">Please fill in all required fields (workspace, endpoint, and table in format catalog.schema.table)</div>';
                    return;
                }

                console.log('Sending POST to /api/zerobus/config');

                // Send config to backend
                const response = await fetch('/api/zerobus/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        protocol: protocol,
                        config: config
                    })
                });

                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);

                if (data.success) {
                    diagnostics.innerHTML = `<div class="success">Configuration saved successfully for ${protocol.toUpperCase()}<br><small>Config file: ${data.config_file}</small></div>`;
                } else {
                    diagnostics.innerHTML = `<div class="error">Error: ${data.message}${data.detail ? '<br><small>' + data.detail + '</small>' : ''}</div>`;
                }
            } catch (error) {
                console.error('Error saving config:', error);
                diagnostics.innerHTML = `<div class="error">Error saving configuration: ${error.message}</div>`;
            }
        }

        async function testZeroBusConnection(protocol) {
            const diagnostics = document.getElementById(`${protocol}-diagnostics`);
            diagnostics.innerHTML = '<div class="info">Testing Zero-Bus connection...</div>';

            // Parse target table (format: catalog.schema.table)
            const targetField = document.getElementById(`${protocol}-target`);
            const targetParts = targetField ? targetField.value.trim().split('.') : [];

            const config = {
                workspace_host: document.getElementById(`${protocol}-workspace`).value.trim(),
                zerobus_endpoint: document.getElementById(`${protocol}-zerobus`).value.trim(),
                auth: {
                    client_id: document.getElementById(`${protocol}-client-id`).value.trim(),
                    client_secret: document.getElementById(`${protocol}-client-secret`).value.trim()
                },
                target: {
                    catalog: targetParts[0] || '',
                    schema: targetParts[1] || '',
                    table: targetParts[2] || ''
                }
            };

            // Validate required fields
            if (!config.workspace_host || !config.zerobus_endpoint ||
                !config.target.catalog || !config.target.schema || !config.target.table) {
                diagnostics.innerHTML = '<div class="error">Please fill in all required fields (workspace, endpoint, and table in format catalog.schema.table)</div>';
                return;
            }

            try {
                // Send test request to backend
                const response = await fetch('/api/zerobus/test', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        protocol: protocol,
                        config: config
                    })
                });

                const data = await response.json();

                if (data.success) {
                    diagnostics.innerHTML = `<div class="success">Connection successful!<br><strong>Table:</strong> ${data.table_name}<br><strong>Stream ID:</strong> ${data.stream_id}</div>`;
                } else {
                    diagnostics.innerHTML = `<div class="error">Connection failed:<br>${data.message}${data.detail ? '<br><small>' + data.detail + '</small>' : ''}</div>`;
                }
            } catch (error) {
                console.error('Error testing connection:', error);
                diagnostics.innerHTML = `<div class="error">Error testing connection: ${error.message}</div>`;
            }
        }

        async function startZeroBusService(protocol) {
            const btn = document.getElementById(`${protocol}-zerobus-btn`);
            const diagnostics = document.getElementById(`${protocol}-diagnostics`);

            // Check if already streaming (button shows "Stop Streaming")
            const isStreaming = btn.textContent.includes('Stop');

            if (isStreaming) {
                // Stop streaming
                btn.disabled = true;
                btn.textContent = '⏸ Stopping...';

                try {
                    const response = await fetch('/api/zerobus/stop', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ protocol: protocol })
                    });

                    const result = await response.json();

                    if (result.success) {
                        btn.textContent = '▶️ Start Streaming';
                        btn.className = 'btn-start-zerobus';
                        diagnostics.innerHTML = `<div class="success">${result.message}</div>`;
                    } else {
                        diagnostics.innerHTML = `<div class="error">${result.message}</div>`;
                        btn.textContent = '⏹ Stop Streaming';
                        btn.className = 'btn-stop-zerobus';
                    }
                } catch (error) {
                    diagnostics.innerHTML = `<div class="error">Error stopping stream: ${error.message}</div>`;
                    btn.textContent = '⏹ Stop Streaming';
                    btn.className = 'btn-stop-zerobus';
                } finally {
                    btn.disabled = false;
                }
            } else {
                // Start streaming
                btn.disabled = true;
                btn.textContent = '⏳ Starting...';

                try {
                    const response = await fetch('/api/zerobus/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ protocol: protocol })
                    });

                    const result = await response.json();

                    if (result.success) {
                        btn.textContent = '⏹ Stop Streaming';
                        btn.className = 'btn-stop-zerobus';
                        diagnostics.innerHTML = `<div class="success">${result.message}<br>Data is being streamed to Zero-Bus every 5 seconds.</div>`;
                        // Update status periodically
                        updateStreamingStatus(protocol);
                    } else {
                        diagnostics.innerHTML = `<div class="error">${result.message}</div>`;
                        btn.textContent = '▶️ Start Streaming';
                        btn.className = 'btn-start-zerobus';
                    }
                } catch (error) {
                    diagnostics.innerHTML = `<div class="error">Error starting stream: ${error.message}</div>`;
                    btn.textContent = '▶️ Start Streaming';
                    btn.className = 'btn-start-zerobus';
                } finally {
                    btn.disabled = false;
                }
            }
        }

        function updateStreamingStatus(protocol) {
            // Periodically check streaming status
            const interval = setInterval(async () => {
                const btn = document.getElementById(`${protocol}-zerobus-btn`);
                if (!btn || !btn.textContent.includes('Stop')) {
                    clearInterval(interval);
                    return;
                }

                try {
                    const response = await fetch('/api/zerobus/status');
                    const result = await response.json();

                    if (result.success && result.status[protocol]) {
                        if (!result.status[protocol].active) {
                            // Streaming stopped externally
                            btn.textContent = '▶️ Start Streaming';
                            btn.className = 'btn-start-zerobus';
                            clearInterval(interval);
                        }
                    }
                } catch (error) {
                    console.error('Error checking streaming status:', error);
                }
            }, 5000);
        }

        // Load saved Zero-Bus configuration for a protocol
        async function loadZeroBusConfig(protocol) {
            try {
                const response = await fetch('/api/zerobus/config/load', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ protocol: protocol })
                });

                const result = await response.json();

                if (result.success && result.config) {
                    const config = result.config;

                    // Populate form fields
                    const workspaceInput = document.getElementById(`${protocol}-workspace`);
                    const zerobusInput = document.getElementById(`${protocol}-zerobus`);
                    const clientIdInput = document.getElementById(`${protocol}-client-id`);
                    const clientSecretInput = document.getElementById(`${protocol}-client-secret`);
                    const targetInput = document.getElementById(`${protocol}-target`);

                    if (workspaceInput && config.workspace_host) {
                        workspaceInput.value = config.workspace_host;
                    }

                    if (zerobusInput && config.zerobus_endpoint) {
                        zerobusInput.value = config.zerobus_endpoint;
                    }

                    if (clientIdInput && config.auth) {
                        // Display the actual client ID (stored encrypted on server)
                        if (config.auth.client_id) {
                            clientIdInput.value = config.auth.client_id;
                        }
                    }

                    if (clientSecretInput && config.auth) {
                        // Display the actual client secret (stored encrypted on server)
                        if (config.auth.client_secret) {
                            clientSecretInput.value = config.auth.client_secret;
                        }
                    }

                    if (targetInput && config.target) {
                        // Reconstruct the target table from catalog.schema.table
                        const catalog = config.target.catalog || '';
                        const schema = config.target.schema || '';
                        const table = config.target.table || '';
                        if (catalog && schema && table) {
                            targetInput.value = `${catalog}.${schema}.${table}`;
                        }
                    }

                    console.log(`Loaded saved configuration for ${protocol}`);
                } else {
                    console.log(`ℹ️ No saved configuration found for ${protocol}`);
                }
            } catch (error) {
                console.error(`Error loading configuration for ${protocol}:`, error);
            }
        }

        // Natural Language Chat
        const chatToggle = document.getElementById('nlp-chat-toggle');
        const chatPanel = document.getElementById('nlp-chat-panel');
        const chatClose = document.getElementById('chat-close');
        const chatMessages = document.getElementById('chat-messages');
        const chatInput = document.getElementById('chat-input');
        const chatSend = document.getElementById('chat-send');

        chatToggle.addEventListener('click', () => {
            chatPanel.classList.remove('hidden');
            chatInput.focus();
        });

        chatClose.addEventListener('click', () => {
            chatPanel.classList.add('hidden');
        });

        function addMessage(role, content, reasoning = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;

            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = role === 'user' ? '' : '️';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            // Use innerText instead of textContent to preserve line breaks
            bubble.style.whiteSpace = 'pre-wrap';
            bubble.textContent = content;

            contentDiv.appendChild(bubble);

            if (reasoning && role === 'agent') {
                const reasoningDiv = document.createElement('div');
                reasoningDiv.className = 'message-reasoning';
                reasoningDiv.textContent = `${reasoning}`;
                contentDiv.appendChild(reasoningDiv);
            }

            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);

            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function addTypingIndicator() {
            const indicatorDiv = document.createElement('div');
            indicatorDiv.className = 'message agent';
            indicatorDiv.id = 'typing-indicator';

            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = '️';

            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

            indicatorDiv.appendChild(avatar);
            indicatorDiv.appendChild(typingDiv);

            chatMessages.appendChild(indicatorDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function removeTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) {
                indicator.remove();
            }
        }

        function sendMessage() {
            const text = chatInput.value.trim();
            if (!text) return;

            console.log('Sending NLP command:', text);

            // Display user message
            addMessage('user', text);
            chatInput.value = '';

            // Add to conversation history
            conversationHistory.push({
                role: 'user',
                content: text
            });

            // Send to WebSocket
            if (ws && ws.readyState === WebSocket.OPEN) {
                const message = {
                    type: 'nlp_command',
                    text: text,
                    history: conversationHistory.slice(-10)  // Last 10 messages
                };
                console.log('WebSocket sending:', message);
                ws.send(JSON.stringify(message));

                // Show typing indicator
                addTypingIndicator();
            } else {
                console.error('WebSocket not connected, state:', ws?.readyState);
                addMessage('agent', 'WebSocket connection not available. Please refresh the page.');
            }
        }

        chatSend.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Load sensors
        async function loadSensors() {
            try {
                const response = await fetch('/api/sensors');
                const industries = await response.json();

                const sensorBrowser = document.getElementById('sensor-browser');
                sensorBrowser.innerHTML = '';

                // Render each industry accordion
                Object.values(industries).forEach(industry => {
                    const accordionDiv = document.createElement('div');
                    accordionDiv.className = 'industry-accordion';

                    // Industry header
                    const headerDiv = document.createElement('div');
                    headerDiv.className = 'industry-header';
                    headerDiv.innerHTML = `
                        <div class="industry-header-left">
                            <span class="industry-title">${industry.display_name}</span>
                            <span class="industry-count">${industry.sensor_count} sensors</span>
                        </div>
                        <span class="industry-chevron">▶</span>
                    `;

                    // Sensors container
                    const sensorsDiv = document.createElement('div');
                    sensorsDiv.className = 'industry-sensors';

                    // Render sensors
                    industry.sensors.forEach(sensor => {
                        const sensorItem = document.createElement('div');
                        sensorItem.className = 'sensor-item';

                        // Protocol badges HTML
                        const protocolBadgesHTML = sensor.protocols.map(proto =>
                            `<span class="protocol-badge-mini ${proto}">${proto}</span>`
                        ).join('');

                        sensorItem.innerHTML = `
                            <div class="sensor-info">
                                <div class="sensor-name">${sensor.name}</div>
                                <div class="sensor-meta">
                                    <span class="sensor-type">${sensor.type}</span>
                                    <div class="protocol-badges">
                                        ${protocolBadgesHTML}
                                    </div>
                                </div>
                            </div>
                            <span class="sensor-add">+</span>
                        `;

                        sensorItem.onclick = (event) => {
                            // Check for Ctrl/Cmd key for multi-selection
                            if (event.ctrlKey || event.metaKey) {
                                event.stopPropagation();
                                toggleSensorSelection(sensor.path, sensor, sensorItem);
                            } else {
                                // Normal single chart creation
                                if (!charts[sensor.path]) {
                                    createChart(sensor.path, sensor);
                                }
                            }
                        };

                        sensorsDiv.appendChild(sensorItem);
                    });

                    // Toggle accordion
                    headerDiv.onclick = () => {
                        const isExpanded = sensorsDiv.classList.contains('expanded');
                        const chevron = headerDiv.querySelector('.industry-chevron');

                        if (isExpanded) {
                            sensorsDiv.classList.remove('expanded');
                            headerDiv.classList.remove('active');
                            chevron.classList.remove('expanded');
                        } else {
                            sensorsDiv.classList.add('expanded');
                            headerDiv.classList.add('active');
                            chevron.classList.add('expanded');
                        }
                    };

                    accordionDiv.appendChild(headerDiv);
                    accordionDiv.appendChild(sensorsDiv);
                    sensorBrowser.appendChild(accordionDiv);
                });
            } catch (error) {
                console.error('Error loading sensors:', error);
            }
        }

        // Initialize Zero-Bus streaming button states
        async function initZeroBusButtons() {
            try {
                const response = await fetch('/api/zerobus/status');
                const result = await response.json();

                if (result.success && result.status) {
                    // Update button states for each protocol
                    ['opcua', 'mqtt', 'modbus'].forEach(protocol => {
                        const status = result.status[protocol];
                        const btn = document.getElementById(`${protocol}-zerobus-btn`);

                        if (btn && status) {
                            if (status.active) {
                                // Streaming is active
                                btn.textContent = '⏹ Stop Streaming';
                                btn.className = 'btn-stop-zerobus';
                                // Start periodic status updates
                                updateStreamingStatus(protocol);
                            } else {
                                // Streaming is not active
                                btn.textContent = '▶️ Start Streaming';
                                btn.className = 'btn-start-zerobus';
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('Error initializing ZeroBus button states:', error);
            }
        }

        // Initialize
        connectWebSocket();
        loadSensors();

        // Load saved Zero-Bus configurations for all protocols
        loadZeroBusConfig('opcua');
        loadZeroBusConfig('mqtt');
        loadZeroBusConfig('modbus');

        // Initialize ZeroBus button states based on current streaming status
        initZeroBusButtons();

        // Add some default charts
        setTimeout(() => {
            // These will be created once sensors are loaded
            const defaultSensors = [
                'mining/crusher_1_motor_power',
                'utilities/grid_main_frequency'
            ];
            // Will auto-create once sensor data is available
        }, 1000);

        // OPC-UA Browser functionality
        const opcuaBrowserPanel = document.getElementById('opcua-browser-panel');
        const opcuaBrowserClose = document.getElementById('opcua-browser-close');
        const opcuaTreeContainer = document.getElementById('opcua-tree-container');
        const opcuaSearchInput = document.getElementById('opcua-search-input');

        let opcuaHierarchyData = null;
        let opcuaUpdateInterval = null;

        // Global function to toggle OPC-UA browser panel (called from header button)
        window.toggleOPCUABrowser = function() {
            opcuaBrowserPanel.classList.remove('hidden');
            if (!opcuaHierarchyData) {
                loadOpcuaHierarchy();
            }
            // Start auto-refresh (500ms for smoother updates)
            if (!opcuaUpdateInterval) {
                opcuaUpdateInterval = setInterval(updateOpcuaValues, 500);
            }
        };

        opcuaBrowserClose.addEventListener('click', () => {
            opcuaBrowserPanel.classList.add('hidden');
            // Stop auto-refresh when closed
            if (opcuaUpdateInterval) {
                clearInterval(opcuaUpdateInterval);
                opcuaUpdateInterval = null;
            }
        });

        // Auto-close floating panels when user clicks on config inputs
        // This prevents panels from overlapping Zero-Bus config forms
        document.addEventListener('focusin', (e) => {
            const target = e.target;
            // Check if the focused element is an input or textarea in a config section
            if ((target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') &&
                target.closest('.config-section, .zerobus-section')) {
                // Close OPC-UA browser
                opcuaBrowserPanel.classList.add('hidden');
                if (opcuaUpdateInterval) {
                    clearInterval(opcuaUpdateInterval);
                    opcuaUpdateInterval = null;
                }
                // Close NLP chat
                chatPanel.classList.add('hidden');
            }
        });

        // Search functionality with fuzzy matching
        opcuaSearchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            filterOpcuaTree(searchTerm);
        });

        // Fuzzy search aliases - common full words map to abbreviations
        const searchAliases = {
            'temperature': 'temp',
            'pressure': 'press',
            'vibration': 'vib',
            'position': 'pos',
            'current': 'curr',
            'voltage': 'volt',
            'frequency': 'freq',
            'humidity': 'hum',
            'conveyor': 'conv'
        };

        function expandSearchTerm(term) {
            // Check if the search term matches any alias
            const lowerTerm = term.toLowerCase();
            for (const [fullWord, abbrev] of Object.entries(searchAliases)) {
                if (lowerTerm.includes(fullWord)) {
                    // Return both the original and abbreviated version
                    return [term, term.replace(new RegExp(fullWord, 'gi'), abbrev)];
                }
            }
            return [term];
        }

        function filterOpcuaTree(searchTerm) {
            const allNodes = document.querySelectorAll('.tree-node');
            const allContainers = document.querySelectorAll('.tree-children');
            const allHeaders = document.querySelectorAll('.tree-node-header');

            if (!searchTerm) {
                // Show all nodes and reset expansion
                allNodes.forEach(node => node.style.display = '');
                allContainers.forEach(container => container.style.display = '');
                allHeaders.forEach(header => header.style.display = '');
                return;
            }

            // First, hide everything
            allNodes.forEach(node => node.style.display = 'none');

            // Expand search term to include aliases
            const searchTerms = expandSearchTerm(searchTerm);

            // Find all matching nodes
            const matchingNodes = [];
            allNodes.forEach(node => {
                const header = node.querySelector('.tree-node-header');
                const label = header ? header.querySelector('.tree-label') : null;
                const labelText = label ? label.textContent.toLowerCase() : '';

                // Check if any of the search terms match
                const matches = searchTerms.some(term => labelText.includes(term.toLowerCase()));

                if (matches) {
                    matchingNodes.push(node);
                    // Show this node
                    node.style.display = '';

                    // Show and expand all parent nodes
                    let parent = node.parentElement;
                    while (parent) {
                        if (parent.classList.contains('tree-children')) {
                            parent.style.display = '';
                            parent.classList.add('expanded');

                            // Find and show the parent node
                            const parentNode = parent.closest('.tree-node');
                            if (parentNode) {
                                parentNode.style.display = '';
                            }

                            // Expand the header
                            const header = parent.previousElementSibling;
                            if (header && header.classList.contains('tree-node-header')) {
                                header.style.display = '';
                                header.classList.add('active');
                                const chevron = header.querySelector('.tree-chevron');
                                if (chevron) chevron.classList.add('expanded');
                            }
                        }
                        parent = parent.parentElement;
                    }
                }
            });

            console.log(`Search "${searchTerm}" found ${matchingNodes.length} matches`);
        }

        async function loadOpcuaHierarchy() {
            try {
                opcuaTreeContainer.innerHTML = '<div style="text-align: center; padding: 40px; color: #6B7280;">Loading OPC-UA hierarchy...</div>';

                const response = await fetch('/api/opcua/hierarchy');
                opcuaHierarchyData = await response.json();

                renderOpcuaTree();
            } catch (error) {
                console.error('Error loading OPC-UA hierarchy:', error);
                opcuaTreeContainer.innerHTML = '<div style="text-align: center; padding: 40px; color: #DC2626;">Failed to load hierarchy. Please try again.</div>';
            }
        }

        async function updateOpcuaValues() {
            // Fetch fresh data and update only the values
            try {
                const response = await fetch('/api/opcua/hierarchy');
                const newData = await response.json();
                updateNodeValues(newData);
            } catch (error) {
                console.error('Error updating OPC-UA values:', error);
            }
        }

        function updateNodeValues(data) {
            // Update sensor values without re-rendering entire tree
            const updateNode = (node) => {
                if (node.type === 'sensor' && node.path) {
                    const valueElement = document.querySelector(`[data-sensor-path="${node.path}"] .tree-value`);
                    const qualityElement = document.querySelector(`[data-sensor-path="${node.path}"] .tree-quality`);

                    if (valueElement && node.value !== undefined) {
                        const oldValue = valueElement.textContent;
                        const newValue = node.value.toFixed(2);

                        // Only flash if value actually changed
                        if (oldValue !== newValue) {
                            valueElement.textContent = newValue;

                            // Add flash animation
                            valueElement.classList.add('updated');

                            // Remove the class after animation completes
                            setTimeout(() => {
                                valueElement.classList.remove('updated');
                            }, 500);
                        }
                    }

                    if (qualityElement && node.quality) {
                        // Update quality badge
                        qualityElement.className = 'tree-quality';
                        if (node.forced) {
                            qualityElement.classList.add('forced');
                            qualityElement.textContent = 'FORCED';
                        } else if (node.quality.toLowerCase().includes('good')) {
                            qualityElement.classList.add('good');
                            qualityElement.textContent = 'Good';
                        } else if (node.quality.toLowerCase().includes('uncertain')) {
                            qualityElement.classList.add('uncertain');
                            qualityElement.textContent = 'Uncertain';
                        } else if (node.quality.toLowerCase().includes('bad')) {
                            qualityElement.classList.add('bad');
                            qualityElement.textContent = node.quality;
                        }
                    }
                }

                if (node.children) {
                    node.children.forEach(updateNode);
                }
            };

            updateNode(data);
        }

        function renderOpcuaTree() {
            if (!opcuaHierarchyData) return;

            opcuaTreeContainer.innerHTML = '';

            // Render root
            const rootNode = createTreeNode({
                name: opcuaHierarchyData.root,
                type: 'root',
                children: opcuaHierarchyData.children
            }, 0);

            opcuaTreeContainer.appendChild(rootNode);
        }

        function createTreeNode(node, depth) {
            const nodeDiv = document.createElement('div');
            nodeDiv.className = 'tree-node';

            const hasChildren = node.children && node.children.length > 0;
            const hasProperties = node.properties && Object.keys(node.properties).length > 0;

            // Create header
            const header = document.createElement('div');
            header.className = 'tree-node-header';

            // Chevron
            const chevron = document.createElement('span');
            chevron.className = hasChildren || hasProperties ? 'tree-chevron' : 'tree-chevron leaf';
            chevron.textContent = '▶';
            header.appendChild(chevron);

            // Icon based on type
            const icon = document.createElement('span');
            icon.className = 'tree-icon';
            if (node.type === 'root' || node.type === 'folder') {
                icon.textContent = '▸';
            } else if (node.type === 'plc') {
                icon.textContent = '⊙';
            } else if (node.type === 'industry') {
                icon.textContent = '◆';
            } else if (node.type === 'sensor') {
                icon.textContent = '●';
            } else {
                icon.textContent = '○';
            }
            header.appendChild(icon);

            // Label
            const label = document.createElement('span');
            label.className = 'tree-label';
            label.textContent = node.name;
            header.appendChild(label);

            // For sensors, show value and quality
            if (node.type === 'sensor') {
                header.setAttribute('data-sensor-path', node.path);

                const value = document.createElement('span');
                value.className = 'tree-value';
                value.textContent = node.value !== undefined ? node.value.toFixed(2) : '--';
                header.appendChild(value);

                const unit = document.createElement('span');
                unit.className = 'tree-unit';
                unit.textContent = node.unit || '';
                header.appendChild(unit);

                const quality = document.createElement('span');
                quality.className = 'tree-quality';
                if (node.forced) {
                    quality.classList.add('forced');
                    quality.textContent = 'FORCED';
                } else if (node.quality && node.quality.toLowerCase().includes('good')) {
                    quality.classList.add('good');
                    quality.textContent = 'Good';
                } else if (node.quality && node.quality.toLowerCase().includes('uncertain')) {
                    quality.classList.add('uncertain');
                    quality.textContent = 'Uncertain';
                } else if (node.quality && node.quality.toLowerCase().includes('bad')) {
                    quality.classList.add('bad');
                    quality.textContent = node.quality;
                } else {
                    quality.classList.add('good');
                    quality.textContent = 'Good';
                }
                header.appendChild(quality);
            }

            nodeDiv.appendChild(header);

            // Create children container
            if (hasChildren || hasProperties) {
                const childrenDiv = document.createElement('div');
                childrenDiv.className = 'tree-children';

                // Add properties if present
                if (hasProperties) {
                    const propsDiv = document.createElement('div');
                    propsDiv.className = 'tree-properties';

                    Object.entries(node.properties).forEach(([key, value]) => {
                        const propDiv = document.createElement('div');
                        propDiv.className = 'tree-property';

                        const propName = document.createElement('span');
                        propName.className = 'tree-property-name';
                        propName.textContent = key + ':';
                        propDiv.appendChild(propName);

                        const propValue = document.createElement('span');
                        propValue.className = 'tree-property-value';
                        propValue.textContent = value;
                        propDiv.appendChild(propValue);

                        propsDiv.appendChild(propDiv);
                    });

                    childrenDiv.appendChild(propsDiv);
                }

                // Add child nodes
                if (hasChildren) {
                    node.children.forEach(child => {
                        const childNode = createTreeNode(child, depth + 1);
                        childrenDiv.appendChild(childNode);
                    });
                }

                nodeDiv.appendChild(childrenDiv);

                // Toggle functionality
                header.addEventListener('click', () => {
                    const isExpanded = childrenDiv.classList.contains('expanded');

                    if (isExpanded) {
                        childrenDiv.classList.remove('expanded');
                        header.classList.remove('active');
                        chevron.classList.remove('expanded');
                    } else {
                        childrenDiv.classList.add('expanded');
                        header.classList.add('active');
                        chevron.classList.add('expanded');
                    }
                });
            }

            return nodeDiv;
        }

        // ==================== Sensor Selection ====================
        let sensorSelectionState = {
            currentProtocol: null,
            allSensors: [],
            selectedSensors: new Set(),
            // Filters track which items are ENABLED (checked = show, unchecked = hide)
            enabledFilters: {
                industries: new Set(),  // Empty = all enabled
                sensorTypes: new Set(), // Empty = all enabled
                plcs: new Set()         // Empty = all enabled
            }
        };

        async function openSensorSelector(protocol) {
            sensorSelectionState.currentProtocol = protocol;
            document.getElementById('sensor-modal-protocol').textContent = protocol.toUpperCase();

            // Load sensors from API
            try {
                const response = await fetch('/api/sensors');
                const industries = await response.json();

                // Flatten sensors from all industries
                sensorSelectionState.allSensors = [];
                for (const industryName in industries) {
                    const industry = industries[industryName];
                    industry.sensors.forEach(sensor => {
                        sensor.industryDisplay = industry.display_name;
                        // Use actual PLC vendor and model if available
                        if (sensor.plc_vendor && sensor.plc_model) {
                            sensor.plc = `${sensor.plc_vendor} ${sensor.plc_model}`;
                        } else {
                            sensor.plc = 'Unknown PLC';
                        }
                        sensorSelectionState.allSensors.push(sensor);
                    });
                }

                // Initialize with NO sensors selected (empty set)
                sensorSelectionState.selectedSensors = new Set();

                // Build filter options
                buildFilterOptions();

                // Render sensor list
                renderSensorList();

                // Show modal
                document.getElementById('sensor-modal').classList.add('active');
            } catch (error) {
                console.error('Error loading sensors:', error);
                alert('Failed to load sensors');
            }
        }

        function closeSensorSelector() {
            document.getElementById('sensor-modal').classList.remove('active');
        }

        function buildFilterOptions() {
            const industries = new Set();
            const sensorTypes = new Set();
            const plcs = new Set();

            sensorSelectionState.allSensors.forEach(sensor => {
                industries.add(sensor.industryDisplay);
                sensorTypes.add(sensor.type);
                plcs.add(sensor.plc);
            });

            // Initialize enabledFilters as empty (checkboxes start unchecked)
            sensorSelectionState.enabledFilters.industries = new Set();
            sensorSelectionState.enabledFilters.sensorTypes = new Set();
            sensorSelectionState.enabledFilters.plcs = new Set();

            // Industry filters
            const industryContainer = document.getElementById('industry-filter-options');
            industryContainer.innerHTML = '';
            Array.from(industries).sort().forEach(industry => {
                const option = createFilterOption('industry', industry);
                industryContainer.appendChild(option);
            });

            // Sensor type filters
            const typeContainer = document.getElementById('sensor-type-filter-options');
            typeContainer.innerHTML = '';
            Array.from(sensorTypes).sort().forEach(type => {
                const option = createFilterOption('type', type);
                typeContainer.appendChild(option);
            });

            // PLC filters
            const plcContainer = document.getElementById('plc-filter-options');
            plcContainer.innerHTML = '';
            Array.from(plcs).sort().forEach(plc => {
                // PLC names are already formatted (e.g., "rockwell ControlLogix 5580")
                const option = createFilterOption('plc', plc);
                plcContainer.appendChild(option);
            });
        }

        function createFilterOption(filterType, displayName, value = null) {
            const actualValue = value || displayName;
            const div = document.createElement('div');
            div.className = 'sensor-filter-option';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = false;
            checkbox.id = `filter-${filterType}-${actualValue}`;
            checkbox.onchange = () => handleFilterChange(filterType, actualValue, checkbox.checked);

            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.textContent = displayName;

            div.appendChild(checkbox);
            div.appendChild(label);

            return div;
        }

        function handleFilterChange(filterType, value, checked) {
            // CORRECTED LOGIC: Checked = add to enabledFilters (show), Unchecked = remove (hide)
            if (filterType === 'industry') {
                if (checked) {
                    sensorSelectionState.enabledFilters.industries.add(value);
                } else {
                    sensorSelectionState.enabledFilters.industries.delete(value);
                }
            } else if (filterType === 'type') {
                if (checked) {
                    sensorSelectionState.enabledFilters.sensorTypes.add(value);
                } else {
                    sensorSelectionState.enabledFilters.sensorTypes.delete(value);
                }
            } else if (filterType === 'plc') {
                if (checked) {
                    sensorSelectionState.enabledFilters.plcs.add(value);
                } else {
                    sensorSelectionState.enabledFilters.plcs.delete(value);
                }
            }

            renderSensorList();
        }

        function getFilteredSensors() {
            return sensorSelectionState.allSensors.filter(sensor => {
                // CORRECTED LOGIC: Empty set = show all, otherwise check if item IS IN enabledFilters

                // Industry filter: if set is not empty, sensor must be in the enabled set
                if (sensorSelectionState.enabledFilters.industries.size > 0 &&
                    !sensorSelectionState.enabledFilters.industries.has(sensor.industryDisplay)) {
                    return false;
                }

                // Sensor type filter
                if (sensorSelectionState.enabledFilters.sensorTypes.size > 0 &&
                    !sensorSelectionState.enabledFilters.sensorTypes.has(sensor.type)) {
                    return false;
                }

                // PLC filter
                if (sensorSelectionState.enabledFilters.plcs.size > 0 &&
                    !sensorSelectionState.enabledFilters.plcs.has(sensor.plc)) {
                    return false;
                }

                return true;
            });
        }

        function renderSensorList() {
            const filteredSensors = getFilteredSensors();
            const container = document.getElementById('sensor-items-grid');
            container.innerHTML = '';

            filteredSensors.forEach(sensor => {
                const item = createSensorItem(sensor);
                container.appendChild(item);
            });

            // Update counts
            document.getElementById('filtered-sensor-count').textContent = filteredSensors.length;
            updateSelectedCount();
        }

        function createSensorItem(sensor) {
            const div = document.createElement('div');
            div.className = 'sensor-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = sensorSelectionState.selectedSensors.has(sensor.path);
            checkbox.id = `sensor-${sensor.path.replace(/[\\/\\.]/g, '-')}`;
            checkbox.onchange = () => handleSensorSelection(sensor.path, checkbox.checked);

            const label = document.createElement('label');
            label.className = 'sensor-item-label';
            label.htmlFor = checkbox.id;
            label.textContent = sensor.name;

            const badge = document.createElement('span');
            badge.className = 'sensor-item-badge';
            badge.textContent = sensor.unit;

            div.appendChild(checkbox);
            div.appendChild(label);
            div.appendChild(badge);

            return div;
        }

        function handleSensorSelection(sensorPath, selected) {
            if (selected) {
                sensorSelectionState.selectedSensors.add(sensorPath);
            } else {
                sensorSelectionState.selectedSensors.delete(sensorPath);
            }
            updateSelectedCount();
        }

        function updateSelectedCount() {
            document.getElementById('selected-sensor-count').textContent =
                sensorSelectionState.selectedSensors.size;
        }

        function selectAllFilteredSensors() {
            const filteredSensors = getFilteredSensors();
            filteredSensors.forEach(sensor => {
                sensorSelectionState.selectedSensors.add(sensor.path);
            });
            renderSensorList();
        }

        function clearAllSensors() {
            sensorSelectionState.selectedSensors.clear();
            renderSensorList();
        }

        function applySensorSelection() {
            const protocol = sensorSelectionState.currentProtocol;
            const selectedCount = sensorSelectionState.selectedSensors.size;
            const totalCount = sensorSelectionState.allSensors.length;

            // Update summary text
            const summaryDiv = document.getElementById(`${protocol}-sensor-summary`);
            if (selectedCount === 0) {
                summaryDiv.textContent = 'No sensors selected';
                summaryDiv.style.color = '#EF4444';
            } else if (selectedCount === totalCount) {
                summaryDiv.textContent = `All sensors selected (${totalCount} total)`;
                summaryDiv.style.color = '#6B7280';
            } else {
                summaryDiv.textContent = `${selectedCount} of ${totalCount} sensors selected`;
                summaryDiv.style.color = '#059669';
            }

            // Store selection for later use (when starting Zero-Bus streaming)
            window[`${protocol}_selected_sensors`] = Array.from(sensorSelectionState.selectedSensors);

            closeSensorSelector();
        }

        // Close modal on background click
        document.getElementById('sensor-modal').addEventListener('click', (e) => {
            if (e.target.id === 'sensor-modal') {
                closeSensorSelector();
            }
        });

        // ==================== VENDOR MODE JAVASCRIPT ====================

        // Tab switching
        function switchTab(tabName) {
            // Remove active class from all tabs and content
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            // Add active class to selected tab and content
            document.getElementById('tab-' + tabName).classList.add('active');
            document.getElementById('content-' + tabName).classList.add('active');

            // If switching to modes tab, refresh mode data
            if (tabName === 'modes') {
                refreshVendorModes();
            }

            // If switching to connections tab, load connection info
            if (tabName === 'connections') {
                loadConnectionInfo();
            }
        }

        // Current selected mode
        let currentSelectedMode = null;

        // Select a mode panel
        function selectMode(modeName) {
            currentSelectedMode = modeName;

            // Remove active class from all mode cards and panels
            document.querySelectorAll('.mode-card').forEach(card => card.classList.remove('active'));
            document.querySelectorAll('.mode-panel').forEach(panel => panel.classList.remove('active'));

            // Add active class to selected mode
            const card = document.getElementById('mode-card-' + modeName);
            const panel = document.getElementById('panel-' + modeName);

            if (card) card.classList.add('active');
            if (panel) {
                panel.classList.add('active');
                // Refresh data for this specific mode
                refreshModePanel(modeName);
            }
        }

        // Toggle mode on/off
        async function toggleMode(modeName) {
            try {
                // Get current state
                const toggleButton = document.getElementById(`toggle-${modeName}`);
                const currentlyEnabled = toggleButton.classList.contains('enabled');
                const newState = !currentlyEnabled;

                const response = await fetch(`/api/modes/${modeName}/toggle`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ enabled: newState })
                });

                if (!response.ok) {
                    console.error('Failed to toggle mode:', modeName);
                    return;
                }

                const data = await response.json();
                console.log('Mode toggled:', modeName, data);

                // Refresh mode data
                await refreshVendorModes();

            } catch (error) {
                console.error('Error toggling mode:', error);
            }
        }

        // Toggle protocol (OPC UA or MQTT) for a vendor mode
        async function toggleProtocol(modeName, protocol) {
            try {
                // Get current state
                const toggleButton = document.getElementById(`toggle-${modeName}-${protocol}`);
                const currentlyEnabled = toggleButton.classList.contains('enabled');
                const newState = !currentlyEnabled;

                const response = await fetch(`/api/modes/${modeName}/protocol/toggle`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ protocol: protocol, enabled: newState })
                });

                if (!response.ok) {
                    console.error(`Failed to toggle ${protocol} for ${modeName}`);
                    return;
                }

                const data = await response.json();
                console.log('Protocol toggled:', modeName, protocol, data);

                // Update button state
                if (newState) {
                    toggleButton.classList.add('enabled');
                } else {
                    toggleButton.classList.remove('enabled');
                }

            } catch (error) {
                console.error('Error toggling protocol:', error);
            }
        }

        // Refresh all vendor modes status
        async function refreshVendorModes() {
            try {
                const response = await fetch('/api/modes');
                if (!response.ok) {
                    console.error('Failed to fetch modes');
                    return;
                }

                const data = await response.json();
                const modes = data.modes || [];

                // Update each mode card
                for (const modeData of modes) {
                    const modeName = modeData.mode_type;
                    updateModeCard(modeName, modeData);
                }

                // If a mode panel is selected, refresh it
                if (currentSelectedMode) {
                    refreshModePanel(currentSelectedMode);
                }

            } catch (error) {
                console.error('Error refreshing vendor modes:', error);
            }
        }

        // Update mode card UI
        function updateModeCard(modeName, modeData) {
            const enabled = modeData.enabled || false;

            // Update toggle button
            const toggle = document.getElementById('toggle-' + modeName);
            if (toggle) {
                if (enabled) {
                    toggle.classList.add('enabled');
                } else {
                    toggle.classList.remove('enabled');
                }
            }

            // Update badge
            const badge = document.getElementById('badge-' + modeName);
            if (badge) {
                badge.textContent = enabled ? 'Enabled' : 'Disabled';
                badge.classList.toggle('enabled', enabled);
                badge.classList.toggle('disabled', !enabled);
            }

            // Update card state
            const card = document.getElementById('mode-card-' + modeName);
            if (card) {
                card.classList.toggle('disabled', !enabled);
            }

            // Update protocol toggle buttons
            const config = modeData.config || {};
            const opcuaToggle = document.getElementById(`toggle-${modeName}-opcua`);
            if (opcuaToggle) {
                if (config.opcua_enabled) {
                    opcuaToggle.classList.add('enabled');
                } else {
                    opcuaToggle.classList.remove('enabled');
                }
            }
            const mqttToggle = document.getElementById(`toggle-${modeName}-mqtt`);
            if (mqttToggle) {
                if (config.mqtt_enabled) {
                    mqttToggle.classList.add('enabled');
                } else {
                    mqttToggle.classList.remove('enabled');
                }
            }

            // Update mode-specific stats if available
            const metrics = modeData.metrics || {};
            const diagnostics = modeData.diagnostics || {};

            if (modeName === 'generic') {
                updateElement('stat-generic-messages', metrics.messages_sent || 0);
                updateElement('stat-generic-sensors', metrics.sensors_registered || 0);
                const qualityPct = metrics.quality_good_pct || 0;
                updateElement('stat-generic-quality', qualityPct > 0 ? Math.round(qualityPct) + '%' : '—');
            }
            else if (modeName === 'kepware') {
                updateElement('stat-kepware-channels', diagnostics.total_channels || 0);
                updateElement('stat-kepware-devices', diagnostics.total_devices || 0);
                updateElement('stat-kepware-tags', diagnostics.total_tags || 0);
            }
            else if (modeName === 'sparkplug_b' || modeName === 'sparkplug-b') {
                const diagnostics = modeData.diagnostics || {};
                updateElement('stat-sparkplug-nodes', diagnostics.edge_nodes || 0);
                updateElement('stat-sparkplug-devices', diagnostics.devices || 0);
                updateElement('stat-sparkplug-seq', diagnostics.bdSeq || 0);
            }
            else if (modeName === 'honeywell') {
                const diagnostics = modeData.diagnostics || {};
                updateElement('stat-honeywell-modules', diagnostics.modules || 0);
                updateElement('stat-honeywell-points', diagnostics.points || 0);
                updateElement('stat-honeywell-controllers', diagnostics.controllers || 0);
            }
        }

        // Refresh a specific mode panel
        async function refreshModePanel(modeName) {
            try {
                // Fetch diagnostics
                const diagResponse = await fetch(`/api/modes/${modeName}/diagnostics`);
                if (diagResponse.ok) {
                    const diagnostics = await diagResponse.json();
                    updateModePanelUI(modeName, diagnostics);
                }

                // Fetch status
                const statusResponse = await fetch(`/api/modes/${modeName}`);
                if (statusResponse.ok) {
                    const status = await statusResponse.json();
                    updateModePanelMetrics(modeName, status);
                }

            } catch (error) {
                console.error('Error refreshing mode panel:', error);
            }
        }

        // Update mode panel UI with diagnostics
        function updateModePanelUI(modeName, diagnostics) {
            if (modeName === 'kepware') {
                updateKepwarePanel(diagnostics);
            }
            else if (modeName === 'sparkplug_b' || modeName === 'sparkplug-b') {
                updateSparkplugPanel(diagnostics);
            }
            else if (modeName === 'honeywell') {
                updateHoneywellPanel(diagnostics);
            }
        }

        // Update Kepware panel structure
        function updateKepwarePanel(diagnostics) {
            const container = document.getElementById('kepware-structure');
            if (!container) return;

            const channels = diagnostics.channels || [];
            if (channels.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #6B7280;">No channels configured</div>';
                return;
            }

            let html = '';
            for (const channel of channels) {
                const devices = channel.devices || [];

                html += `
                    <div class="kepware-channel" style="margin-bottom: 24px;">
                        <div class="kepware-channel-header" style="background: #F3F4F6; padding: 12px 16px; border-radius: 8px 8px 0 0; border-bottom: 2px solid #F59E0B;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div class="kepware-channel-name" style="font-size: 16px; font-weight: 600; color: #1F2937;">${escapeHtml(channel.name)}</div>
                                    <div style="font-size: 12px; color: #6B7280; margin-top: 4px;">
                                        <strong>PLC:</strong> ${escapeHtml(channel.plc_vendor)} ${escapeHtml(channel.plc_model)} •
                                        <strong>Driver:</strong> ${escapeHtml(channel.driver_type)}
                                    </div>
                                </div>
                                <div style="text-align: right; font-size: 13px; color: #6B7280;">
                                    <div><strong>${channel.device_count || 0}</strong> devices</div>
                                    <div><strong>${channel.tag_count || 0}</strong> tags</div>
                                </div>
                            </div>
                        </div>

                        <div style="background: white; border: 1px solid #E5E7EB; border-top: none; border-radius: 0 0 8px 8px; overflow: hidden;">
                            <div style="display: grid; grid-template-columns: 2fr 2fr 1fr 1fr; gap: 12px; padding: 10px 16px; background: #FAFAFA; font-weight: 600; font-size: 11px; color: #6B7280; text-transform: uppercase; border-bottom: 1px solid #E5E7EB;">
                                <div>Device</div>
                                <div>Equipment Type</div>
                                <div>Tags</div>
                                <div>Status</div>
                            </div>
                `;

                if (devices.length === 0) {
                    html += `
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            No devices configured
                        </div>
                    `;
                } else {
                    for (const device of devices) {
                        html += `
                            <div style="display: grid; grid-template-columns: 2fr 2fr 1fr 1fr; gap: 12px; padding: 12px 16px; font-size: 13px; border-bottom: 1px solid #F3F4F6;">
                                <div style="font-weight: 500; color: #1F2937;">${escapeHtml(device.name)}</div>
                                <div style="color: #6B7280;">${escapeHtml(device.equipment_type)}</div>
                                <div style="color: #6B7280;">${device.tag_count || 0}</div>
                                <div style="font-weight: 500;">${device.status}</div>
                            </div>
                        `;
                    }
                }

                html += `
                        </div>
                    </div>
                `;
            }

            // Add Quality Distribution section
            html += `
                <div style="margin-top: 24px;">
                    <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">
                        Quality Distribution
                    </div>
                    <div id="kepware-quality-dist" style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; padding: 16px;">
                        Loading quality data...
                    </div>
                </div>
            `;

            // Add Sample Tags section at the end
            html += `
                <div style="margin-top: 24px;">
                    <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">
                        Sample Tags (Live Values)
                    </div>
                    <div id="kepware-sample-tags" style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden;">
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            Loading sample tags...
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = html;

            // Update metrics
            updateElement('kepware-channels', diagnostics.total_channels || 0);
            updateElement('kepware-devices', diagnostics.total_devices || 0);
            updateElement('kepware-tags', diagnostics.total_tags || 0);

            // Fetch and display sample tags with current values and quality distribution
            fetchKepwareQualityDistribution();
            fetchKepwareSampleTags();
        }

        // Fetch and display quality distribution for Kepware
        async function fetchKepwareQualityDistribution() {
            try {
                const response = await fetch('/api/modes/kepware');
                const data = await response.json();

                const container = document.getElementById('kepware-quality-dist');
                if (!container) return;

                const metrics = data.metrics || {};
                const qualityDist = metrics.quality_distribution || {};
                const good = qualityDist.good || 0;
                const bad = qualityDist.bad || 0;
                const uncertain = qualityDist.uncertain || 0;
                const total = good + bad + uncertain;

                if (total === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; color: #9CA3AF; font-size: 13px;">
                            No quality data available. Start publishing messages to see distribution.
                        </div>
                    `;
                    return;
                }

                const goodPct = ((good / total) * 100).toFixed(1);
                const badPct = ((bad / total) * 100).toFixed(1);
                const uncertainPct = ((uncertain / total) * 100).toFixed(1);

                // Build quality distribution bars
                let html = `
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px;">
                            <span style="font-weight: 500; color: #10B981;">Good</span>
                            <span style="font-weight: 600; color: #1F2937;">${good} (${goodPct}%)</span>
                        </div>
                        <div style="background: #E5E7EB; border-radius: 6px; overflow: hidden; height: 24px;">
                            <div style="background: #10B981; height: 100%; width: ${goodPct}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px;">
                            <span style="font-weight: 500; color: #F59E0B;">Uncertain</span>
                            <span style="font-weight: 600; color: #1F2937;">${uncertain} (${uncertainPct}%)</span>
                        </div>
                        <div style="background: #E5E7EB; border-radius: 6px; overflow: hidden; height: 24px;">
                            <div style="background: #F59E0B; height: 100%; width: ${uncertainPct}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>

                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px;">
                            <span style="font-weight: 500; color: #EF4444;">Bad</span>
                            <span style="font-weight: 600; color: #1F2937;">${bad} (${badPct}%)</span>
                        </div>
                        <div style="background: #E5E7EB; border-radius: 6px; overflow: hidden; height: 24px;">
                            <div style="background: #EF4444; height: 100%; width: ${badPct}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>

                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #E5E7EB; font-size: 12px; color: #6B7280;">
                        Total Messages: ${total}
                    </div>
                `;

                container.innerHTML = html;

            } catch (error) {
                console.error('Error fetching Kepware quality distribution:', error);
                const container = document.getElementById('kepware-quality-dist');
                if (container) {
                    container.innerHTML = `
                        <div style="text-align: center; color: #EF4444; font-size: 13px;">
                            Error loading quality data
                        </div>
                    `;
                }
            }
        }

        // Fetch and display sample Kepware tags with live values
        async function fetchKepwareSampleTags() {
            try {
                // Get recent Kepware messages to extract tag values
                const response = await fetch('/api/modes/messages/recent?mode=kepware&protocol=mqtt&limit=50');
                const data = await response.json();

                const container = document.getElementById('kepware-sample-tags');
                if (!container) return;

                const messages = data.messages || [];

                if (messages.length === 0) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            No recent messages. Start MQTT broker to see live tag values.
                        </div>
                    `;
                    return;
                }

                // Extract unique tags with their latest values
                const tagMap = new Map();
                for (const msg of messages) {
                    const payload = msg.payload || {};
                    const sensorPath = payload.sensor_path;
                    const value = payload.value;
                    const quality = payload.quality || 'Good';
                    const timestamp = msg.timestamp;
                    const topic = msg.topic || '';
                    const unit = payload.unit || '';

                    if (sensorPath && value !== undefined) {
                        const key = sensorPath;
                        if (!tagMap.has(key) || tagMap.get(key).timestamp < timestamp) {
                            // Extract tag path from topic (kepware/Channel/Device/Tag)
                            const topicParts = topic.split('/');
                            const tagPath = topicParts.length >= 4 ?
                                `${topicParts[1]}.${topicParts[2]}.${topicParts[3]}` :
                                sensorPath.replace('/', '.');

                            tagMap.set(key, {
                                tagPath,
                                value: typeof value === 'number' ? value.toFixed(2) : value,
                                unit,
                                quality,
                                timestamp,
                                topic
                            });
                        }
                    }
                }

                const tags = Array.from(tagMap.values()).slice(0, 10); // Show first 10 unique tags

                if (tags.length === 0) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            No tag data available
                        </div>
                    `;
                    return;
                }

                // Build tags table
                let html = `
                    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 100px 140px; gap: 12px; padding: 10px 16px; background: #F3F4F6; font-weight: 600; font-size: 11px; color: #6B7280; text-transform: uppercase; border-bottom: 1px solid #E5E7EB;">
                        <div>Tag Path</div>
                        <div>Current Value</div>
                        <div>Unit</div>
                        <div>Quality</div>
                        <div>Last Updated</div>
                    </div>
                `;

                // Add tag rows
                for (const tag of tags) {
                    const timestamp = new Date(tag.timestamp * 1000);
                    const timeStr = timestamp.toLocaleTimeString('en-US', { hour12: false });
                    const secondsAgo = Math.floor((Date.now() / 1000) - tag.timestamp);
                    const timeAgo = secondsAgo < 60 ? `${secondsAgo}s ago` :
                                    secondsAgo < 3600 ? `${Math.floor(secondsAgo / 60)}m ago` :
                                    `${Math.floor(secondsAgo / 3600)}h ago`;

                    // Quality badge color
                    const qualityColor = tag.quality === 'Good' || tag.quality === 'good' ? '#10B981' : '#EF4444';

                    html += `
                        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 100px 140px; gap: 12px; padding: 10px 16px; font-size: 12px; border-bottom: 1px solid #F3F4F6;">
                            <div style="font-family: monospace; font-size: 11px; color: #1F2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(tag.topic)}">
                                ${escapeHtml(tag.tagPath)}
                            </div>
                            <div style="font-weight: 600; color: #1F2937;">${escapeHtml(tag.value)}</div>
                            <div style="color: #6B7280;">${escapeHtml(tag.unit)}</div>
                            <div>
                                <span style="background: ${qualityColor}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;">
                                    ${escapeHtml(tag.quality)}
                                </span>
                            </div>
                            <div style="color: #6B7280; font-size: 11px;">
                                ${timeStr}<br>
                                <span style="color: #9CA3AF;">${timeAgo}</span>
                            </div>
                        </div>
                    `;
                }

                container.innerHTML = html;

            } catch (error) {
                console.error('Error fetching Kepware sample tags:', error);
                const container = document.getElementById('kepware-sample-tags');
                if (container) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #EF4444; font-size: 13px;">
                            Error loading sample tags
                        </div>
                    `;
                }
            }
        }

        // Update Sparkplug B panel
        function updateSparkplugPanel(diagnostics) {
            const container = document.getElementById('sparkplug-nodes');
            if (!container) return;

            // Display edge node status
            const edgeNodeOnline = diagnostics.edge_node_online || false;
            const edgeNodeState = diagnostics.edge_node_state || '🔴 OFFLINE';
            const bdSeq = diagnostics.bd_seq || 0;
            const msgSeq = diagnostics.msg_seq || 0;
            const groupId = diagnostics.group_id || 'N/A';
            const edgeNodeId = diagnostics.edge_node_id || 'N/A';
            const birthTimeFormatted = diagnostics.edge_node_birth_time_formatted || 'Never';
            const birthTimeAgo = diagnostics.edge_node_birth_time_ago || 'N/A';
            const devices = diagnostics.devices || [];

            // Build HTML for edge node display
            let html = `
                <div class="sparkplug-node" style="border-color: ${edgeNodeOnline ? '#10B981' : '#EF4444'};">
                    <div style="margin-bottom: 16px;">
                        <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 8px;">
                            Configuration
                        </div>
                        <div style="display: grid; grid-template-columns: 140px 1fr; gap: 8px; font-size: 13px;">
                            <div style="color: #6B7280;">Group ID:</div>
                            <div style="font-weight: 500;">${escapeHtml(groupId)}</div>
                            <div style="color: #6B7280;">Edge Node ID:</div>
                            <div style="font-weight: 500;">${escapeHtml(edgeNodeId)}</div>
                            <div style="color: #6B7280;">Protobuf Encoding:</div>
                            <div>${diagnostics.use_protobuf ? '✅ Enabled' : '⚪ Disabled (using JSON)'}</div>
                        </div>
                    </div>

                    <div style="margin-bottom: 16px; padding: 12px; background: #F9FAFB; border-radius: 6px;">
                        <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">
                            State Management
                        </div>
                        <div style="display: grid; grid-template-columns: 200px 1fr; gap: 8px; font-size: 13px;">
                            <div style="color: #6B7280;">Birth/Death Sequence (bdSeq):</div>
                            <div style="font-weight: 600; color: #8B5CF6;">${bdSeq}</div>
                            <div style="color: #6B7280;">Message Sequence (seq):</div>
                            <div style="font-weight: 600; color: #8B5CF6;">${msgSeq}</div>
                            <div style="color: #6B7280;">Edge Node State:</div>
                            <div style="font-weight: 600;">${edgeNodeState}</div>
                            <div style="color: #6B7280;">Last NBIRTH:</div>
                            <div style="font-weight: 500;">${birthTimeFormatted} <span style="color: #6B7280;">(${birthTimeAgo})</span></div>
                        </div>
                    </div>

                    <div>
                        <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">
                            Device Status
                        </div>
                        <div style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden;">
                            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 12px; padding: 10px 16px; background: #F3F4F6; font-weight: 600; font-size: 11px; color: #6B7280; text-transform: uppercase; border-bottom: 1px solid #E5E7EB;">
                                <div>Device ID</div>
                                <div>State</div>
                                <div>Last DBIRTH</div>
                                <div>Metrics</div>
                            </div>
            `;

            // Add device rows
            if (devices.length === 0) {
                html += `
                    <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                        No devices configured
                    </div>
                `;
            } else {
                for (const device of devices) {
                    const deviceOnline = device.is_online || false;
                    const deviceState = device.state || '🔴 Offline';
                    const lastBirthSeq = device.last_birth_seq !== null && device.last_birth_seq !== undefined ? device.last_birth_seq : '-';

                    html += `
                        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 12px; padding: 12px 16px; font-size: 13px; border-bottom: 1px solid #F3F4F6;">
                            <div style="font-weight: 500; color: #1F2937;">${escapeHtml(device.device_id)}</div>
                            <div style="font-weight: 500;">${deviceState}</div>
                            <div style="color: #6B7280;">${lastBirthSeq}</div>
                            <div style="color: #6B7280;">${device.metric_count || 0}</div>
                        </div>
                    `;
                }
            }

            html += `
                        </div>
                    </div>

                    <!-- Quality Distribution Section -->
                    <div style="margin-top: 24px;">
                        <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">
                            Quality Distribution
                        </div>
                        <div id="sparkplug-quality-dist" style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; padding: 16px;">
                            Loading quality data...
                        </div>
                    </div>

                    <!-- Message Type Distribution Section -->
                    <div style="margin-top: 24px;">
                        <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">
                            Message Type Distribution
                        </div>
                        <div id="sparkplug-message-types" style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden;">
                            Loading message type data...
                        </div>
                    </div>

                    <!-- Recent Messages Section -->
                    <div style="margin-top: 24px;">
                        <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">
                            Recent Messages
                        </div>
                        <div id="sparkplug-recent-messages" style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden;">
                            <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                                Loading recent messages...
                            </div>
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = html;

            // Update metrics
            updateElement('sparkplug-births', devices.filter(d => d.last_birth_seq !== null).length);

            // Fetch and display recent Sparkplug B messages, quality distribution, and message types
            fetchSparkplugRecentMessages();
            fetchSparkplugQualityDistribution();
            fetchSparkplugMessageTypes();
        }

        // Fetch and display recent Sparkplug B messages
        async function fetchSparkplugRecentMessages() {
            try {
                const response = await fetch('/api/modes/messages/recent?mode=sparkplug_b&limit=20');
                const data = await response.json();

                const container = document.getElementById('sparkplug-recent-messages');
                if (!container) return;

                const messages = data.messages || [];

                if (messages.length === 0) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            No recent messages. Start MQTT broker to see messages.
                        </div>
                    `;
                    return;
                }

                // Build messages table
                let html = `
                    <div style="display: grid; grid-template-columns: 160px 100px 1fr 80px; gap: 12px; padding: 10px 16px; background: #F3F4F6; font-weight: 600; font-size: 11px; color: #6B7280; text-transform: uppercase; border-bottom: 1px solid #E5E7EB;">
                        <div>Time</div>
                        <div>Type</div>
                        <div>Topic</div>
                        <div>Seq</div>
                    </div>
                `;

                // Add message rows (show last 10)
                for (const msg of messages.slice(0, 10)) {
                    const timestamp = new Date(msg.timestamp * 1000);
                    const timeStr = timestamp.toLocaleTimeString('en-US', { hour12: false });
                    const messageType = msg.message_type || 'DDATA';
                    const topic = msg.topic || '';
                    const seq = msg.payload?.seq !== undefined ? msg.payload.seq : '-';

                    // Color code message types
                    let typeBgColor = '#3B82F6'; // Blue for DATA
                    if (messageType === 'NBIRTH' || messageType === 'DBIRTH') {
                        typeBgColor = '#10B981'; // Green for BIRTH
                    } else if (messageType === 'NDEATH' || messageType === 'DDEATH') {
                        typeBgColor = '#EF4444'; // Red for DEATH
                    }

                    // Shorten topic for display
                    const topicParts = topic.split('/');
                    const shortTopic = topicParts.length > 3 ?
                        `.../${topicParts[topicParts.length-2]}/${topicParts[topicParts.length-1]}` :
                        topic;

                    html += `
                        <div style="display: grid; grid-template-columns: 160px 100px 1fr 80px; gap: 12px; padding: 10px 16px; font-size: 12px; border-bottom: 1px solid #F3F4F6;">
                            <div style="color: #6B7280;">${timeStr}</div>
                            <div>
                                <span style="background: ${typeBgColor}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600;">
                                    ${escapeHtml(messageType)}
                                </span>
                            </div>
                            <div style="font-family: monospace; font-size: 11px; color: #1F2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(topic)}">
                                ${escapeHtml(shortTopic)}
                            </div>
                            <div style="color: #6B7280; text-align: center;">${seq}</div>
                        </div>
                    `;
                }

                container.innerHTML = html;

            } catch (error) {
                console.error('Error fetching Sparkplug B messages:', error);
                const container = document.getElementById('sparkplug-recent-messages');
                if (container) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #EF4444; font-size: 13px;">
                            Error loading messages
                        </div>
                    `;
                }
            }
        }

        // Fetch and display quality distribution for Sparkplug B
        async function fetchSparkplugQualityDistribution() {
            try {
                const response = await fetch('/api/modes/sparkplug_b');
                const data = await response.json();

                const container = document.getElementById('sparkplug-quality-dist');
                if (!container) return;

                const metrics = data.metrics || {};
                const qualityDist = metrics.quality_distribution || {};
                const good = qualityDist.good || 0;
                const bad = qualityDist.bad || 0;
                const uncertain = qualityDist.uncertain || 0;
                const total = good + bad + uncertain;

                if (total === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; color: #9CA3AF; font-size: 13px;">
                            No quality data available. Start publishing messages to see distribution.
                        </div>
                    `;
                    return;
                }

                const goodPct = ((good / total) * 100).toFixed(1);
                const badPct = ((bad / total) * 100).toFixed(1);
                const uncertainPct = ((uncertain / total) * 100).toFixed(1);

                // Build quality distribution bars
                let html = `
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px;">
                            <span style="font-weight: 500; color: #10B981;">Good</span>
                            <span style="font-weight: 600; color: #1F2937;">${good} (${goodPct}%)</span>
                        </div>
                        <div style="background: #E5E7EB; border-radius: 6px; overflow: hidden; height: 24px;">
                            <div style="background: #10B981; height: 100%; width: ${goodPct}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px;">
                            <span style="font-weight: 500; color: #F59E0B;">Uncertain</span>
                            <span style="font-weight: 600; color: #1F2937;">${uncertain} (${uncertainPct}%)</span>
                        </div>
                        <div style="background: #E5E7EB; border-radius: 6px; overflow: hidden; height: 24px;">
                            <div style="background: #F59E0B; height: 100%; width: ${uncertainPct}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>

                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px;">
                            <span style="font-weight: 500; color: #EF4444;">Bad</span>
                            <span style="font-weight: 600; color: #1F2937;">${bad} (${badPct}%)</span>
                        </div>
                        <div style="background: #E5E7EB; border-radius: 6px; overflow: hidden; height: 24px;">
                            <div style="background: #EF4444; height: 100%; width: ${badPct}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>

                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #E5E7EB; font-size: 12px; color: #6B7280;">
                        Total Messages: ${total}
                    </div>
                `;

                container.innerHTML = html;

            } catch (error) {
                console.error('Error fetching Sparkplug B quality distribution:', error);
                const container = document.getElementById('sparkplug-quality-dist');
                if (container) {
                    container.innerHTML = `
                        <div style="text-align: center; color: #EF4444; font-size: 13px;">
                            Error loading quality data
                        </div>
                    `;
                }
            }
        }

        // Fetch and display message type distribution for Sparkplug B
        async function fetchSparkplugMessageTypes() {
            try {
                const response = await fetch('/api/modes/messages/recent?mode=sparkplug_b&limit=200');
                const data = await response.json();

                const container = document.getElementById('sparkplug-message-types');
                if (!container) return;

                const messages = data.messages || [];

                if (messages.length === 0) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            No messages to analyze. Start MQTT broker to see message type distribution.
                        </div>
                    `;
                    return;
                }

                // Count message types
                const typeCounts = {
                    'NBIRTH': 0,
                    'DBIRTH': 0,
                    'NDATA': 0,
                    'DDATA': 0,
                    'NDEATH': 0,
                    'DDEATH': 0
                };

                for (const msg of messages) {
                    const messageType = msg.message_type;
                    if (messageType && typeCounts.hasOwnProperty(messageType)) {
                        typeCounts[messageType]++;
                    }
                }

                const total = Object.values(typeCounts).reduce((a, b) => a + b, 0);

                if (total === 0) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            No message type data available
                        </div>
                    `;
                    return;
                }

                // Build message type table
                let html = `
                    <div style="display: grid; grid-template-columns: 2fr 1fr 2fr; gap: 12px; padding: 10px 16px; background: #F3F4F6; font-weight: 600; font-size: 11px; color: #6B7280; text-transform: uppercase; border-bottom: 1px solid #E5E7EB;">
                        <div>Message Type</div>
                        <div>Count</div>
                        <div>Percentage</div>
                    </div>
                `;

                // Define message types with colors
                const messageTypes = [
                    { type: 'NBIRTH', label: 'NBIRTH (Node Birth)', color: '#10B981' },
                    { type: 'DBIRTH', label: 'DBIRTH (Device Birth)', color: '#059669' },
                    { type: 'NDATA', label: 'NDATA (Node Data)', color: '#3B82F6' },
                    { type: 'DDATA', label: 'DDATA (Device Data)', color: '#2563EB' },
                    { type: 'NDEATH', label: 'NDEATH (Node Death)', color: '#EF4444' },
                    { type: 'DDEATH', label: 'DDEATH (Device Death)', color: '#DC2626' }
                ];

                for (const msgType of messageTypes) {
                    const count = typeCounts[msgType.type];
                    const pct = ((count / total) * 100).toFixed(1);

                    html += `
                        <div style="display: grid; grid-template-columns: 2fr 1fr 2fr; gap: 12px; padding: 10px 16px; font-size: 13px; border-bottom: 1px solid #F3F4F6;">
                            <div>
                                <span style="background: ${msgType.color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; margin-right: 8px;">
                                    ${msgType.type}
                                </span>
                                <span style="color: #6B7280; font-size: 11px;">${msgType.label.split('(')[1].replace(')', '')}</span>
                            </div>
                            <div style="font-weight: 600; color: #1F2937;">${count}</div>
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <div style="flex: 1; background: #E5E7EB; border-radius: 4px; height: 16px; overflow: hidden;">
                                        <div style="background: ${msgType.color}; height: 100%; width: ${pct}%; transition: width 0.5s ease;"></div>
                                    </div>
                                    <span style="font-weight: 600; color: #1F2937; min-width: 45px;">${pct}%</span>
                                </div>
                            </div>
                        </div>
                    `;
                }

                html += `
                    <div style="padding: 12px 16px; background: #F9FAFB; font-size: 12px; color: #6B7280; border-top: 1px solid #E5E7EB;">
                        <strong>Total Messages Analyzed:</strong> ${total} (from last ${messages.length} messages)
                    </div>
                `;

                container.innerHTML = html;

            } catch (error) {
                console.error('Error fetching Sparkplug B message types:', error);
                const container = document.getElementById('sparkplug-message-types');
                if (container) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #EF4444; font-size: 13px;">
                            Error loading message type data
                        </div>
                    `;
                }
            }
        }

        // Fetch and display OPC UA connected clients
        async function fetchOPCUAClients() {
            try {
                const response = await fetch('/api/protocols/opcua/clients');
                const data = await response.json();

                const clients = data.clients || [];
                const totalClients = data.total_clients || 0;

                // Update client count badge
                const countBadge = document.getElementById('opcua-client-count');
                if (countBadge) {
                    countBadge.textContent = `${totalClients} client${totalClients !== 1 ? 's' : ''}`;
                }

                const container = document.getElementById('opcua-clients-list');
                if (!container) return;

                if (clients.length === 0) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                            No OPC UA clients currently connected
                        </div>
                    `;
                    return;
                }

                // Build client table
                let html = `
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead style="background: #F9FAFB; border-bottom: 2px solid #E5E7EB;">
                            <tr>
                                <th style="padding: 10px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #6B7280; text-transform: uppercase;">Client ID</th>
                                <th style="padding: 10px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #6B7280; text-transform: uppercase;">Endpoint</th>
                                <th style="padding: 10px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #6B7280; text-transform: uppercase;">Subscriptions</th>
                                <th style="padding: 10px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #6B7280; text-transform: uppercase;">Connected</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                for (const client of clients) {
                    const clientId = client.client_id || 'Unknown';
                    const endpoint = client.endpoint || 'Unknown';
                    const subscriptions = client.subscriptions || 0;
                    const connectTime = client.connect_time || Date.now() / 1000;

                    // Calculate time ago
                    const now = Date.now() / 1000;
                    const secondsAgo = Math.floor(now - connectTime);
                    let timeAgo = '';
                    if (secondsAgo < 60) {
                        timeAgo = `${secondsAgo}s ago`;
                    } else if (secondsAgo < 3600) {
                        timeAgo = `${Math.floor(secondsAgo / 60)}m ago`;
                    } else {
                        timeAgo = `${Math.floor(secondsAgo / 3600)}h ago`;
                    }

                    html += `
                        <tr style="border-bottom: 1px solid #E5E7EB;">
                            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #1F2937; font-family: 'Monaco', monospace;">${escapeHtml(clientId)}</td>
                            <td style="padding: 12px 16px; font-size: 12px; color: #6B7280; font-family: 'Monaco', monospace;">${escapeHtml(endpoint)}</td>
                            <td style="padding: 12px 16px; font-size: 13px; color: #1F2937; text-align: left;">
                                <span style="background: #DBEAFE; color: #1E40AF; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">${subscriptions}</span>
                            </td>
                            <td style="padding: 12px 16px; font-size: 12px; color: #6B7280;">${timeAgo}</td>
                        </tr>
                    `;
                }

                html += `
                        </tbody>
                    </table>
                `;

                container.innerHTML = html;

            } catch (error) {
                console.error('Error fetching OPC UA clients:', error);
                const container = document.getElementById('opcua-clients-list');
                if (container) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #EF4444; font-size: 13px;">
                            Error loading client information
                        </div>
                    `;
                }
            }
        }

        // Fetch and display MQTT subscribers
        async function fetchMQTTSubscribers() {
            try {
                const response = await fetch('/api/protocols/mqtt/subscribers');
                const data = await response.json();

                const subscribers = data.subscribers || [];
                const totalSubscribers = data.total_subscribers || 0;
                const note = data.note || '';

                // Update subscriber count badge
                const countBadge = document.getElementById('mqtt-subscriber-count');
                if (countBadge) {
                    countBadge.textContent = subscribers.length > 0 ? `${totalSubscribers} subscriber${totalSubscribers !== 1 ? 's' : ''}` : 'N/A';
                }

                const container = document.getElementById('mqtt-subscribers-list');
                if (!container) return;

                // MQTT protocol limitation message
                container.innerHTML = `
                    <div style="padding: 20px;">
                        <div style="text-align: center; color: #9CA3AF; font-size: 13px; margin-bottom: 12px;">
                            Subscriber tracking not available
                        </div>
                        <div style="background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 6px; padding: 12px; font-size: 12px; color: #92400E;">
                            <strong style="color: #78350F;">Protocol Limitation:</strong><br>
                            MQTT publishers do not receive subscriber information from brokers. To track subscribers, you would need:<br><br>
                            <ul style="margin: 8px 0 0 20px; padding: 0;">
                                <li>Mosquitto: Subscribe to <code style="background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px;">$SYS/broker/clients/connected</code></li>
                                <li>HiveMQ: Use REST API <code style="background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px;">/api/v1/mqtt/clients</code></li>
                                <li>AWS IoT: CloudWatch metrics</li>
                                <li>Azure IoT Hub: Device Registry API</li>
                            </ul>
                        </div>
                    </div>
                `;

            } catch (error) {
                console.error('Error fetching MQTT subscribers:', error);
                const container = document.getElementById('mqtt-subscribers-list');
                if (container) {
                    container.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #EF4444; font-size: 13px;">
                            Error loading subscriber information
                        </div>
                    `;
                }
            }
        }

        // Update Honeywell panel
        function updateHoneywellPanel(diagnostics) {
            const container = document.getElementById('honeywell-modules-view');
            if (!container) return;

            const modules = diagnostics.modules_status || [];
            if (modules.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #6B7280;">No modules configured</div>';
                return;
            }

            let html = '';
            for (const module of modules) {
                const type = module.type || 'FIM';
                const icon = type.substring(0, 2);
                html += `
                    <div class="honeywell-module">
                        <div class="honeywell-module-header">
                            <div class="honeywell-module-icon">${icon}</div>
                            <div>
                                <div class="honeywell-module-name">${escapeHtml(module.name || 'Module')}</div>
                                <div style="font-size: 11px; color: #6B7280;">${type}</div>
                            </div>
                        </div>
                        <div style="font-size: 12px; color: #6B7280; margin-top: 12px;">
                            Points: ${module.point_count || 0}
                        </div>
                    </div>
                `;
            }
            container.innerHTML = html;

            // Update metrics
            updateElement('honeywell-modules', diagnostics.modules || 0);
            updateElement('honeywell-points', diagnostics.points || 0);
        }

        // Update mode panel metrics
        function updateModePanelMetrics(modeName, status) {
            const metrics = status.metrics || {};

            if (modeName === 'generic') {
                updateElement('generic-msg-rate', (metrics.message_rate || 0).toFixed(1));
                updateElement('generic-total-sensors', metrics.sensors_registered || 0);
                updateElement('generic-payload-size', Math.round(metrics.avg_payload_size || 0));
                updateElement('generic-quality-pct', Math.round(metrics.quality_good_pct || 0));
            }
            else if (modeName === 'kepware') {
                updateElement('kepware-msg-rate', (metrics.message_rate || 0).toFixed(1));
            }
            else if (modeName === 'sparkplug_b' || modeName === 'sparkplug-b') {
                updateElement('sparkplug-msg-rate', (metrics.message_rate || 0).toFixed(1));
                updateElement('sparkplug-births', metrics.birth_messages || 0);
            }
            else if (modeName === 'honeywell') {
                updateElement('honeywell-msg-rate', (metrics.message_rate || 0).toFixed(1));
                updateElement('honeywell-controllers', metrics.controllers || 0);
            }
        }

        // Message inspector
        let inspectorRunning = false;
        let inspectorMessages = [];
        const MAX_INSPECTOR_MESSAGES = 100;
        let inspectorInterval = null;
        let inspectorSensorList = [];

        function toggleMessageInspector() {
            inspectorRunning = !inspectorRunning;
            const btn = document.getElementById('inspector-toggle-btn');
            if (btn) {
                btn.textContent = inspectorRunning ? 'Stop' : 'Start';
                btn.classList.toggle('btn-start', !inspectorRunning);
            }

            if (!inspectorRunning) {
                console.log('Message inspector stopped');
                if (inspectorInterval) {
                    clearInterval(inspectorInterval);
                    inspectorInterval = null;
                }
            } else {
                console.log('Message inspector started');
                const body = document.getElementById('message-inspector-body');
                if (body && inspectorMessages.length === 0) {
                    body.innerHTML = '<div style="text-align: center; padding: 40px; color: #6B7280;">Listening for vendor mode messages...</div>';
                }
                // Start polling for messages
                if (!inspectorInterval) {
                    fetchSensorList().then(() => {
                        inspectorInterval = setInterval(pollVendorMessages, 2000); // Poll every 2 seconds
                        pollVendorMessages(); // Immediate first poll
                    });
                }
            }
        }

        async function fetchSensorList() {
            // Use predefined sensor list
            const sampleSensors = [
                { industry: 'mining', sensor: 'crusher_1_motor_power' },
                { industry: 'mining', sensor: 'conveyor_belt_1_speed' },
                { industry: 'oil_gas', sensor: 'compressor_1_motor_power' },
                { industry: 'oil_gas', sensor: 'pipeline_1_flow' },
                { industry: 'utilities', sensor: 'grid_main_frequency' },
                { industry: 'manufacturing', sensor: 'robot_1_joint_1_torque' },
            ];
            inspectorSensorList = sampleSensors;
        }

        async function pollVendorMessages() {
            if (!inspectorRunning) return;

            try {
                // Fetch recent real messages from the backend
                const response = await fetch('/api/modes/messages/recent?limit=50');
                if (!response.ok) {
                    console.error('Failed to fetch messages:', response.status);
                    return;
                }

                const data = await response.json();
                console.log(`Fetched ${data.count} recent messages`);

                // Process each message
                for (const message of data.messages) {
                    addMessageToInspector(message);
                }

            } catch (error) {
                console.error('Error polling vendor messages:', error);
            }
        }

        function clearMessageInspector() {
            inspectorMessages = [];
            const body = document.getElementById('message-inspector-body');
            if (body) {
                body.innerHTML = '<div style="text-align: center; padding: 40px; color: #6B7280;">Cleared. Click "Start" to resume.</div>';
            }
        }

        function addMessageToInspector(message) {
            console.log('addMessageToInspector called:', message);

            if (!inspectorRunning) {
                console.log('Inspector not running, skipping message');
                return;
            }

            // Apply protocol filter
            const protocolFilter = document.getElementById('inspector-protocol-filter')?.value;
            if (protocolFilter && message.protocol !== protocolFilter) {
                console.log('Message filtered out by protocol');
                return;
            }

            // Apply mode filter
            const modeFilter = document.getElementById('inspector-mode-filter')?.value;
            console.log('Mode filter value:', modeFilter, 'Message mode:', message.mode);

            if (modeFilter && message.mode !== modeFilter) {
                console.log('Message filtered out by mode');
                return;
            }

            // Apply industry filter
            const industryFilter = document.getElementById('inspector-industry-filter')?.value;
            if (industryFilter && message.industry !== industryFilter) {
                console.log('Message filtered out by industry');
                return;
            }

            // Add to array (FIFO)
            inspectorMessages.unshift(message);
            if (inspectorMessages.length > MAX_INSPECTOR_MESSAGES) {
                inspectorMessages.pop();
            }

            console.log('Inspector messages count:', inspectorMessages.length);

            // Update UI
            const body = document.getElementById('message-inspector-body');
            if (!body) {
                console.error('Message inspector body element not found!');
                return;
            }

            let html = '';
            for (const msg of inspectorMessages) {
                const timestamp = new Date(msg.timestamp * 1000).toLocaleTimeString();
                const payloadStr = JSON.stringify(msg.payload, null, 2);
                const protocol = msg.protocol || 'unknown';
                const industry = msg.industry || 'N/A';
                const messageType = msg.message_type || null;

                // Protocol color coding
                let protocolClass = 'message-protocol';
                if (protocol === 'mqtt') protocolClass += ' protocol-mqtt';
                else if (protocol === 'opcua') protocolClass += ' protocol-opcua';
                else if (protocol === 'modbus') protocolClass += ' protocol-modbus';

                // Industry badge styling
                const industryBadge = industry !== 'N/A' ?
                    `<span class="message-industry" style="background: #F3F4F6; color: #374151; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${escapeHtml(industry.toUpperCase())}</span>` : '';

                // Sparkplug B message type badge
                let messageTypeBadge = '';
                if (messageType) {
                    let bgColor = '#8B5CF6'; // Default purple
                    if (messageType === 'NBIRTH' || messageType === 'DBIRTH') {
                        bgColor = '#10B981'; // Green for BIRTH
                    } else if (messageType === 'NDEATH' || messageType === 'DDEATH') {
                        bgColor = '#EF4444'; // Red for DEATH
                    } else if (messageType === 'NDATA' || messageType === 'DDATA') {
                        bgColor = '#3B82F6'; // Blue for DATA
                    }
                    messageTypeBadge = `<span style="background: ${bgColor}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${escapeHtml(messageType)}</span>`;
                }

                html += `
                    <div class="message-item">
                        <div class="message-header">
                            <span class="message-timestamp">${timestamp}</span>
                            <span class="${protocolClass}">${escapeHtml(protocol.toUpperCase())}</span>
                            ${industryBadge}
                            ${messageTypeBadge}
                            <span class="message-topic">${escapeHtml(msg.topic || 'N/A')}</span>
                            <span class="message-mode">${escapeHtml(msg.mode || 'unknown')}</span>
                        </div>
                        <div class="message-payload">${syntaxHighlightJSON(payloadStr)}</div>
                    </div>
                `;
            }
            body.innerHTML = html;
            console.log('Updated inspector UI with', inspectorMessages.length, 'messages');
        }

        // Syntax highlighting for JSON
        function syntaxHighlightJSON(json) {
            json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
                let cls = 'message-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'message-key';
                    } else {
                        cls = 'message-value';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'message-value';
                } else if (/null/.test(match)) {
                    cls = 'message-value';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        }

        // Helper to escape HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Helper to update element text
        function updateElement(id, value) {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = value;
            }
        }

        // Periodic refresh of vendor modes (every 5 seconds)
        setInterval(() => {
            if (document.getElementById('content-modes')?.classList.contains('active')) {
                refreshVendorModes();
            }
        }, 5000);

        // Initial load
        if (document.getElementById('content-modes')) {
            setTimeout(() => {
                refreshVendorModes();
            }, 1000);
        }

        // Periodic refresh of protocol clients (every 10 seconds)
        setInterval(() => {
            if (document.getElementById('content-overview')?.classList.contains('active')) {
                fetchOPCUAClients();
                fetchMQTTSubscribers();
            }
        }, 10000);

        // Initial load of protocol clients
        if (document.getElementById('opcua-clients-section')) {
            setTimeout(() => {
                fetchOPCUAClients();
                fetchMQTTSubscribers();
            }, 1500);
        }

        // ==================== CONNECTION INFO JAVASCRIPT ====================

        // Load connection information
        async function loadConnectionInfo() {
            try {
                const response = await fetch('/api/connection/endpoints');
                const data = await response.json();

                // Render protocols
                renderProtocols(data.protocols);

                // Render vendor modes
                renderVendorModes(data.vendor_modes);

                // Render PLCs
                renderPLCs(data.plc_controllers);

                // Render examples
                renderConnectionExamples(data.connection_examples);

            } catch (error) {
                console.error('Error loading connection info:', error);
            }
        }

        function renderProtocols(protocols) {
            const container = document.getElementById('connection-protocols');
            container.innerHTML = '';

            for (const [name, info] of Object.entries(protocols)) {
                const card = document.createElement('div');
                card.style.cssText = 'background: rgba(255,255,255,0.05); border-radius: 8px; padding: 16px; border: 1px solid rgba(255,255,255,0.1);';

                let details = '';
                if (name === 'opcua') {
                    // Build vendor-specific endpoints table
                    let vendorEndpoints = '';
                    if (info.vendor_endpoints) {
                        vendorEndpoints = `
                            <div style="margin-top: 12px;">
                                <strong style="color: #3B82F6;">Vendor-Specific Endpoints:</strong>
                                <div style="margin-top: 8px; background: rgba(0,0,0,0.2); border-radius: 6px; padding: 12px;">
                                    ${Object.entries(info.vendor_endpoints).map(([mode, ep]) => `
                                        <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                            <div style="font-weight: 600; color: ${mode === 'generic' ? '#10B981' : mode === 'kepware' ? '#F59E0B' : '#8B5CF6'}; text-transform: capitalize; margin-bottom: 4px;">${mode.replace('_', ' ')}</div>
                                            <div style="font-size: 11px;"><strong>Port:</strong> ${ep.port}</div>
                                            <div style="font-size: 11px;"><strong>Nodes:</strong> ${ep.node_count}</div>
                                            ${ep.note ? `<div style="font-size: 10px; color: rgba(255,255,255,0.5); margin-top: 4px; font-style: italic;">${ep.note}</div>` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `;
                    }

                    details = `
                        <div style="margin-top: 8px; font-size: 13px;">
                            <div><strong>Main Endpoint:</strong> <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">${info.endpoint}</code></div>
                            <div style="margin-top: 4px;"><strong>Namespace:</strong> ${info.namespace}</div>
                            <div style="margin-top: 4px;"><strong>Security:</strong> ${info.security}</div>
                            ${vendorEndpoints}
                        </div>
                    `;
                } else if (name === 'mqtt') {
                    details = `
                        <div style="margin-top: 8px; font-size: 13px;">
                            <div><strong>Broker:</strong> <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">${info.broker}:${info.port}</code></div>
                            <div style="margin-top: 4px;"><strong>TLS:</strong> ${info.tls ? 'Enabled' : 'Disabled'}</div>
                            <div style="margin-top: 4px;"><strong>Auth Required:</strong> ${info.auth_required ? 'Yes' : 'No'}</div>
                        </div>
                    `;
                } else if (name === 'modbus') {
                    details = `
                        <div style="margin-top: 8px; font-size: 13px;">
                            <div><strong>Host:</strong> <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">${info.host}:${info.port}</code></div>
                            <div style="margin-top: 4px;"><strong>Protocol:</strong> ${info.protocol}</div>
                            <div style="margin-top: 4px;"><strong>Slave ID:</strong> ${info.slave_id}</div>
                        </div>
                    `;
                } else if (name === 'websocket') {
                    details = `
                        <div style="margin-top: 8px; font-size: 13px;">
                            <div><strong>URL:</strong> <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">${info.url}</code></div>
                            <div style="margin-top: 4px;"><strong>Update Frequency:</strong> ${info.update_frequency}</div>
                        </div>
                    `;
                }

                card.innerHTML = `
                    <div style="font-weight: 600; font-size: 14px; color: #10B981; text-transform: uppercase; margin-bottom: 4px;">${name}</div>
                    <div style="font-size: 12px; color: rgba(255,255,255,0.6); margin-bottom: 8px;">${info.description}</div>
                    ${details}
                `;

                container.appendChild(card);
            }
        }

        function renderVendorModes(vendorModes) {
            const container = document.getElementById('connection-vendor-modes');
            container.innerHTML = '';

            for (const [name, info] of Object.entries(vendorModes)) {
                const card = document.createElement('div');
                card.style.cssText = 'background: rgba(255,255,255,0.05); border-radius: 8px; padding: 16px; border: 1px solid rgba(255,255,255,0.1);';

                card.innerHTML = `
                    <div style="font-weight: 600; font-size: 14px; color: #3B82F6; margin-bottom: 4px;">${info.display_name}</div>
                    <div style="font-size: 12px; color: rgba(255,255,255,0.6); margin-bottom: 12px;">${info.description}</div>

                    <div style="margin-bottom: 8px;">
                        <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">OPC-UA Pattern:</div>
                        <code style="display: block; background: rgba(0,0,0,0.3); padding: 6px 8px; border-radius: 4px; font-size: 11px; word-break: break-all;">${info.opcua_pattern}</code>
                    </div>

                    <div style="margin-bottom: 8px;">
                        <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">MQTT Pattern:</div>
                        <code style="display: block; background: rgba(0,0,0,0.3); padding: 6px 8px; border-radius: 4px; font-size: 11px; word-break: break-all;">${info.mqtt_pattern}</code>
                    </div>

                    <div style="margin-bottom: 8px;">
                        <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">Example OPC-UA:</div>
                        <code style="display: block; background: rgba(16, 185, 129, 0.1); padding: 6px 8px; border-radius: 4px; font-size: 10px; word-break: break-all; color: #10B981;">${info.example_opcua}</code>
                    </div>

                    <div>
                        <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">Example MQTT:</div>
                        <code style="display: block; background: rgba(16, 185, 129, 0.1); padding: 6px 8px; border-radius: 4px; font-size: 10px; word-break: break-all; color: #10B981;">${info.example_mqtt}</code>
                    </div>
                `;

                container.appendChild(card);
            }
        }

        function renderPLCs(plcInfo) {
            const container = document.getElementById('connection-plcs');
            container.innerHTML = '';

            // Add summary card first
            const summaryCard = document.createElement('div');
            summaryCard.style.cssText = 'background: rgba(139, 92, 246, 0.1); border-radius: 8px; padding: 16px; border: 1px solid rgba(139, 92, 246, 0.3); grid-column: 1 / -1;';
            summaryCard.innerHTML = `
                <div style="font-weight: 600; font-size: 14px; color: #8B5CF6; margin-bottom: 8px;">PLC Overview</div>
                <div style="font-size: 13px;">${plcInfo.description}</div>
                <div style="margin-top: 8px; display: flex; gap: 16px;">
                    <div><strong>Total PLCs:</strong> ${plcInfo.total_plcs}</div>
                    <div><strong>Vendors:</strong> ${plcInfo.total_vendors}</div>
                </div>
            `;
            container.appendChild(summaryCard);

            // Add vendor cards
            plcInfo.vendors.forEach(vendor => {
                const card = document.createElement('div');
                card.style.cssText = 'background: rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; border: 1px solid rgba(255,255,255,0.1);';

                card.innerHTML = `
                    <div style="font-weight: 600; font-size: 13px; color: #8B5CF6; margin-bottom: 6px;">${vendor.name}</div>
                    <div style="font-size: 11px; color: rgba(255,255,255,0.6); margin-bottom: 6px;">PLCs: ${vendor.plc_count}</div>
                    <div style="font-size: 11px;">
                        <div style="color: rgba(255,255,255,0.5); margin-bottom: 4px;">Channels:</div>
                        ${vendor.channels.map(ch => `<div style="padding: 2px 6px; background: rgba(0,0,0,0.3); border-radius: 4px; margin: 2px 0; font-size: 10px;"><code>${ch}</code></div>`).join('')}
                    </div>
                `;

                container.appendChild(card);
            });
        }

        function renderConnectionExamples(examples) {
            const container = document.getElementById('connection-examples');
            container.innerHTML = '';

            for (const [name, info] of Object.entries(examples)) {
                const card = document.createElement('div');
                card.style.cssText = 'background: rgba(255,255,255,0.05); border-radius: 8px; padding: 16px; border: 1px solid rgba(255,255,255,0.1);';

                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <div style="font-weight: 600; font-size: 14px; color: #10B981; margin-bottom: 4px;">${name.replace(/_/g, ' ').toUpperCase()}</div>
                            <div style="font-size: 12px; color: rgba(255,255,255,0.6);">${info.description}</div>
                            ${info.library ? `<div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 4px;">Library: ${info.library} | Install: <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">${info.install}</code></div>` : ''}
                        </div>
                        <button onclick="copyToClipboard(\`${info.code.replace(/`/g, '\\`')}\`, this)" style="padding: 8px 16px; background: #10B981; color: white; border: none; border-radius: 6px; font-size: 12px; cursor: pointer; white-space: nowrap;">Copy Code</button>
                    </div>
                    <pre style="background: #1a1a1a; padding: 12px; border-radius: 6px; overflow-x: auto; margin: 0;"><code style="font-size: 11px; color: #e5e7eb; font-family: 'Courier New', monospace;">${info.code}</code></pre>
                `;

                container.appendChild(card);
            }
        }

        function copyToClipboard(text, button) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.style.background = '#059669';
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = '#10B981';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        }

        // ==================== END CONNECTION INFO JAVASCRIPT ====================

        // ==================== END VENDOR MODE JAVASCRIPT ====================

    </script>
</body>
</html>"""


def get_main_page_html() -> str:
    """Return the complete HTML page by combining all sections."""
    return (
        get_head_html()
        + "\n"
        + get_styles_html()
        + "\n"
        + get_body_html()
        + "\n"
        + get_scripts_html()
    )
