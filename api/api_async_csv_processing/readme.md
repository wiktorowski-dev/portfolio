# Transaction Data Processing and Aggregation System

## Overview

Company requires a backend solution to handle large volumes of transaction data from various systems. This repository provides a **transaction data processing and aggregation tool** that allows for data import, validation, simple processing, and exposes aggregated results via a RESTful API. The system is designed to efficiently **decouple data processing from the API requests**, using a background task queue so that heavy computations do not block user interactions. In practice, this means you can upload or stream transaction data to the system, have it processed asynchronously, and then retrieve summary results (such as totals, counts, etc.) through the API once processing is complete.

## How to Run the Application

To simplify deployment and setup, the entire stack is containerized using **Docker Compose**. Follow these steps to get the system up and running:

1. **Prerequisites:** Install Docker and Docker Compose on your machine (see Docker's documentation for installation steps).

2. **Clone the Repository:** Download or clone this repository to your local machine.

3. **Configure Environment:** (If applicable) Create a `.env` file or adjust configuration files for any environment-specific settings (e.g., API ports, database credentials). By default, the Docker Compose file includes reasonable defaults for development.

4. **Launch the Services:** Run `docker compose up --build` in the project directory. Docker Compose will build images (if not already built) and start the required containers. This single command brings up:

   * **Web API Service:** The main application (FastAPI) that provides endpoints for data import and retrieving results.
   * **Celery Worker Service:** A worker process running Celery that executes the background processing tasks.
   * **Redis Service:** A Redis instance acting as the message broker for Celery.
   * **Postgres DB:** A Postgres instance storing all processing and reference data.

   Running the above command will start the application server, a Redis instance, and a Celery worker, all in separate containers. You should see logs indicating each service starting up.

5. **Access the API:** Once the containers are up, the API server will be accessible (by default) at `http://localhost:8080/` (or another port if configured). You can use tools like `curl` or Postman to interact with the API:

   *Note:* The exact endpoint paths and request/response format are documented within the API section of this project (see the code or docs for details).

6. **Shut Down:** To stop all services, press `Ctrl+C` in the terminal running Docker Compose, or run `docker-compose down` to gracefully stop and remove containers.

## Design Decisions and Architecture

* **Docker Compose for Orchestration:** I used Docker Compose to containerize the application and its dependencies, making it easy to run all components together in any environment. This approach ensures that the **web service, Celery workers, Postgres DB, and Redis broker** all run with a single command and can communicate on a virtual network. Containerization also helps in isolating dependencies and simplifying deployment.
* **Celery for Background Task Processing:** I chose **Celery** as the task queue framework to handle data processing asynchronously. Celery is a mature distributed task queue that **enables scalable background processing** and task scheduling with minimal effort. By offloading heavy computations to Celery workers, the main API server remains responsive, and I can process large transaction files without timing out requests. Celery automatically manages worker processes and allows horizontal scaling (I can add more workers for higher throughput), which aligns with the need to handle large volumes of data efficiently. Each data import request triggers a Celery task that performs validation and aggregation logic in the background.
* **Redis as Message Broker:** I opted for **Redis** as the message broker for Celery. Redis is a fast in-memory data store that can function as a lightweight message queue. When a task is queued, Celery sends the task message to Redis, which holds it until a worker picks it up for execution. This decoupling via a message broker means the API doesn’t need to wait for processing to finish – the task will be handled asynchronously by a worker, and results can be stored or retrieved when ready. Redis was chosen over other brokers (like RabbitMQ) for simplicity and ease of setup in a containerized environment, as well as sufficient performance for this use-case. (In Celery’s configuration, the Redis URL is set as the broker, and I also use Redis as the result backend to store task outcomes for quick retrieval by the API.)
* **REST API Design:** The system provides a RESTful API for interaction. The design follows a clear separation of concerns:

  * The **ingestion endpoint** simply accepts data (or a reference to data) and triggers a Celery task, responding quickly to confirm receipt. It does minimal work (just validation of input format and queuing the task).
  * The **results endpoint** allows clients to fetch aggregated results. If the data is still being processed, the API might return a pending status or empty result; otherwise it returns the computed metrics. This polling style was chosen over pushing results to keep the API stateless and simple.

* **Data Validation and Processing:** Upon receiving transaction data, the system performs basic validation (e.g., required fields present, correct data types) before processing. All heavy‑lifting happens in Polars, whose columnar, multi‑threaded engine enables fast validation. This logic is kept **simple and modular** – as a Celery task, it can be enhanced or parallelized further if needed (for instance, splitting the dataset into chunks). The focus was on demonstrating the pipeline rather than implementing complex analytics.
* **Scalability:** Thanks to Celery and Docker, the design can scale both vertically and horizontally. For heavier loads, you can increase the number of Celery worker containers in the Docker Compose configuration or deploy the worker component on separate machines. The message queue architecture means tasks can be distributed across multiple workers on different hosts if required, providing resilience and scalability for large data volumes. The API server remains unaffected by the number of tasks, other than perhaps providing status updates.

## Compromises and Trade-offs

In designing this solution, a few compromises and trade-offs were made due to scope and simplicity considerations:

* **Message Broker Choice:** I chose Redis for the broker for ease of use. While Redis works well and is easy to set up, it is not as full-featured in messaging as RabbitMQ (for example, RabbitMQ might handle complex routing or acknowledgments more robustly). For the scale and complexity of this project, Redis is sufficient, but in a large-scale production environment with very high throughput or complex routing needs, RabbitMQ or another dedicated message broker could be considered. The trade-off here was simplicity and developer convenience versus some advanced messaging features.
* **Database/Persistence:** The stack now includes a dedicated **PostgreSQL**. All raw transactions and computed summaries are persisted in this database, so your data survives container restarts and scales well for historical analysis. Redis still serves as the Celery message broker (and optional result backend), but PostgreSQL is the single source of truth for long-term storage.
* **Synchronous vs Asynchronous Trade-off:** By using asynchronous processing, I accept that results are not instantaneous. Clients may need to poll the API for results or be notified when processing is done. This **eventual consistency** model is a compromise to achieve scalability – the system favors being able to handle large workloads over immediate consistency. As a result, there is a slight complexity added in client-side logic (to check if processing is finished), but this keeps the server robust under load and responsive.
* **Error Handling and Monitoring:** Basic error handling is implemented (Celery will retry failed tasks automatically by default, and validation errors are returned to the client if import data is invalid).
* **Validation and Processing Logic Simplicity:** The validation rules and aggregation computations are kept fairly simple. I assumed a consistent input format and did not implement advanced data cleaning or complex aggregation queries. This is a conscious compromise to meet the project requirements without over-engineering. In future iterations, one might need to handle more edge cases in data (e.g., malformed records) and possibly stream processing if the data volume is too large to hold in memory at once.

## Conclusion

This README provided a brief overview of the Transaction Data Processing and Aggregation System, including how to run it and the key design decisions behind it. In summary, the solution is containerized for easy setup, uses Celery with Redis to handle heavy data processing in the background (ensuring the system stays **scalable and responsive under load**), and exposes an API for integration with other services or front-end applications. The chosen architecture addresses the need to process large transaction datasets by distributing work to background workers, while any compromises made (such as using a lightweight broker and simplifying persistence) are documented for transparency. I believe this setup provides a solid foundation that can be extended or hardened for production use, and welcome feedback or contributions for future improvements.
