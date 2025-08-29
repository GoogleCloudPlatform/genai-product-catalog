# Catalog ML

This project is a machine learning application for product catalog management. It includes agents for processing and a model for predictions.

## Getting Started

### Prerequisites

This project uses `uv` for dependency management. To install `uv`, run:

```bash
pip install uv
```

### Installation

1.  Create a virtual environment:
    ```bash
    uv venv --seed
    ```
2.  Install the dependencies:
    ```bash
    uv sync
    ```
## GCloud Setup

```shell
gcloud config configurations create <configuration_name>
```

```shell
gcloud config configurations activate <configuration_name>
```

```shell
# Activate Google Cloud Project
 gcloud config set project <project_name>
```

```shell
# Authenticate with Google Cloud
gcloud auth application-default login
```

```shell
# Set the quota project
gcloud auth application-default set-quota-project <project_name>
```

## Running the Application

This project uses the Google Agent Development Kit (ADK). You can run the agent in two ways:

### 1. Command-Line Interface (CLI)

To run the agent in your terminal, execute the following command from the project root:

```bash
adk run agents
```

You can then interact with the agent directly in your terminal.

### 2. Web-Based Development UI

To launch a local web server with a user interface for interacting with your agent, run:

```bash
adk web
```

> Then select the "agents" folder from the dropdown.

This will start a web server (usually at `http://localhost:8000`) where you can interact with the agent in a more visual way.

## Testing with Curl

### URL
<Your Cloud RUN URL>

```shell
# Set the app URL
export APP_URL="<Cloud Run URL>"
```

```shell
# Set your access token
export TOKEN=$(gcloud auth print-identity-token)
```

```shell
# Check the application list
curl -X GET -H "Authorization: Bearer $TOKEN" $APP_URL/list-apps
```

```shell
# Create or update a session
curl -X POST -H "Authorization: Bearer $TOKEN" \
    $APP_URL/apps/catalog-enrichment-app/users/user_123/sessions/session_abc \
    -H "Content-Type: application/json" \
    -d '{"state": {"preferred_language": "English", "visit_count": 5}}'
```

```shell
# Run the agent
curl -X POST -H "Authorization: Bearer $TOKEN" \
    $APP_URL/run_sse \
    -H "Content-Type: application/json" \
    -d '{
    "app_name": "catalog-enrichment-app",
    "user_id": "user_123",
    "session_id": "session_abc",
    "new_message": {
        "role": "user",
        "parts": [{
        "text": "{\"uniq_id\":3152365,\"crawl_timestamp\":\"2025-07-30 16:37:40 +0200\",\"product_url\":\"https://product_url/\",\"product_name\":\"Navy Branded T-shirt\",\"product_category_tree\":[\"Men >> Tops\",\"Brands >> Men >> Fuel >> Tops\",\"Men >> Fuel\",\"Men >> Fuel\",\"Men >> Tops >> T-shirts\"],\"pid\":3152365,\"retail_price\":250,\"discounted_price\":null,\"images\":[\"https://image_url.jpg\",\"https://image_url2.jpg\",\"https://image_url3.jpg\"],\"is_FK_Advantage_product\":\"FALSE\",\"description\":\"Navy Branded T-shirt by Fuel\\r\\n-Colour: Navy\\r\\n-Style: T-shirt\\r\\n-Sleeve length: Short sleeve\\r\\n-Fabric: Carded Single Jersey\",\"product_rating\":\"No rating available\",\"overall_rating\":\"No rating available\",\"brand\":\"Fuel\",\"product_specifications\":[{\"key\":\"Type\",\"value\":\"T-Shirts\"},{\"key\":\"Primary Colour\",\"value\":\"Navy\"},{\"key\":\"Style\",\"value\":\"T-shirts\"},{\"key\":\"Sleeve length\",\"value\":\"Short sleeve\"},{\"key\":\"Gender\",\"value\":\"Men\"},{\"key\":\"Age Group\",\"value\":\"Adult\"}]}"
        }]
    },
    "streaming": false
    }'
```




## Contributing

Contributions are welcome! Please adhere to the existing code style and conventions when making changes.


## Services Enable
