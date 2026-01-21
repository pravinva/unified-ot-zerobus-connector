"""Training UI module - provides GUI for training scenarios and fault injection."""

from __future__ import annotations


def get_training_ui_html() -> str:
    """Return HTML/CSS/JS for the Training UI tab."""
    return """
    <!-- Training Tab CSS -->
    <style>
        .training-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .training-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .training-section h2 {
            margin-top: 0;
            color: #1B3139;
            font-size: 20px;
            border-bottom: 2px solid #00A8E1;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        .training-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .training-card {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            border-left: 4px solid #00A8E1;
        }

        .training-card h3 {
            margin: 0 0 10px 0;
            color: #1B3139;
            font-size: 16px;
        }

        .training-card .difficulty-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-right: 8px;
        }

        .difficulty-beginner { background: #10B981; color: white; }
        .difficulty-intermediate { background: #F59E0B; color: white; }
        .difficulty-advanced { background: #EF4444; color: white; }

        .training-form {
            display: grid;
            gap: 15px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            font-weight: 600;
            color: #1B3139;
            margin-bottom: 5px;
            font-size: 14px;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        .form-group textarea {
            min-height: 80px;
            resize: vertical;
        }

        .btn-training {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
        }

        .btn-primary {
            background: #00A8E1;
            color: white;
        }

        .btn-primary:hover {
            background: #0087b8;
        }

        .btn-success {
            background: #10B981;
            color: white;
        }

        .btn-success:hover {
            background: #059669;
        }

        .btn-danger {
            background: #EF4444;
            color: white;
        }

        .btn-danger:hover {
            background: #DC2626;
        }

        .injection-list {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            max-height: 200px;
            overflow-y: auto;
        }

        .injection-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            border-bottom: 1px solid #eee;
        }

        .injection-item:last-child {
            border-bottom: none;
        }

        .leaderboard-table {
            width: 100%;
            border-collapse: collapse;
        }

        .leaderboard-table th,
        .leaderboard-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }

        .leaderboard-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #1B3139;
        }

        .leaderboard-table tr:hover {
            background: #f8f9fa;
        }

        .rank-1 { color: #FFD700; font-weight: bold; }
        .rank-2 { color: #C0C0C0; font-weight: bold; }
        .rank-3 { color: #CD7F32; font-weight: bold; }

        .csv-upload-area {
            border: 2px dashed #00A8E1;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }

        .csv-upload-area:hover {
            background: #f0f9ff;
            border-color: #0087b8;
        }

        .csv-upload-area.dragover {
            background: #e0f2fe;
            border-color: #0087b8;
        }

        .notification {
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
            z-index: 10000;
            max-width: 400px;
        }

        .notification.success {
            background: #10B981;
            color: white;
        }

        .notification.error {
            background: #EF4444;
            color: white;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .tabs {
            display: flex;
            border-bottom: 2px solid #e5e7eb;
            margin-bottom: 20px;
        }

        .tab {
            padding: 12px 24px;
            cursor: pointer;
            border: none;
            background: none;
            font-weight: 600;
            color: #6b7280;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }

        .tab:hover {
            color: #00A8E1;
        }

        .tab.active {
            color: #00A8E1;
            border-bottom-color: #00A8E1;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }
    </style>

    <!-- Training Tab Content -->
    <div class="training-container">
        <!-- Tab Navigation -->
        <div class="tabs">
            <button class="tab active" onclick="switchTrainingTab('inject')">Inject Faults</button>
            <button class="tab" onclick="switchTrainingTab('scenarios')">Scenarios</button>
            <button class="tab" onclick="switchTrainingTab('csv')">CSV Upload</button>
            <button class="tab" onclick="switchTrainingTab('leaderboard')">Leaderboard</button>
        </div>

        <!-- Inject Faults Tab -->
        <div id="inject-tab" class="tab-content active">
            <div class="training-section">
                <h2>🎯 Manual Fault Injection</h2>
                <div class="training-grid">
                    <div>
                        <div class="training-form">
                            <div class="form-group">
                                <label>Sensor Path</label>
                                <input type="text" id="inject-sensor-path"
                                       placeholder="mining/crusher_bearing_temp"
                                       list="sensor-paths">
                                <datalist id="sensor-paths"></datalist>
                            </div>
                            <div class="form-group">
                                <label>Value</label>
                                <input type="number" id="inject-value" step="0.1" placeholder="95.5">
                            </div>
                            <div class="form-group">
                                <label>Duration (seconds)</label>
                                <input type="number" id="inject-duration" value="60">
                            </div>
                            <button class="btn-training btn-primary" onclick="injectSingleFault()">
                                Inject Fault
                            </button>
                        </div>
                    </div>
                    <div>
                        <h3>Batch Injection</h3>
                        <div class="injection-list" id="batch-injection-list">
                            <p style="color: #6b7280; text-align: center;">No injections added yet</p>
                        </div>
                        <div class="training-form" style="margin-top: 10px;">
                            <button class="btn-training btn-success" onclick="addToBatch()">
                                Add to Batch
                            </button>
                            <button class="btn-training btn-primary" onclick="executeBatch()">
                                Execute Batch
                            </button>
                            <button class="btn-training btn-danger" onclick="clearBatch()">
                                Clear Batch
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scenarios Tab -->
        <div id="scenarios-tab" class="tab-content">
            <div class="training-section">
                <h2>📋 Create Training Scenario</h2>
                <div class="training-form">
                    <div class="form-group">
                        <label>Scenario Name</label>
                        <input type="text" id="scenario-name" placeholder="Bearing Overheating Scenario">
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="scenario-description"
                                  placeholder="Gradual bearing temperature increase leading to failure"></textarea>
                    </div>
                    <div class="training-grid">
                        <div class="form-group">
                            <label>Industry</label>
                            <select id="scenario-industry">
                                <option value="mining">Mining</option>
                                <option value="utilities">Utilities</option>
                                <option value="manufacturing">Manufacturing</option>
                                <option value="oil_gas">Oil & Gas</option>
                                <option value="automotive">Automotive</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Difficulty</label>
                            <select id="scenario-difficulty">
                                <option value="beginner">Beginner</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="advanced">Advanced</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Duration (seconds)</label>
                            <input type="number" id="scenario-duration" value="300">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Tags (comma-separated)</label>
                        <input type="text" id="scenario-tags" placeholder="bearing, temperature, failure">
                    </div>
                    <h3 style="margin-top: 20px;">Timed Injections</h3>
                    <div class="injection-list" id="scenario-injection-list">
                        <p style="color: #6b7280; text-align: center;">No injections added yet</p>
                    </div>
                    <div class="training-grid" style="margin-top: 10px;">
                        <div class="form-group">
                            <label>Sensor Path</label>
                            <input type="text" id="scenario-inject-sensor" placeholder="mining/crusher_bearing_temp">
                        </div>
                        <div class="form-group">
                            <label>Value</label>
                            <input type="number" id="scenario-inject-value" step="0.1">
                        </div>
                        <div class="form-group">
                            <label>At Second</label>
                            <input type="number" id="scenario-inject-time" value="0">
                        </div>
                    </div>
                    <div class="training-grid" style="margin-top: 10px;">
                        <button class="btn-training btn-success" onclick="addScenarioInjection()">
                            Add Injection
                        </button>
                        <button class="btn-training btn-primary" onclick="createScenario()">
                            Create Scenario
                        </button>
                    </div>
                </div>
            </div>

            <div class="training-section">
                <h2>🎬 Saved Scenarios</h2>
                <div id="scenarios-list" class="training-grid">
                    <p style="color: #6b7280;">Loading scenarios...</p>
                </div>
            </div>
        </div>

        <!-- CSV Upload Tab -->
        <div id="csv-tab" class="tab-content">
            <div class="training-section">
                <h2>📁 CSV Data Upload & Replay</h2>
                <div class="csv-upload-area" id="csv-upload-area"
                     ondrop="handleCSVDrop(event)"
                     ondragover="handleCSVDragOver(event)"
                     ondragleave="handleCSVDragLeave(event)"
                     onclick="document.getElementById('csv-file-input').click()">
                    <input type="file" id="csv-file-input" accept=".csv"
                           style="display: none;" onchange="handleCSVFileSelect(event)">
                    <p style="font-size: 48px; margin: 0;">📄</p>
                    <p style="font-size: 16px; font-weight: 600; margin: 10px 0;">
                        Drop CSV file here or click to browse
                    </p>
                    <p style="font-size: 14px; color: #6b7280; margin: 0;">
                        Format: timestamp,sensor_path,value
                    </p>
                </div>
                <div id="csv-preview" style="margin-top: 20px; display: none;">
                    <h3>CSV Preview</h3>
                    <div id="csv-preview-content"></div>
                    <div class="training-grid" style="margin-top: 15px;">
                        <div class="form-group">
                            <label>Replay Speed</label>
                            <select id="csv-replay-speed">
                                <option value="1">1x (Real-time)</option>
                                <option value="2">2x</option>
                                <option value="5">5x</option>
                                <option value="10" selected>10x</option>
                                <option value="50">50x</option>
                                <option value="100">100x</option>
                            </select>
                        </div>
                        <div style="display: flex; gap: 10px; align-items: flex-end;">
                            <button class="btn-training btn-primary" onclick="startCSVReplay()">
                                Start Replay
                            </button>
                            <button class="btn-training btn-danger" onclick="clearCSV()">
                                Clear
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Leaderboard Tab -->
        <div id="leaderboard-tab" class="tab-content">
            <div class="training-section">
                <h2>🏆 Training Leaderboard</h2>
                <table class="leaderboard-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Trainee</th>
                            <th>Attempts</th>
                            <th>Correct</th>
                            <th>Avg Score</th>
                            <th>Avg Time</th>
                            <th>Accuracy</th>
                        </tr>
                    </thead>
                    <tbody id="leaderboard-body">
                        <tr>
                            <td colspan="7" style="text-align: center; color: #6b7280;">
                                Loading leaderboard...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Training JavaScript -->
    <script>
        // Global state
        let batchInjections = [];
        let scenarioInjections = [];
        let csvData = null;
        let currentReplayId = null;

        // Tab switching
        function switchTrainingTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');

            // Load data for specific tabs
            if (tabName === 'scenarios') {
                loadScenarios();
            } else if (tabName === 'leaderboard') {
                loadLeaderboard();
            }
        }

        // Notification system
        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        // Single fault injection
        async function injectSingleFault() {
            const sensorPath = document.getElementById('inject-sensor-path').value;
            const value = parseFloat(document.getElementById('inject-value').value);
            const duration = parseInt(document.getElementById('inject-duration').value);

            if (!sensorPath || isNaN(value) || isNaN(duration)) {
                showNotification('Please fill all fields', 'error');
                return;
            }

            try {
                const response = await fetch('/api/training/inject_data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sensor_path: sensorPath, value, duration_seconds: duration })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification(`Fault injected: ${sensorPath} = ${value}`);
                } else {
                    showNotification(data.error || 'Failed to inject fault', 'error');
                }
            } catch (error) {
                showNotification('Network error: ' + error.message, 'error');
            }
        }

        // Batch operations
        function addToBatch() {
            const sensorPath = document.getElementById('inject-sensor-path').value;
            const value = parseFloat(document.getElementById('inject-value').value);
            const duration = parseInt(document.getElementById('inject-duration').value);

            if (!sensorPath || isNaN(value) || isNaN(duration)) {
                showNotification('Please fill all fields', 'error');
                return;
            }

            batchInjections.push({ sensor_path: sensorPath, value, duration_seconds: duration });
            updateBatchList();
            showNotification('Added to batch');
        }

        function updateBatchList() {
            const list = document.getElementById('batch-injection-list');
            if (batchInjections.length === 0) {
                list.innerHTML = '<p style="color: #6b7280; text-align: center;">No injections added yet</p>';
                return;
            }

            list.innerHTML = batchInjections.map((inj, idx) => `
                <div class="injection-item">
                    <span>${inj.sensor_path} = ${inj.value} (${inj.duration_seconds}s)</span>
                    <button class="btn-training btn-danger" style="padding: 4px 8px; font-size: 12px;"
                            onclick="removeFromBatch(${idx})">Remove</button>
                </div>
            `).join('');
        }

        function removeFromBatch(idx) {
            batchInjections.splice(idx, 1);
            updateBatchList();
        }

        function clearBatch() {
            batchInjections = [];
            updateBatchList();
            showNotification('Batch cleared');
        }

        async function executeBatch() {
            if (batchInjections.length === 0) {
                showNotification('No injections in batch', 'error');
                return;
            }

            try {
                const response = await fetch('/api/training/inject_batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ injections: batchInjections })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification(`Batch executed: ${data.succeeded}/${data.total} succeeded`);
                    clearBatch();
                } else {
                    showNotification('Batch execution failed', 'error');
                }
            } catch (error) {
                showNotification('Network error: ' + error.message, 'error');
            }
        }

        // Scenario operations
        function addScenarioInjection() {
            const sensorPath = document.getElementById('scenario-inject-sensor').value;
            const value = parseFloat(document.getElementById('scenario-inject-value').value);
            const atSecond = parseInt(document.getElementById('scenario-inject-time').value);

            if (!sensorPath || isNaN(value) || isNaN(atSecond)) {
                showNotification('Please fill all injection fields', 'error');
                return;
            }

            scenarioInjections.push({ sensor_path: sensorPath, value, at_second: atSecond });
            scenarioInjections.sort((a, b) => a.at_second - b.at_second);
            updateScenarioInjectionList();
            showNotification('Injection added to scenario');
        }

        function updateScenarioInjectionList() {
            const list = document.getElementById('scenario-injection-list');
            if (scenarioInjections.length === 0) {
                list.innerHTML = '<p style="color: #6b7280; text-align: center;">No injections added yet</p>';
                return;
            }

            list.innerHTML = scenarioInjections.map((inj, idx) => `
                <div class="injection-item">
                    <span>@${inj.at_second}s: ${inj.sensor_path} = ${inj.value}</span>
                    <button class="btn-training btn-danger" style="padding: 4px 8px; font-size: 12px;"
                            onclick="removeScenarioInjection(${idx})">Remove</button>
                </div>
            `).join('');
        }

        function removeScenarioInjection(idx) {
            scenarioInjections.splice(idx, 1);
            updateScenarioInjectionList();
        }

        async function createScenario() {
            const name = document.getElementById('scenario-name').value;
            const description = document.getElementById('scenario-description').value;
            const industry = document.getElementById('scenario-industry').value;
            const difficulty = document.getElementById('scenario-difficulty').value;
            const duration = parseInt(document.getElementById('scenario-duration').value);
            const tags = document.getElementById('scenario-tags').value.split(',').map(t => t.trim());

            if (!name || scenarioInjections.length === 0) {
                showNotification('Please provide name and at least one injection', 'error');
                return;
            }

            try {
                const response = await fetch('/api/training/create_scenario', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name, description, industry, difficulty, duration_seconds: duration, tags,
                        injections: scenarioInjections
                    })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification(`Scenario created: ${name}`);
                    scenarioInjections = [];
                    updateScenarioInjectionList();
                    document.getElementById('scenario-name').value = '';
                    document.getElementById('scenario-description').value = '';
                    loadScenarios();
                } else {
                    showNotification(data.error || 'Failed to create scenario', 'error');
                }
            } catch (error) {
                showNotification('Network error: ' + error.message, 'error');
            }
        }

        async function loadScenarios() {
            try {
                const response = await fetch('/api/training/scenarios');
                const data = await response.json();

                const container = document.getElementById('scenarios-list');
                if (!data.success || data.scenarios.length === 0) {
                    container.innerHTML = '<p style="color: #6b7280;">No scenarios yet. Create one above!</p>';
                    return;
                }

                container.innerHTML = data.scenarios.map(scenario => `
                    <div class="training-card">
                        <h3>${scenario.name}</h3>
                        <p style="color: #6b7280; font-size: 14px; margin: 8px 0;">
                            ${scenario.description}
                        </p>
                        <div style="margin: 10px 0;">
                            <span class="difficulty-badge difficulty-${scenario.difficulty}">
                                ${scenario.difficulty.toUpperCase()}
                            </span>
                            <span style="color: #6b7280; font-size: 13px;">
                                ${scenario.duration_seconds}s • ${scenario.injections.length} steps
                            </span>
                        </div>
                        <div style="margin-top: 10px;">
                            ${scenario.tags.map(tag => `
                                <span style="background: #e5e7eb; padding: 2px 8px; border-radius: 3px;
                                             font-size: 12px; margin-right: 5px;">${tag}</span>
                            `).join('')}
                        </div>
                        <button class="btn-training btn-success" style="margin-top: 15px; width: 100%;"
                                onclick="runScenario('${scenario.scenario_id}', '${scenario.name}')">
                            Run Scenario
                        </button>
                    </div>
                `).join('');
            } catch (error) {
                document.getElementById('scenarios-list').innerHTML =
                    '<p style="color: #EF4444;">Failed to load scenarios</p>';
            }
        }

        async function runScenario(scenarioId, scenarioName) {
            const traineeId = prompt('Enter your trainee ID:', 'trainee_user');
            if (!traineeId) return;

            try {
                const response = await fetch('/api/training/run_scenario', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scenario_id: scenarioId, trainee_id: traineeId })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification(`Scenario "${scenarioName}" started! Duration: ${data.duration_seconds}s`);
                } else {
                    showNotification(data.error || 'Failed to run scenario', 'error');
                }
            } catch (error) {
                showNotification('Network error: ' + error.message, 'error');
            }
        }

        // CSV operations
        function handleCSVDragOver(e) {
            e.preventDefault();
            e.currentTarget.classList.add('dragover');
        }

        function handleCSVDragLeave(e) {
            e.currentTarget.classList.remove('dragover');
        }

        function handleCSVDrop(e) {
            e.preventDefault();
            e.currentTarget.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                processCSVFile(files[0]);
            }
        }

        function handleCSVFileSelect(e) {
            const files = e.target.files;
            if (files.length > 0) {
                processCSVFile(files[0]);
            }
        }

        async function processCSVFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/training/upload_csv', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (data.success) {
                    currentReplayId = data.replay_id;
                    showNotification(`CSV uploaded: ${data.rows_loaded} rows`);

                    // Show preview
                    document.getElementById('csv-preview').style.display = 'block';
                    document.getElementById('csv-preview-content').innerHTML = `
                        <p><strong>Replay ID:</strong> ${data.replay_id}</p>
                        <p><strong>Rows:</strong> ${data.rows_loaded}</p>
                        <p><strong>File:</strong> ${file.name}</p>
                    `;
                } else {
                    showNotification(data.error || 'Failed to upload CSV', 'error');
                }
            } catch (error) {
                showNotification('Network error: ' + error.message, 'error');
            }
        }

        async function startCSVReplay() {
            if (!currentReplayId) {
                showNotification('No CSV uploaded', 'error');
                return;
            }

            const speed = parseFloat(document.getElementById('csv-replay-speed').value);

            try {
                const response = await fetch('/api/training/start_replay', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ replay_id: currentReplayId, speed })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification(`Replay started at ${speed}x speed`);
                } else {
                    showNotification(data.error || 'Failed to start replay', 'error');
                }
            } catch (error) {
                showNotification('Network error: ' + error.message, 'error');
            }
        }

        function clearCSV() {
            currentReplayId = null;
            document.getElementById('csv-preview').style.display = 'none';
            document.getElementById('csv-file-input').value = '';
            showNotification('CSV cleared');
        }

        // Leaderboard
        async function loadLeaderboard() {
            try {
                const response = await fetch('/api/training/leaderboard');
                const data = await response.json();

                const tbody = document.getElementById('leaderboard-body');
                if (!data.success || data.leaderboard.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="7" style="text-align: center; color: #6b7280;">
                                No training data yet
                            </td>
                        </tr>
                    `;
                    return;
                }

                tbody.innerHTML = data.leaderboard.map((entry, idx) => {
                    const rank = idx + 1;
                    const rankClass = rank <= 3 ? `rank-${rank}` : '';
                    return `
                        <tr>
                            <td class="${rankClass}">#${rank}</td>
                            <td>${entry.trainee_id}</td>
                            <td>${entry.attempts}</td>
                            <td>${entry.correct}</td>
                            <td><strong>${entry.avg_score.toFixed(1)}</strong></td>
                            <td>${entry.avg_time.toFixed(1)}s</td>
                            <td>${entry.accuracy.toFixed(1)}%</td>
                        </tr>
                    `;
                }).join('');
            } catch (error) {
                document.getElementById('leaderboard-body').innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align: center; color: #EF4444;">
                            Failed to load leaderboard
                        </td>
                    </tr>
                `;
            }
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Training UI initialized');
        });
    </script>
    """


__all__ = ["get_training_ui_html"]
