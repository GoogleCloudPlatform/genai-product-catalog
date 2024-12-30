# Product Enrichment

## Introduction

This project introduces an intermediary to be executed prior to
search indexing. The following ideas and code are intended for customer use
and licensed according to open source licensing terms.

## Architecture

```mermaid
architecture-beta
    group api(cloud)[API]
    group on_prem(cloud)[On Prem]
    
    service catalog(database)[Catalog Data] in on_prem
    service web(server)[Management UI] in api
    service db(database)[Cloud SQL Postgres] in api
    service disk1(disk)[Google Cloud Storage] in api
    service disk2(disk)[Persistant Disk] in api
    service int_server(server)[Intermediary API] in api
    service enr_server(server)[Enrichment API] in api

    int_server:L --> R:catalog
    int_server:R --> L:disk1
    web:R --> L:enr_server
    enr_server:B -- T:disk1
    enr_server:R -- L:db
    disk2:T -- B:db

```

> Coming soon

## Workflow

```mermaid
sequenceDiagram
    Intermediary ->> Catalog:Get Item
    Intermediary -->> Gemini:Enrich Item
    Intermediary -->> Vertex:Generate Embeddings
    Intermediary -->> CloudSQL:Store Enriched Data and Embeddings
    EnrichmentAPI -->> CloudSQL:Search
    IndexingProcess -->> EnrichmentAPI:Read Enriched Data
    IndexingProcess -->> IndexingProcess:Generate Indexes
    IndexingProcess -->> ElasticSearch:Store
```

## Runtime Model

```mermaid
classDiagram
    SQLModel <|-- Product
    SQLModel <|-- ProductEmbeddings
    SQLModel <|-- Reviews
    SQLModel <|-- Review
    SQLModel <|-- ProductSpecification
    SQLModel <|-- ProductFeature
    SQLModel <|-- Image
    
    Image : +int id
    Image : +str url
    Image : +str mime_type
    Image : +str alt
    
    Product : +int id
    Product : +str name
    Product : +str sku
    Product : +str category
    Product : +str short_description
    Product : +str long_description
    Product : +List[Image] images
    Product : +List[ProductFeature] features
    Product : +List[ProductSpecification] specifications
    
    ProductFeature : +int id
    ProductFeature : +str title
    ProductFeature : +str body
    ProductFeature : +Product product
    ProductFeature : +List[Image] images

    ProductSpecification : +int id
    ProductSpecification : +str category
    ProductSpecification : +str key
    ProductSpecification : +str value
    ProductSpecification : +Product product
    
    ProductEmbeddings : +int id
    ProductEmbeddings : +datetime created
    ProductEmbeddings : +str model_name
    ProductEmbeddings : +List[float] embeddings
    ProductEmbeddings : +Product product
    
    Review : +int id
    Review : +bool verified
    Review : +float sentiment_score
    Review : +str title
    Review : +int rating
    Review : +str body
    Review : +str member
    Review : +str member_since
    Review : +Product product
    
    Reviews : +int id
    Reviews : +float aggregate_score
    Reviews : +Product product
```

## Data Model

```mermaid
erDiagram
    PRODUCT ||--o{ EMBEDDINGS : embeddings
    PRODUCT ||--o{ FEATURES : features
    PRODUCT ||--o{ PRODUCT_IMAGES : images
    PRODUCT ||--o{ SPECIFICATION : specifications
    PRODUCT ||--|{ REVIEW_STATS : review_stats
    PRODUCT ||--o{ REVIEWS : reviews
    
    FEATURES ||--o{ FEATURE_IMAGES : images
    
    PRODUCT_IMAGES ||--|{ IMAGE : image
    FEATURE_IMAGES ||--|{ IMAGE : image
```
