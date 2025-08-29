# Copyright 2024 Google, LLC.
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
product_attributes = [
    {
        "name": "Product Identification & Core Information",
        "attributes": [
            { "name": "ProductID", "type": "String/Number" },
            { "name": "SKU", "type": "String" },
            { "name": "UPC", "type": "String" },
            { "name": "EAN", "type": "String" },
            { "name": "GTIN", "type": "String" },
            { "name": "ProductName", "type": "String" },
            { "name": "BrandName", "type": "String" },
            { "name": "ProductDescriptionShort", "type": "String" },
            { "name": "ProductDescriptionLong", "type": "Text" },
            { "name": "ProductType", "type": "String" },
            { "name": "SubCategory", "type": "String" },
            { "name": "ModelNumber", "type": "String" },
            { "name": "SerialNumber", "type": "String" },
            { "name": "IsActive", "type": "Boolean" }
        ]
    },
    {
        "name": "Physical Attributes",
        "attributes": [
            { "name": "Height", "type": "Number" },
            { "name": "Width", "type": "Number" },
            { "name": "Depth", "type": "Number" },
            { "name": "WeightNet", "type": "Number" },
            { "name": "WeightGross", "type": "Number" },
            { "name": "Color", "type": "String" },
            { "name": "ColorFamily", "type": "String" },
            { "name": "Material", "type": "String" },
            { "name": "Finish", "type": "String" },
            { "name": "Shape", "type": "String" },
            { "name": "Size", "type": "String" },
            { "name": "PackQuantity", "type": "Integer" },
            { "name": "Volume", "type": "Number" }
        ]
    },
    {
        "name": "Pricing & Sales Information",
        "attributes": [
            { "name": "CostPrice", "type": "Currency" },
            { "name": "RetailPrice", "type": "Currency" },
            { "name": "SalePrice", "type": "Currency" },
            { "name": "Discount", "type": "Number" },
            { "name": "IsTaxable", "type": "Boolean" },
            { "name": "TaxCode", "type": "String/Number" },
            { "name": "Currency", "type": "String" },
            { "name": "UnitOfMeasure", "type": "String" },
            { "name": "IsAvailableForSale", "type": "Boolean" }
        ]
    },
    {
        "name": "Logistics & Inventory",
        "attributes": [
            { "name": "QuantityOnHand", "type": "Integer" },
            { "name": "ReorderLevel", "type": "Integer" },
            { "name": "SupplierName", "type": "String" },
            { "name": "CountryOfOrigin", "type": "String" },
            { "name": "WarehouseLocation", "type": "String" },
            { "name": "ShippingClass", "type": "String" },
            { "name": "IsShippable", "type": "Boolean" },
            { "name": "LeadTime", "type": "Number" },
            { "name": "IsDangerousGood", "type": "Boolean" },
            { "name": "HSCode", "type": "String" }
        ]
    },
    {
        "name": "Perishable Goods Attributes",
        "attributes": [
            { "name": "ManufactureDate", "type": "Date" },
            { "name": "ExpirationDate", "type": "Date" },
            { "name": "BestBeforeDate", "type": "Date" },
            { "name": "SellByDate", "type": "Date" },
            { "name": "LotNumber", "type": "String" },
            { "name": "StorageConditions", "type": "String" },
            { "name": "Ingredients", "type": "Array" },
            { "name": "AllergenInfo", "type": "Array" },
            { "name": "NutritionalFacts", "type": "Object" },
            { "name": "IsOrganic", "type": "Boolean" },
            { "name": "IsGmoFree", "type": "Boolean" }
        ]
    },
    {
        "name": "Durable Goods & Technical Specs",
        "attributes": [
            { "name": "WarrantyPeriod", "type": "String" },
            { "name": "WarrantyInfo", "type": "Text" },
            { "name": "PowerSource", "type": "String" },
            { "name": "Voltage", "type": "String" },
            { "name": "EnergyEfficiencyRating", "type": "String" },
            { "name": "IsAssemblyRequired", "type": "Boolean" },
            { "name": "IncludedAccessories", "type": "Array" }
        ]
    },
    {
        "name": "Marketing & Media",
        "attributes": [
            { "name": "ImageUrlMain", "type": "URL" },
            { "name": "ImageUrlGallery", "type": "Array" },
            { "name": "VideoURL", "type": "URL" },
            { "name": "MetaTitle", "type": "String" },
            { "name": "MetaDescription", "type": "String" },
            { "name": "Tags", "type": "Array" },
            { "name": "CustomerReviews", "type": "Array" },
            { "name": "AverageRating", "type": "Number" },
            { "name": "RelatedProducts", "type": "Array" },
            { "name": "UpsellProducts", "type": "Array" }
        ]
    },
    {
        "name": "Compliance & Other",
        "attributes": [
            { "name": "DateCreated", "type": "Timestamp" },
            { "name": "LastModifiedDate", "type": "Timestamp" },
            { "name": "Certifications", "type": "Array" },
            { "name": "SafetyWarnings", "type": "Text" },
            { "name": "DocumentationURL", "type": "URL" },
            { "name": "DiscontinuationDate", "type": "Date" }
        ]
    }
]

def get_common_attributes_and_types() -> list[dict]:
    return product_attributes
