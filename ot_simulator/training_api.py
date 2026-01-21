"""Training API for manual data injection and fault scenarios.

Provides REST endpoints for:
- Manual sensor value injection
- Batch data injection
- CSV upload and replay
- Fault scenario creation/management
- Training assessment
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from aiohttp import web

logger = logging.getLogger("ot_simulator.training_api")


@dataclass
class FaultScenario:
    """Represents a training fault scenario."""
    scenario_id: str
    name: str
    description: str
    industry: str
    duration_seconds: float
    injections: list[dict[str, Any]]
    created_at: float
    tags: list[str]
    difficulty: str  # "beginner", "intermediate", "advanced"


@dataclass
class TrainingAssessment:
    """Represents a training assessment result."""
    trainee_id: str
    scenario_id: str
    start_time: float
    end_time: float
    actions: list[dict[str, Any]]
    diagnosis: str
    correct: bool
    score: float
    time_to_diagnose: float


class TrainingAPIHandler:
    """Handles training-specific API endpoints."""

    def __init__(self, simulator_manager):
        """Initialize training API handler.

        Args:
            simulator_manager: Reference to SimulatorManager for sensor access
        """
        self.simulator_manager = simulator_manager
        self.scenarios: dict[str, FaultScenario] = {}
        self.assessments: list[TrainingAssessment] = []
        self.scenarios_dir = Path("ot_simulator/scenarios")
        self.scenarios_dir.mkdir(exist_ok=True)

        # Load saved scenarios
        self._load_scenarios()

    def _load_scenarios(self):
        """Load saved scenarios from disk."""
        try:
            for scenario_file in self.scenarios_dir.glob("*.json"):
                with open(scenario_file, 'r') as f:
                    data = json.load(f)
                    scenario = FaultScenario(**data)
                    self.scenarios[scenario.scenario_id] = scenario
            logger.info(f"Loaded {len(self.scenarios)} saved scenarios")
        except Exception as e:
            logger.error(f"Failed to load scenarios: {e}")

    def _save_scenario(self, scenario: FaultScenario):
        """Save scenario to disk."""
        try:
            scenario_file = self.scenarios_dir / f"{scenario.scenario_id}.json"
            with open(scenario_file, 'w') as f:
                json.dump(asdict(scenario), f, indent=2)
            logger.info(f"Saved scenario: {scenario.name}")
        except Exception as e:
            logger.error(f"Failed to save scenario: {e}")

    async def handle_inject_data(self, request: web.Request) -> web.Response:
        """Inject a single sensor value.

        POST /api/training/inject_data
        Body: {
            "sensor_path": "mining.crusher.bearing_temp",
            "value": 95.5,
            "duration_seconds": 60
        }
        """
        try:
            data = await request.json()
            sensor_path = data.get("sensor_path")
            value = data.get("value")
            duration_seconds = data.get("duration_seconds", 0)

            if not sensor_path or value is None:
                return web.json_response({
                    "success": False,
                    "error": "Missing sensor_path or value"
                }, status=400)

            # Inject fault via simulator manager
            success = self.simulator_manager.inject_fault(
                sensor_path=sensor_path,
                fault_type="fixed_value",
                params={"value": value},
                duration=duration_seconds
            )

            if success:
                return web.json_response({
                    "success": True,
                    "message": f"Injected value {value} to {sensor_path}",
                    "sensor_path": sensor_path,
                    "value": value,
                    "duration_seconds": duration_seconds
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Sensor not found: {sensor_path}"
                }, status=404)

        except Exception as e:
            logger.error(f"Error injecting data: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_inject_batch(self, request: web.Request) -> web.Response:
        """Inject multiple sensor values at once.

        POST /api/training/inject_batch
        Body: {
            "injections": [
                {"sensor_path": "mining.crusher.bearing_temp", "value": 95.5, "duration_seconds": 60},
                {"sensor_path": "mining.crusher.vibration", "value": 8.2, "duration_seconds": 60}
            ]
        }
        """
        try:
            data = await request.json()
            injections = data.get("injections", [])

            if not injections:
                return web.json_response({
                    "success": False,
                    "error": "No injections provided"
                }, status=400)

            results = []
            for injection in injections:
                sensor_path = injection.get("sensor_path")
                value = injection.get("value")
                duration_seconds = injection.get("duration_seconds", 0)

                if not sensor_path or value is None:
                    results.append({
                        "success": False,
                        "sensor_path": sensor_path,
                        "error": "Missing sensor_path or value"
                    })
                    continue

                success = self.simulator_manager.inject_fault(
                    sensor_path=sensor_path,
                    fault_type="fixed_value",
                    params={"value": value},
                    duration=duration_seconds
                )

                results.append({
                    "success": success,
                    "sensor_path": sensor_path,
                    "value": value,
                    "error": None if success else "Sensor not found"
                })

            return web.json_response({
                "success": True,
                "results": results,
                "total": len(injections),
                "succeeded": sum(1 for r in results if r["success"])
            })

        except Exception as e:
            logger.error(f"Error injecting batch: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_upload_csv(self, request: web.Request) -> web.Response:
        """Upload CSV file with sensor data for replay.

        POST /api/training/upload_csv
        multipart/form-data with file field

        CSV Format:
        timestamp,sensor_path,value
        2025-01-19T10:00:00,mining.crusher.bearing_temp,75.5
        2025-01-19T10:00:01,mining.crusher.bearing_temp,76.2
        """
        try:
            reader = await request.multipart()
            field = await reader.next()

            if not field or field.name != 'file':
                return web.json_response({
                    "success": False,
                    "error": "No file uploaded"
                }, status=400)

            # Read CSV content
            content = await field.read(decode=True)
            csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))

            # Parse CSV rows
            rows = []
            for row in csv_reader:
                try:
                    rows.append({
                        "timestamp": row.get("timestamp"),
                        "sensor_path": row.get("sensor_path"),
                        "value": float(row.get("value"))
                    })
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row: {row}, error: {e}")

            if not rows:
                return web.json_response({
                    "success": False,
                    "error": "No valid rows found in CSV"
                }, status=400)

            # Store for replay
            replay_id = f"replay_{int(time.time() * 1000)}"
            self.simulator_manager.set_replay_data(replay_id, rows)

            return web.json_response({
                "success": True,
                "replay_id": replay_id,
                "rows_loaded": len(rows),
                "message": f"CSV uploaded successfully with {len(rows)} rows"
            })

        except Exception as e:
            logger.error(f"Error uploading CSV: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_start_replay(self, request: web.Request) -> web.Response:
        """Start replaying uploaded CSV data.

        POST /api/training/start_replay
        Body: {
            "replay_id": "replay_1234567890",
            "speed": 1.0  # 1x = real-time, 10x = 10x faster
        }
        """
        try:
            data = await request.json()
            replay_id = data.get("replay_id")
            speed = data.get("speed", 1.0)

            if not replay_id:
                return web.json_response({
                    "success": False,
                    "error": "Missing replay_id"
                }, status=400)

            # Start replay task
            success = self.simulator_manager.start_replay(replay_id, speed)

            if success:
                return web.json_response({
                    "success": True,
                    "replay_id": replay_id,
                    "speed": speed,
                    "message": "Replay started"
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Replay ID not found: {replay_id}"
                }, status=404)

        except Exception as e:
            logger.error(f"Error starting replay: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_create_scenario(self, request: web.Request) -> web.Response:
        """Create a new fault scenario.

        POST /api/training/create_scenario
        Body: {
            "name": "Bearing Overheating Scenario",
            "description": "Gradual bearing temperature increase leading to failure",
            "industry": "mining",
            "duration_seconds": 300,
            "difficulty": "intermediate",
            "tags": ["bearing", "temperature", "failure"],
            "injections": [
                {"sensor_path": "mining.crusher.bearing_temp", "value": 85, "at_second": 0},
                {"sensor_path": "mining.crusher.bearing_temp", "value": 95, "at_second": 120},
                {"sensor_path": "mining.crusher.bearing_temp", "value": 105, "at_second": 240}
            ]
        }
        """
        try:
            data = await request.json()

            scenario_id = f"scenario_{int(time.time() * 1000)}"
            scenario = FaultScenario(
                scenario_id=scenario_id,
                name=data.get("name", "Untitled Scenario"),
                description=data.get("description", ""),
                industry=data.get("industry", "general"),
                duration_seconds=data.get("duration_seconds", 60),
                injections=data.get("injections", []),
                created_at=time.time(),
                tags=data.get("tags", []),
                difficulty=data.get("difficulty", "beginner")
            )

            # Save scenario
            self.scenarios[scenario_id] = scenario
            self._save_scenario(scenario)

            return web.json_response({
                "success": True,
                "scenario_id": scenario_id,
                "scenario": asdict(scenario)
            })

        except Exception as e:
            logger.error(f"Error creating scenario: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_list_scenarios(self, request: web.Request) -> web.Response:
        """List all available fault scenarios.

        GET /api/training/scenarios?industry=mining&difficulty=beginner
        """
        try:
            # Get query parameters for filtering
            industry = request.query.get("industry")
            difficulty = request.query.get("difficulty")

            scenarios = list(self.scenarios.values())

            # Apply filters
            if industry:
                scenarios = [s for s in scenarios if s.industry == industry]
            if difficulty:
                scenarios = [s for s in scenarios if s.difficulty == difficulty]

            return web.json_response({
                "success": True,
                "scenarios": [asdict(s) for s in scenarios],
                "total": len(scenarios)
            })

        except Exception as e:
            logger.error(f"Error listing scenarios: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_run_scenario(self, request: web.Request) -> web.Response:
        """Run a saved fault scenario.

        POST /api/training/run_scenario
        Body: {
            "scenario_id": "scenario_1234567890",
            "trainee_id": "trainee_john_doe"
        }
        """
        try:
            data = await request.json()
            scenario_id = data.get("scenario_id")
            trainee_id = data.get("trainee_id", "anonymous")

            if not scenario_id:
                return web.json_response({
                    "success": False,
                    "error": "Missing scenario_id"
                }, status=400)

            scenario = self.scenarios.get(scenario_id)
            if not scenario:
                return web.json_response({
                    "success": False,
                    "error": f"Scenario not found: {scenario_id}"
                }, status=404)

            # Start scenario execution in background
            asyncio.create_task(self._execute_scenario(scenario, trainee_id))

            return web.json_response({
                "success": True,
                "scenario_id": scenario_id,
                "trainee_id": trainee_id,
                "message": f"Scenario '{scenario.name}' started",
                "duration_seconds": scenario.duration_seconds
            })

        except Exception as e:
            logger.error(f"Error running scenario: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _execute_scenario(self, scenario: FaultScenario, trainee_id: str):
        """Execute a fault scenario asynchronously."""
        try:
            logger.info(f"Starting scenario '{scenario.name}' for trainee {trainee_id}")
            start_time = time.time()

            # Sort injections by at_second
            sorted_injections = sorted(scenario.injections, key=lambda x: x.get("at_second", 0))

            # Execute each injection at the scheduled time
            for injection in sorted_injections:
                at_second = injection.get("at_second", 0)

                # Wait until scheduled time
                elapsed = time.time() - start_time
                if elapsed < at_second:
                    await asyncio.sleep(at_second - elapsed)

                # Inject the fault
                sensor_path = injection.get("sensor_path")
                value = injection.get("value")
                duration = injection.get("duration_seconds", 0)

                if sensor_path and value is not None:
                    self.simulator_manager.inject_fault(
                        sensor_path=sensor_path,
                        fault_type="fixed_value",
                        params={"value": value},
                        duration=duration
                    )
                    logger.info(f"Injected {sensor_path}={value} at {at_second}s")

            logger.info(f"Scenario '{scenario.name}' completed")

        except Exception as e:
            logger.error(f"Error executing scenario: {e}")

    async def handle_submit_diagnosis(self, request: web.Request) -> web.Response:
        """Submit trainee diagnosis for assessment.

        POST /api/training/submit_diagnosis
        Body: {
            "trainee_id": "trainee_john_doe",
            "scenario_id": "scenario_1234567890",
            "diagnosis": "bearing_failure",
            "actions": [
                {"action": "viewed_chart", "sensor": "bearing_temp", "timestamp": 1234567890},
                {"action": "injected_fault", "sensor": "vibration", "timestamp": 1234567891}
            ]
        }
        """
        try:
            data = await request.json()
            trainee_id = data.get("trainee_id")
            scenario_id = data.get("scenario_id")
            diagnosis = data.get("diagnosis")
            actions = data.get("actions", [])

            if not trainee_id or not scenario_id or not diagnosis:
                return web.json_response({
                    "success": False,
                    "error": "Missing required fields"
                }, status=400)

            # Get scenario
            scenario = self.scenarios.get(scenario_id)
            if not scenario:
                return web.json_response({
                    "success": False,
                    "error": f"Scenario not found: {scenario_id}"
                }, status=404)

            # Calculate score (simplified grading logic)
            # In production, this would use ML model or rule-based system
            correct = self._grade_diagnosis(scenario, diagnosis)
            score = 100.0 if correct else 0.0

            # Calculate time to diagnose
            if actions:
                start_time = min(a.get("timestamp", time.time()) for a in actions)
                end_time = max(a.get("timestamp", time.time()) for a in actions)
                time_to_diagnose = end_time - start_time
            else:
                time_to_diagnose = 0

            # Create assessment
            assessment = TrainingAssessment(
                trainee_id=trainee_id,
                scenario_id=scenario_id,
                start_time=actions[0].get("timestamp", time.time()) if actions else time.time(),
                end_time=time.time(),
                actions=actions,
                diagnosis=diagnosis,
                correct=correct,
                score=score,
                time_to_diagnose=time_to_diagnose
            )

            self.assessments.append(assessment)

            return web.json_response({
                "success": True,
                "assessment": asdict(assessment),
                "message": "Diagnosis submitted successfully"
            })

        except Exception as e:
            logger.error(f"Error submitting diagnosis: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    def _grade_diagnosis(self, scenario: FaultScenario, diagnosis: str) -> bool:
        """Grade diagnosis against scenario.

        Simplified grading logic. In production, use ML model or rule engine.
        """
        # Check if diagnosis matches scenario tags
        diagnosis_lower = diagnosis.lower()
        for tag in scenario.tags:
            if tag.lower() in diagnosis_lower:
                return True
        return False

    async def handle_get_leaderboard(self, request: web.Request) -> web.Response:
        """Get training leaderboard.

        GET /api/training/leaderboard?scenario_id=scenario_1234567890
        """
        try:
            scenario_id = request.query.get("scenario_id")

            # Filter assessments
            assessments = self.assessments
            if scenario_id:
                assessments = [a for a in assessments if a.scenario_id == scenario_id]

            # Group by trainee
            trainee_scores: dict[str, dict[str, Any]] = {}
            for assessment in assessments:
                trainee_id = assessment.trainee_id
                if trainee_id not in trainee_scores:
                    trainee_scores[trainee_id] = {
                        "trainee_id": trainee_id,
                        "total_score": 0,
                        "attempts": 0,
                        "correct": 0,
                        "avg_time": 0,
                        "total_time": 0
                    }

                trainee_scores[trainee_id]["total_score"] += assessment.score
                trainee_scores[trainee_id]["attempts"] += 1
                trainee_scores[trainee_id]["correct"] += 1 if assessment.correct else 0
                trainee_scores[trainee_id]["total_time"] += assessment.time_to_diagnose

            # Calculate averages
            leaderboard = []
            for trainee_id, scores in trainee_scores.items():
                scores["avg_score"] = scores["total_score"] / scores["attempts"] if scores["attempts"] > 0 else 0
                scores["avg_time"] = scores["total_time"] / scores["attempts"] if scores["attempts"] > 0 else 0
                scores["accuracy"] = (scores["correct"] / scores["attempts"] * 100) if scores["attempts"] > 0 else 0
                leaderboard.append(scores)

            # Sort by avg_score descending
            leaderboard.sort(key=lambda x: x["avg_score"], reverse=True)

            return web.json_response({
                "success": True,
                "leaderboard": leaderboard,
                "total_trainees": len(leaderboard)
            })

        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_legacy_fault_inject(self, request: web.Request) -> web.Response:
        """Legacy fault injection endpoint for backward compatibility with LLM agent.

        POST /api/fault/inject
        Body: {
            "sensor_path": "mining/crusher_1_motor_power",
            "duration": 60
        }
        """
        try:
            data = await request.json()
            sensor_path = data.get("sensor_path")
            duration = data.get("duration", 10)

            if not sensor_path:
                return web.json_response({
                    "success": False,
                    "error": "Missing sensor_path"
                }, status=400)

            # Inject fault via simulator manager
            success = self.simulator_manager.inject_fault(
                sensor_path=sensor_path,
                fault_type="fixed_value",
                params={"value": 0},  # Default: set to 0 for legacy compatibility
                duration=duration
            )

            if success:
                return web.json_response({
                    "success": True,
                    "message": f"Fault injected into {sensor_path} for {duration} seconds"
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Sensor not found: {sensor_path}"
                }, status=404)

        except Exception as e:
            logger.error(f"Error injecting fault: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    def register_routes(self, app: web.Application):
        """Register training API routes."""
        # Training-specific endpoints
        app.router.add_post("/api/training/inject_data", self.handle_inject_data)
        app.router.add_post("/api/training/inject_batch", self.handle_inject_batch)
        app.router.add_post("/api/training/upload_csv", self.handle_upload_csv)
        app.router.add_post("/api/training/start_replay", self.handle_start_replay)
        app.router.add_post("/api/training/create_scenario", self.handle_create_scenario)
        app.router.add_get("/api/training/scenarios", self.handle_list_scenarios)
        app.router.add_post("/api/training/run_scenario", self.handle_run_scenario)
        app.router.add_post("/api/training/submit_diagnosis", self.handle_submit_diagnosis)
        app.router.add_get("/api/training/leaderboard", self.handle_get_leaderboard)

        # Legacy compatibility endpoint for LLM agent
        app.router.add_post("/api/fault/inject", self.handle_legacy_fault_inject)

        logger.info("Training API routes registered (9 endpoints + legacy fault endpoint)")
