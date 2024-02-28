-- # Copyright 2024 Google LLC
-- #
-- # Licensed under the Apache License, Version 2.0 (the "License");
-- # you may not use this file except in compliance with the License.
-- # You may obtain a copy of the License at
-- #
-- #    http://www.apache.org/licenses/LICENSE-2.0
-- #
-- # Unless required by applicable law or agreed to in writing, software
-- # distributed under the License is distributed on an "AS IS" BASIS,
-- # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- # See the License for the specific language governing permissions and
-- # limitations under the License.

CREATE TABLE `<PROJECT_ID>.<DATASET_ID>.<TABLE_ID>`
(
  business_keys ARRAY<STRUCT<value STRING, name STRING>>,
  image_embedding ARRAY<FLOAT64>,
  text_embedding ARRAY<FLOAT64>,
  categories ARRAY<STRUCT<children ARRAY<STRUCT<children ARRAY<STRUCT<children ARRAY<STRUCT<children ARRAY<STRING>, name STRING, id STRING>>, name STRING, id STRING>>, name STRING, id STRING>>, name STRING, id STRING>>,
  base_price STRUCT<rounding_rule STRUCT<trim_insignificant_digits BOOL, relevant_decimal INT64>, value STRUCT<decimal INT64, whole INT64>, code STRING>,
  headers ARRAY<STRUCT<attribute_values ARRAY<STRUCT<string_value STRING, template_attribute_rule STRUCT<required BOOL, field_type STRING, allow_overrides BOOL, name STRING>>>, images ARRAY<STRUCT<url STRING, origin_url STRING>>, nlp_description STRING, locale STRING, long_description STRING, short_description STRING, brand STRING, name STRING>>
);