from __future__ import annotations

import os
import unittest
import numpy as np
import torch
import torch.nn as nn

from edge.tflite_quantizer import EdgeModelExporter
from edge.fast_features import FastFeatureExtractor
from detection.ebpf_xdp_filter import eBPFXDPFilterEngine
from detection.modbus_dpi import ModbusDPIParser
from ha_cluster_sync import HAClusterSyncEngine
from mlops_drift_monitor import MLOpsDriftMonitor
from auth_oidc import OIDCAuthManager
from opentelemetry_exporter import OpenTelemetryExporter


class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 4)

    def forward(self, x):
        return self.fc(x)


class ProductionPillarsTest(unittest.TestCase):
    def test_pillar1_edge_exporter_and_quantizer(self) -> None:
        model = DummyModel()
        exporter = EdgeModelExporter(model, timesteps=30, n_features=4)
        weights = exporter.quantize_int8_weights()
        self.assertIn("fc.weight", weights)
        self.assertEqual(weights["fc.weight"].dtype, np.uint8)

    def test_pillar1_fast_feature_extractor(self) -> None:
        temps = np.array([20.0, 21.0, 22.0, 23.0, 24.0], dtype=np.float32)
        hums = np.array([50.0, 50.0, 50.0, 50.0, 50.0], dtype=np.float32)
        features = FastFeatureExtractor.extract_vector_features(temps, hums)
        self.assertAlmostEqual(features["temp_30_slope"], 1.0, delta=0.01)
        self.assertAlmostEqual(features["temp_hum_ratio"], 0.44, delta=0.05)

    def test_pillar2_ebpf_xdp_filter(self) -> None:
        filter_engine = eBPFXDPFilterEngine("eth0")
        record = filter_engine.block_ip_xdp("192.168.1.150", "DDoS Attack")
        self.assertEqual(record["action"], "XDP_DROP")
        self.assertTrue(filter_engine.is_ip_blocked("192.168.1.150"))
        self.assertTrue(filter_engine.unblock_ip_xdp("192.168.1.150"))
        self.assertFalse(filter_engine.is_ip_blocked("192.168.1.150"))

    def test_pillar2_modbus_dpi_parser(self) -> None:
        parser = ModbusDPIParser()
        valid, msg = parser.inspect_modbus_frame(1, 6, 40001, 22.5)
        self.assertTrue(valid)
        invalid, err_msg = parser.inspect_modbus_frame(1, 6, 40001, 99.0)
        self.assertFalse(invalid)
        self.assertIn("Out-of-bounds Register Write", err_msg)

    def test_pillar3_ha_cluster_sync(self) -> None:
        ha = HAClusterSyncEngine("Node_A", "BACKUP")
        new_role = ha.check_heartbeat("Node_B", last_seen_seconds=10.0)
        self.assertEqual(new_role, "PROMOTED_MASTER")
        ha.cloud_connected = False
        ha.queue_alert_telemetry({"alert": "Injection Attack"})
        self.assertEqual(len(ha.local_offline_queue), 1)
        ha.cloud_connected = True
        flushed = ha.flush_offline_queue()
        self.assertEqual(flushed, 1)

    def test_pillar4_mlops_drift_monitor(self) -> None:
        baseline = np.random.normal(20.0, 1.0, 100)
        shifted = np.random.normal(35.0, 5.0, 100)
        monitor = MLOpsDriftMonitor(baseline, psi_threshold=0.2)
        drifted, psi, _ = monitor.check_drift(shifted)
        self.assertTrue(drifted)
        self.assertGreater(psi, 0.2)

    def test_pillar5_oidc_auth_manager(self) -> None:
        oidc = OIDCAuthManager()
        # Header: {"alg":"HS256","typ":"JWT"} Payload: {"sub":"user123","exp":9999999999,"roles":["admin"]}
        import base64
        import json
        h_str = base64.urlsafe_b64encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode()).decode().rstrip("=")
        p_str = base64.urlsafe_b64encode(json.dumps({"sub":"user123","exp":9999999999,"roles":["admin"]}).encode()).decode().rstrip("=")
        mock_jwt = f"{h_str}.{p_str}.mock_sig"
        valid, uid, roles = oidc.validate_token(mock_jwt)
        self.assertTrue(valid)
        self.assertEqual(uid, "user123")
        self.assertIn("admin", roles)

    def test_pillar6_opentelemetry_exporter(self) -> None:
        otel = OpenTelemetryExporter()
        span = otel.start_span("inference_step")
        dur = otel.end_span(span)
        self.assertGreaterEqual(dur, 0.0)
        otel.record_count("attacks_detected", 1)
        data = otel.generate_otel_json()
        self.assertEqual(data["metrics"]["attacks_detected"], 1)


if __name__ == "__main__":
    unittest.main()
