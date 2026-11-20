# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Hermetic security tests for embeddings.get_embedding() (applied & legacy)."""

import builtins
import importlib.util
import os
import pathlib
import sys
import unittest
from unittest import mock

_THIS_DIR = pathlib.Path(__file__).resolve().parent
_EXPERIMENTS_DIR = _THIS_DIR.parents[4]
if str(_EXPERIMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENTS_DIR))

os.environ.setdefault("APPLIED_AI_CONF", str(_EXPERIMENTS_DIR / "conf" / "app.toml"))

from google.cloud.ml.applied.embeddings import embeddings as applied_embeddings


def _load_legacy_embeddings():
    legacy_dir = _EXPERIMENTS_DIR / "legacy" / "backend"
    if str(legacy_dir) not in sys.path:
        sys.path.insert(0, str(legacy_dir))
    spec = importlib.util.spec_from_file_location(
        "legacy_backend_embeddings", legacy_dir / "embeddings.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


legacy_embeddings = _load_legacy_embeddings()


def _make_mock_prediction_response():
    resp = mock.MagicMock()
    resp.predictions = [
        {
            "textEmbedding": [0.1, 0.2],
            "imageEmbedding": [0.3, 0.4],
        }
    ]
    return resp


class EmbeddingsSecurityTest(unittest.TestCase):
    def setUp(self):
        self._env_patcher = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patcher.start()
        for key in (
            "ALLOWED_IMAGE_GCS_BUCKETS",
            "ALLOWED_GCS_BUCKETS",
            "ALLOWED_IMAGE_GCS_PREFIXES",
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        self._env_patcher.stop()

    def _build_applied_client(self):
        with mock.patch("google.cloud.aiplatform.gapic.PredictionServiceClient") as m:
            m.return_value.predict.return_value = _make_mock_prediction_response()
            return applied_embeddings.EmbeddingPredictionClient(), m.return_value

    def _build_legacy_client(self):
        with mock.patch("google.cloud.aiplatform.gapic.PredictionServiceClient") as m:
            m.return_value.predict.return_value = _make_mock_prediction_response()
            return legacy_embeddings.EmbeddingPredictionClient("test-project"), m.return_value

    def test_blocks_local_file_open_in_both_variants(self):
        applied_client, applied_gapic = self._build_applied_client()
        legacy_client, legacy_gapic = self._build_legacy_client()

        for label, client, gapic in (
            ("applied", applied_client, applied_gapic),
            ("legacy", legacy_client, legacy_gapic),
        ):
            for malicious_path in (
                "/etc/shadow",
                "/proc/self/environ",
                "file:///etc/passwd",
                "../conf/app.toml",
                "https://169.254.169.254/computeMetadata/v1/",
            ):
                with self.subTest(variant=label, path=malicious_path):
                    with mock.patch.object(builtins, "open") as mock_open:
                        with self.assertRaises(ValueError):
                            client.get_embedding(
                                text="shirt", image=malicious_path, base64=False
                            )
                        mock_open.assert_not_called()
                        gapic.predict.assert_not_called()

    def test_fails_closed_when_gcs_allowlist_unset_and_blocks_cross_bucket_read(self):
        applied_client, applied_gapic = self._build_applied_client()
        legacy_client, legacy_gapic = self._build_legacy_client()

        for label, client, gapic in (
            ("applied", applied_client, applied_gapic),
            ("legacy", legacy_client, legacy_gapic),
        ):
            with self.subTest(variant=label, case="unset_allowlist"):
                with self.assertRaises(ValueError):
                    client.get_embedding(
                        text="shirt",
                        image="gs://attacker-chosen-bucket/exfil/private-key.bin",
                        base64=False,
                    )
                gapic.predict.assert_not_called()

            os.environ["ALLOWED_IMAGE_GCS_BUCKETS"] = "trusted-catalog-bucket"
            with self.subTest(variant=label, case="disallowed_bucket"):
                with self.assertRaises(ValueError):
                    client.get_embedding(
                        text="shirt",
                        image="gs://attacker-chosen-bucket/exfil/private-key.bin",
                        base64=False,
                    )
                gapic.predict.assert_not_called()

            with self.subTest(variant=label, case="traversal_in_allowed_bucket"):
                with self.assertRaises(ValueError):
                    client.get_embedding(
                        text="shirt",
                        image="gs://trusted-catalog-bucket/products/../../secret.bin",
                        base64=False,
                    )
                gapic.predict.assert_not_called()

            with self.subTest(variant=label, case="allowed_bucket_succeeds"):
                res = client.get_embedding(
                    text="shirt",
                    image="gs://trusted-catalog-bucket/products/item1.jpg",
                    base64=False,
                )
                self.assertEqual(res.image_embedding, [0.3, 0.4])
                gapic.predict.assert_called_once()
            os.environ.pop("ALLOWED_IMAGE_GCS_BUCKETS", None)

    def test_validates_base64_image_payload(self):
        applied_client, _ = self._build_applied_client()
        legacy_client, _ = self._build_legacy_client()

        valid_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        for label, client in (("applied", applied_client), ("legacy", legacy_client)):
            with self.subTest(variant=label, case="invalid_base64"):
                with self.assertRaises(ValueError):
                    client.get_embedding(
                        text="shirt", image="not!valid!base64", base64=True
                    )
            with self.subTest(variant=label, case="valid_base64"):
                res = client.get_embedding(text="shirt", image=valid_b64, base64=True)
                self.assertEqual(res.image_embedding, [0.3, 0.4])


if __name__ == "__main__":
    unittest.main()
