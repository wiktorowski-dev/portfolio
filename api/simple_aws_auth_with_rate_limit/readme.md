# Simple AWS Auth with Rate Limit
![Coverage](./coverage.svg)

## Project Description

**Simple AWS Auth with Rate Limit** is a Python FastAPI-based web API that demonstrates user authentication using **AWS Cognito** along with an integrated **rate limiting** mechanism. It allows users to sign up and log in via AWS Cognito’s Identity Provider (managing user credentials and JWT tokens), while enforcing a per-client rate limit (e.g. 100 requests per minute) to prevent abuse. The service also uses a MySQL database to store basic user information (like email and preferences) for each authenticated user. This project is a minimal example of combining cloud authentication with application-level rate limiting in a FastAPI application.

## Features

* **AWS Cognito Authentication:** Handles user registration, login, and password management by integrating with AWS Cognito. For example, the API uses Cognito’s *Sign Up* and *Admin Initiate Auth* flows for creating new accounts and verifying credentials. It also supports sending verification codes and password reset via Cognito (e.g. forgot password, resend confirmation code, etc.).
* **JWT Verification & Security:** After login, the client receives a JWT access token (issued by Cognito). The backend validates this token on protected routes using Cognito’s JWKS (public keys) and expected issuer/audience, ensuring only valid tokens are accepted. The token can be provided via an `Authorization: Bearer <token>` header, and the API sets an HTTP-only cookie with the token on login for convenience.
* **Rate Limiting:** Implements a simple in-memory **IP-based rate limiter**. By default, each client IP is limited to 100 requests per 60 seconds. If the limit is exceeded, the API returns HTTP 429 Too Many Requests. This helps protect the service from excessive calls.
* **Persistent User Data:** Uses a MySQL database (via AWS Secrets Manager for credentials) to persist user data such as user ID, email, and a “newsletter subscribed” flag. Upon Cognito sign-up, the user’s info is also saved in the local database. The app demonstrates how to sync Cognito user records with an application database.
* **RESTful Endpoints:** Provides clear API endpoints for common auth tasks and data retrieval. For example, `/auth/sign_up` for registration, `/auth/sign_in` for login, endpoints for confirming emails or resetting passwords, and a protected `/api/v1/internal_data` endpoint that returns sample data only if the requester is authenticated. A health check endpoint (`/health`) is also available to verify that the service is running.

## Requirements

* **AWS Configuration:** An AWS account with a Cognito User Pool set up for user authentication. You will need a User Pool ID, an App Client ID, and the Cognito **issuer/JWKS URL** for token verification. These values should be stored in AWS Secrets Manager, in a secret (JSON format) referenced by the `cognito_secret` environment variable. For example, the secret might contain keys like `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_ISSUER`, and `COGNITO_JWKS_URL` used by the app.
* **Database:** A MySQL database instance (accessible to the application). The database schema should include the necessary tables (e.g. `users`, `account_settings`, and an `internal_data` table for the example endpoint). The schema name is provided via an environment variable `SQL_SCHEMA`, and database connection credentials are fetched from AWS Secrets Manager via a secret referred to by `sql_secret`. Ensure the secret contains the required fields (host, port, username, password, etc.).
* **AWS Credentials:** The application needs AWS credentials to connect to Cognito and Secrets Manager. If running in AWS (e.g. on EC2 or ECS), you can use an IAM role. For local running, ensure your environment is configured with `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and region (or have AWS CLI/SDK credentials configured) so that boto3 can access the services.
* **Python 3.10+ or Docker:** You can run the project with Python (requires **Python 3.10** or higher) or use Docker. The code uses FastAPI and other libraries listed in `requirements.txt`, and a Dockerfile is provided for containerization. Ensure you have Python and pip if running natively, or Docker if you prefer containerized deployment.

## Setup and Installation

**1. Clone the Repository:** Begin by fetching the code (the `simple_aws_auth_with_rate_limit` project directory). Make sure you have the project files available in your environment.

**2. Prepare AWS Resources:** Before running the app, set up the required AWS resources:

* Create or identify an AWS **Cognito User Pool** (and App Client) for authentication.
* In AWS **Secrets Manager**, create a secret (JSON) for Cognito config (with keys for pool ID, client ID, etc.) and another secret for MySQL credentials. Note the secret names or ARNs.
* Ensure your AWS user/role has permissions to read these secrets and use Cognito.

**3. Set Environment Variables:** Configure the following required environment variables in your system or in a `.env` file:

* `SQL_SCHEMA` – the name of your MySQL database (schema) that the app will use.
* `sql_secret` – the name or ARN of the AWS Secrets Manager secret that contains the MySQL connection details.
* `cognito_secret` – the name or ARN of the AWS Secrets Manager secret that contains the Cognito configuration (User Pool info, etc.).
* (Also ensure AWS credentials/environment are set as mentioned in Requirements.)

**4. Install Dependencies:** If running locally, install the Python dependencies:

```bash
pip install -r requirements.txt
```

This will install FastAPI, boto3, SQL drivers, and other required packages.

**5. Initialize Database (if needed):** Set up your MySQL database schema and tables. The app does not create tables automatically. For example:

* Create a schema/database name that matches `SQL_SCHEMA`.
* Create a `users` table (with columns `id` (VARCHAR or UUID), `email` (VARCHAR), etc.).
* Create an `account_settings` table (with columns `user_id` (to link to users.id), `newsletter_subscribed` (BOOLEAN), etc.).
* (Optionally, insert some sample data into an `internal_data` table for testing the protected endpoint.)

**6. Run the Application:**

* **Using Uvicorn (development mode):** You can run the app with hot-reload using:

  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8080 --reload
  ```

  This will start the FastAPI server on port 8080. The `main.py` includes a check to ensure all required env vars are set before the server runs.
* **Using Python directly:** Simply running `python main.py` will launch the server as well (the Docker entrypoint uses this command).
* **Using Docker:** Build and run the Docker container:

  ```bash
  docker build -t simple-aws-auth-rate-limit .
  docker run -p 8080:8080 \
    -e SQL_SCHEMA=<your_db_name> \
    -e sql_secret=<your_db_secret_name> \
    -e cognito_secret=<your_cognito_secret_name> \
    -e AWS_ACCESS_KEY_ID=<your_aws_key> \
    -e AWS_SECRET_ACCESS_KEY=<your_aws_secret> \
    simple-aws-auth-rate-limit
  ```

  This will start the container with the necessary environment. The app (inside the container) will install requirements and run `main.py` automatically.

After starting, the API should be available at `http://<host>:8080`. You can check `GET /health` to see if it returns `{"status": "ok"}`, indicating the server is up.

## How to Use the API

Once the server is running, you can interact with the API using tools like **curl, HTTPie, Postman**, or the built-in **Swagger UI** (navigate to `http://<host>:8080/docs` in a browser to view API documentation and test endpoints).

Here are the main endpoints and their usage:

* **Health Check:** `GET /health` – Public endpoint to verify the service status. It returns a simple JSON like `{"status": "ok"}` when the app is running.

* **User Registration:** `POST /auth/sign_up` – Create a new user account.
  **Request:** JSON body with `email`, `password`, and `newsletter_subscribed` fields. For example:

  ```json
  {
    "email": "user@example.com",
    "password": "StrongPassword123",
    "newsletter_subscribed": true
  }
  ```

  When called, the backend will attempt to register the user in AWS Cognito and also insert a new user record into the local database.

  * On success, you’ll receive a JSON response confirming registration (and Cognito may send a confirmation email depending on your User Pool settings).
  * If the username/email already exists, you’ll get a 400 error (handled as *“Username already exists”* in the code).

* **User Login:** `POST /auth/sign_in` – Authenticate an existing user.
  **Request:** Credentials are expected as form data (content type `application/x-www-form-urlencoded`). You can provide `username` (which is the email) and `password` fields. For example, using curl:

  ```bash
  curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
       -d "username=user@example.com&password=StrongPassword123" \
       http://<host>:8080/auth/sign_in
  ```

  On success, this endpoint returns a JSON containing an `access_token` (a JWT from Cognito) and `token_type` ("bearer"). It also sets an HTTP-only cookie named `access_token` with the same JWT value. You can use the token for authenticated requests (see below). If credentials are invalid or the user is not confirmed, appropriate 401 errors are returned.

* **Protected Resource:** `GET /api/v1/internal_data` – *Example protected endpoint.* This returns some internal data from the database (the `internal_data` table) but only if the request is made by an authenticated user.
  **Usage:** Include the JWT access token you obtained from login in the request. Typically, you do this by setting an `Authorization` header:

  ```
  Authorization: Bearer <your_access_token>
  ```

  If the token is valid and not expired, the server will allow the request and respond with JSON data (or an empty result if no data in the table). If the token is missing or invalid, you will get a 401 Unauthorized error. (If you are using the cookie set by `/auth/sign_in`, a client or browser will need to send that cookie with the request – note that the default auth mechanism expects the token in the header by OAuth2 scheme).

* **Password Reset Flow:** The API supports the Cognito password reset process:

  * `POST /auth/forgot-password` – Initiate a password reset. Send JSON `{"email": "user@example.com"}`. The app will trigger AWS Cognito to send a password reset code to the user's email. The response will be a confirmation message (or error if the email is not found).
  * `POST /auth/confirm-forgot-password` – Complete the password reset. After the user receives the code from email, call this endpoint with JSON containing `username` (email), the `confirmation_code` from email, and a new `password`. Cognito will verify the code and set the new password. A successful response indicates the password is changed.
  * `POST /auth/resend_activation_link` – If a user didn’t receive the sign-up confirmation, this endpoint can resend the verification code. Provide JSON `{"email": "user@example.com"}`; the app calls Cognito to re-send the confirmation email.
  * `POST /auth/change-password` – Change password for a logged-in user. This requires authentication. Provide a JSON body with `token` (the user’s current access token JWT), `previous_password`, and `proposed_password` (new password). If the token and old password are valid, Cognito will update the password. (This endpoint is protected – it also requires a valid login session via `get_current_user`, so include the token in the header or cookie as with other protected endpoints.)

**Rate Limiting:** The application enforces a **rate limit of 100 requests per minute per IP** address by default. This is a rolling window limit: if a single IP sends more than 100 requests within any 60-second span, further requests will be rejected with HTTP 429 Too Many Requests. If you encounter a 429 error, you should wait a short time before retrying. (This limit is configurable in code – see the `times=100, seconds=60` parameters in the `rate_limit` function.)

## Notes and Limitations

* **AWS Setup Required:** This project assumes the necessary AWS resources (Cognito user pool, secrets, etc.) are in place. It will not function out-of-the-box without valid AWS configuration. Be sure to update the environment variables to point to your AWS secrets and have network access to AWS endpoints. Cognito user pool setup (and optionally, configuring email/SMS for verification codes) must be done in your AWS account beforehand.

* **Database Schema:** The FastAPI application does **not auto-create tables** or run migrations. You need to manually ensure the MySQL database has the expected schema and tables. The code expects tables named `users`, `account_settings`, and `internal_data` within the schema you provide. The `users` table stores at least `id` (Cognito user ID) and `email`. The `account_settings` table stores user settings (linked by `user_id`). Without these tables, certain endpoints (especially those that create or fetch users) will error out.

* **In-Memory Rate Limiter:** The rate limiting mechanism uses an in-memory Python dictionary to track request timestamps. This means the limit is per process instance. In a production scenario with multiple instances or servers, each would enforce its own count (no centralized limit). Also, restarting the server will reset the stored history of requests. For a more robust solution, consider using a distributed cache or API gateway rate limiting in a real deployment.

* **Security Considerations:** This project uses Cognito for authentication, which offloads password security and user management to AWS. However, ensure you handle the Cognito secrets and AWS credentials carefully (don’t hard-code them; use environment variables or AWS IAM roles). All sensitive operations (login, sign-up, password change) are done over HTTPS when deployed properly (ensure SSL in production). The JWT validation ensures tokens are genuine and unexpired, but be mindful of token expiration (clients should handle refreshing tokens via Cognito if needed, though a refresh token flow is not explicitly implemented here).

* **Not Production-Ready:** This project is intended as a learning example or starting point. There are aspects you might need to improve for production: for instance, more comprehensive error handling and logging, input validation beyond basic cases, using HTTPS (TLS) in front of the service, and possibly refining how user data is handled (the example stores a newsletter flag in a separate table; a real app might integrate with a mailing service instead). Always review and test configurations (especially AWS resource ARNs, region settings, etc.) in a safe environment before deploying.
