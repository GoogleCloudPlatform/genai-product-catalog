# Copyright 2024 Google LLC
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

"""Hermetic unit tests for FastAPI authentication, tenant scoping, CORS, and BigQuery parameterization."""

import os
import pathlib
import sys
import unittest
from unittest import mock

_SERVICE_DIR = pathlib.Path(__file__).resolve().parent
_EXPERIMENTS_DIR = _SERVICE_DIR.parents[1]
for _p in (str(_SERVICE_DIR), str(_EXPERIMENTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("APPLIED_AI_CONF", str(_EXPERIMENTS_DIR / "conf" / "app.toml"))

with (
    mock.patch("google.cloud.bigquery.Client", autospec=True),
    mock.patch("vertexai.init"),
    mock.patch("vertexai.language_models.TextGenerationModel.from_pretrained"),
    mock.patch("vertexai.preview.generative_models.GenerativeModel", autospec=True),
    mock.patch("google.cloud.aiplatform_v1.IndexServiceClient", autospec=True),
    mock.patch("google.cloud.aiplatform.MatchingEngineIndexEndpoint", autospec=True),
):
    from fastapi.routing import APIRoute
    from fastapi.testclient import TestClient
    import auth
    import main
    from google.cloud.ml.applied.attributes import attributes
    from google.cloud.ml.applied.categories import category
    from google.cloud.ml.applied.embeddings import search


class FastAPIServiceSecurityTest(unittest.TestCase):
    def setUp(self):
        self._env_patcher = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patcher.start()
        for key in (
            "SERVICE_API_KEYS",
            "API_AUTH_TOKEN",
            "ALLOWED_OIDC_AUDIENCE",
            "ALLOWED_OIDC_EMAILS",
            "TRUST_OIDC_TENANT_CLAIM",
            "DEFAULT_TENANT_ID",
            "ALLOWED_CORS_ORIGINS",
        ):
            os.environ.pop(key, None)
        auth.reset_product_ownership_registry()
        self.client = TestClient(main.app)

    def tearDown(self):
        auth.reset_product_ownership_registry()
        self._env_patcher.stop()

    def test_route_security_requirements_and_dependencies_are_enforced(self):
        protected_prefixes = ("/products", "/images", "/categories")
        openapi_paths = main.app.openapi().get("paths", {})
        checked = 0
        for route in main.app.routes:
            if not isinstance(route, APIRoute):
                continue
            if route.path.startswith(protected_prefixes):
                checked += 1
                self.assertGreater(
                    len(route.dependencies),
                    0,
                    f"Expected router dependencies on {route.path}",
                )
                sec_reqs = getattr(
                    route.dependant,
                    "security_requirements",
                    getattr(route.dependant, "_security_dependencies", []),
                )
                self.assertGreater(
                    len(sec_reqs),
                    0,
                    f"Expected OpenAPI security requirements on {route.path}",
                )
                for method in route.methods or ():
                    op = openapi_paths.get(route.path, {}).get(method.lower(), {})
                    self.assertTrue(
                        op.get("security"),
                        f"Expected OpenAPI security schema on {method} {route.path}",
                    )
        self.assertGreaterEqual(checked, 8)

        # Health checks remain accessible and include security headers
        resp = self.client.get("/hello/readiness_check")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(resp.headers.get("x-frame-options"), "DENY")
        self.assertIn(
            "frame-ancestors 'none'",
            resp.headers.get("content-security-policy", ""),
        )

    def test_fails_closed_when_auth_not_configured(self):
        with mock.patch.object(search, "upsert_dp") as mock_upsert:
            resp = self.client.post(
                "/products/api/v1/genai/products",
                json={"id": "prod-1", "description": "Shirt", "category": ["Apparel"]},
            )
            self.assertEqual(resp.status_code, 503)
            mock_upsert.assert_not_called()

    def test_rejects_anonymous_and_invalid_credentials_on_all_crud_routes(self):
        os.environ["SERVICE_API_KEYS"] = "tenantA:secret-token-a,tenantB:secret-token-b"
        with (
            mock.patch.object(search, "upsert_dp") as mock_upsert,
            mock.patch.object(search, "delete_dp") as mock_delete,
        ):
            # Anonymous POST / PUT / DELETE
            r_post = self.client.post(
                "/products/api/v1/genai/products",
                json={"id": "ATTACKER_42", "description": "x", "category": ["Apparel"]},
            )
            self.assertEqual(r_post.status_code, 401)

            r_put = self.client.put(
                "/products/api/v1/genai/products/legit-001",
                json={"id": "legit-001", "description": "x"},
            )
            self.assertEqual(r_put.status_code, 401)

            r_del = self.client.delete("/products/api/v1/genai/products/legit-001")
            self.assertEqual(r_del.status_code, 401)

            # Invalid Bearer token and invalid X-API-Key
            r_bad_bearer = self.client.delete(
                "/products/api/v1/genai/products/legit-001",
                headers={"Authorization": "Bearer wrong-token"},
            )
            self.assertEqual(r_bad_bearer.status_code, 401)

            r_bad_key = self.client.delete(
                "/products/api/v1/genai/products/legit-001",
                headers={"X-API-Key": "wrong-token"},
            )
            self.assertEqual(r_bad_key.status_code, 401)

            mock_upsert.assert_not_called()
            mock_delete.assert_not_called()

    def test_per_tenant_namespacing_and_cross_tenant_delete_protection(self):
        os.environ["SERVICE_API_KEYS"] = "tenantA:secret-token-a,tenantB:secret-token-b"
        headers_a = {"Authorization": "Bearer secret-token-a"}
        headers_b = {"X-API-Key": "secret-token-b"}

        with (
            mock.patch.object(search, "upsert_dp") as mock_upsert,
            mock.patch.object(search, "delete_dp") as mock_delete,
        ):
            # Tenant A creates product legit-001 -> namespaced as tenantA__legit-001
            r_create = self.client.post(
                "/products/api/v1/genai/products",
                json={
                    "id": "legit-001",
                    "description": "Running shoes",
                    "category": ["Footwear"],
                    "image_uri": "gs://catalog-bucket/shoes/legit-001.jpg",
                },
                headers=headers_a,
            )
            self.assertEqual(r_create.status_code, 200)
            mock_upsert.assert_called_once_with(
                prod_id="tenantA__legit-001",
                desc="Running shoes",
                image="gs://catalog-bucket/shoes/legit-001.jpg",
                cat=["Footwear"],
            )

            # Tenant B attempts to delete Tenant A's product (unprefixed & prefixed) -> 403
            for target_id in ("legit-001", "tenantA__legit-001", "tenantA:legit-001"):
                with self.subTest(target_id=target_id):
                    r_cross_del = self.client.delete(
                        f"/products/api/v1/genai/products/{target_id}",
                        headers=headers_b,
                    )
                    self.assertEqual(r_cross_del.status_code, 403)

            # Tenant B attempts to overwrite Tenant A's product -> 403
            r_cross_put = self.client.put(
                "/products/api/v1/genai/products/legit-001",
                json={"id": "legit-001", "description": "Poisoned"},
                headers=headers_b,
            )
            self.assertEqual(r_cross_put.status_code, 403)
            mock_delete.assert_not_called()

            # Spoofed X-Tenant-ID header rejected -> 403
            r_spoof = self.client.delete(
                "/products/api/v1/genai/products/legit-001",
                headers={**headers_b, "X-Tenant-ID": "tenantA"},
            )
            self.assertEqual(r_spoof.status_code, 403)

            # Tenant A can update and delete its own product
            r_own_del = self.client.delete(
                "/products/api/v1/genai/products/legit-001",
                headers=headers_a,
            )
            self.assertEqual(r_own_del.status_code, 200)
            mock_delete.assert_called_once_with(prod_id="tenantA__legit-001")

    def test_oidc_token_authentication_supported(self):
        os.environ["ALLOWED_OIDC_AUDIENCE"] = "https://catalog-service.example.com"
        fake_claims = {
            "iss": "https://accounts.google.com",
            "sub": "1122334455",
            "email": "svc@example.com",
            "email_verified": True,
        }
        with (
            mock.patch(
                "google.oauth2.id_token.verify_oauth2_token",
                return_value=fake_claims,
            ) as mock_verify,
            mock.patch.object(search, "upsert_dp") as mock_upsert,
        ):
            resp = self.client.post(
                "/products/api/v1/genai/products",
                json={"id": "item-99", "description": "Jacket"},
                headers={"Authorization": "Bearer valid.oidc.jwt"},
            )
            self.assertEqual(resp.status_code, 200)
            mock_verify.assert_called_once()
            mock_upsert.assert_called_once_with(
                prod_id="oidc_1122334455__item-99",
                desc="Jacket",
                image=None,
                cat=[],
            )

    def test_rejects_sql_and_restrict_injection_payloads_and_local_image_paths(self):
        os.environ["API_AUTH_TOKEN"] = "single-service-secret"
        headers = {"Authorization": "Bearer single-service-secret"}

        with mock.patch.object(search, "upsert_dp") as mock_upsert:
            # SQL injection in product.id
            r_sqli_id = self.client.post(
                "/products/api/v1/genai/products",
                json={
                    "id": "p1'); DROP TABLE products; --",
                    "description": "Test",
                },
                headers=headers,
            )
            self.assertEqual(r_sqli_id.status_code, 400)

            # Injection in category restrict list
            r_bad_cat = self.client.post(
                "/products/api/v1/genai/products",
                json={
                    "id": "valid-id-1",
                    "description": "Test",
                    "category": ["Apparel'; DROP TABLE products; --"],
                },
                headers=headers,
            )
            self.assertEqual(r_bad_cat.status_code, 400)

            # Local file path in image_uri
            r_bad_img = self.client.post(
                "/products/api/v1/genai/products",
                json={
                    "id": "valid-id-1",
                    "description": "Test",
                    "image_uri": "/etc/passwd",
                },
                headers=headers,
            )
            self.assertEqual(r_bad_img.status_code, 400)

            # Mismatched path product_id and body product.id on PUT
            r_mismatch = self.client.put(
                "/products/api/v1/genai/products/id-one",
                json={"id": "id-two", "description": "Test"},
                headers=headers,
            )
            self.assertEqual(r_mismatch.status_code, 400)

            mock_upsert.assert_not_called()

    def test_cors_disallows_wildcard_and_untrusted_origins(self):
        # Verify wildcard is stripped even if set in ALLOWED_CORS_ORIGINS
        os.environ["ALLOWED_CORS_ORIGINS"] = "*,https://app.example.com"
        parsed = main.get_allowed_cors_origins()
        self.assertEqual(parsed, ["https://app.example.com"])
        self.assertNotIn("*", main.origins)

        # Untrusted origin gets no Access-Control-Allow-Origin header
        untrusted = self.client.options(
            "/hello/readiness_check",
            headers={
                "Origin": "https://attacker.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertIsNone(untrusted.headers.get("access-control-allow-origin"))

        # Allowed localhost origin succeeds
        trusted = self.client.options(
            "/hello/readiness_check",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(
            trusted.headers.get("access-control-allow-origin"),
            "http://localhost:8080",
        )

    def test_bigquery_queries_use_array_query_parameters(self):
        malicious_ids = ["legit_1", "x') UNION ALL SELECT session_user(), '1', '2' --"]

        # Test attributes.join_attributes_desc
        mock_job = mock.MagicMock()
        mock_job.result.return_value = []
        with (
            mock.patch.object(attributes.bq_client, "query", return_value=mock_job) as mock_bq_attr,
            mock.patch.object(
                attributes.Config,
                "value",
                side_effect=lambda section, key=None: {
                    "product_table": "proj.dataset.products",
                    "product_id_column": "id",
                    "product_attributes_column": "attributes",
                    "product_description_column": "description",
                }[key],
            ),
        ):
            attributes.join_attributes_desc(malicious_ids)
            mock_bq_attr.assert_called_once()
            sql_arg = mock_bq_attr.call_args.args[0]
            job_cfg = mock_bq_attr.call_args.kwargs["job_config"]
            self.assertIn("UNNEST(@ids)", sql_arg)
            self.assertNotIn("UNION ALL", sql_arg)
            self.assertEqual(len(job_cfg.query_parameters), 1)
            self.assertEqual(job_cfg.query_parameters[0].name, "ids")
            self.assertEqual(list(job_cfg.query_parameters[0].values), malicious_ids)

        # Test category.join_categories
        with (
            mock.patch.object(category.bq_client, "query", return_value=mock_job) as mock_bq_cat,
            mock.patch.object(category, "table_product", "proj.dataset.products"),
        ):
            category.join_categories(malicious_ids)
            mock_bq_cat.assert_called_once()
            sql_arg = mock_bq_cat.call_args.args[0]
            job_cfg = mock_bq_cat.call_args.kwargs["job_config"]
            self.assertIn("UNNEST(@ids)", sql_arg)
            self.assertNotIn("UNION ALL", sql_arg)
            self.assertEqual(len(job_cfg.query_parameters), 1)
            self.assertEqual(job_cfg.query_parameters[0].name, "ids")
            self.assertEqual(list(job_cfg.query_parameters[0].values), malicious_ids)


if __name__ == "__main__":
    unittest.main()
