# Gemini Code-Assist Agent Project Guidelines: Ouroboros

This document provides a comprehensive guide for the Gemini Code-Assist agent, outlining the project's architecture, coding conventions, and development workflows. Adherence to these guidelines is crucial for maintaining code quality, consistency, and project integrity.

## 1. Core Project Overview

Ouroboros is a distributed platform for password cracking, designed for high performance and scalability. It leverages a swarm of agents to collaboratively crack hashes, managed by a central server. The platform is built with a modern web interface for user interaction and a robust backend for processing and coordination.

- **Primary Goal**: To efficiently and effectively crack password hashes by distributing the workload across multiple agents.
- **Key Features**:
  - **Distributed Cracking**: Utilizes a swarm of agents to parallelize the cracking process.
  - **Web-Based UI**: A SvelteKit frontend for managing campaigns, tasks, and agents.
  - **RESTful API**: A FastAPI-based backend for managing the cracking process.
  - **Real-Time Updates**: Server-Sent Events (SSE) for real-time communication between the frontend and backend.

## 2. Architecture and Design

The project follows a service-oriented architecture, with a clear separation of concerns between the frontend, backend, and worker agents.

### 2.1. Backend Architecture

- **Framework**: FastAPI is the core framework for the backend, providing a robust and efficient platform for building the API.
- **Service Layer**: A service layer abstracts the business logic from the API endpoints, promoting code reuse and testability.
- **Database**: PostgreSQL is the primary database, with SQLAlchemy used as the ORM for data access. Alembic is used for database migrations.
- **State Machine**: The core logic of the cracking process is modeled as a state machine, ensuring predictable and reliable behavior.
- **Background Tasks**: Celery is used for managing background tasks, such as hash cracking and other long-running operations.

### 2.2. Frontend Architecture

- **Framework**: SvelteKit 5 with Runes is the framework for the frontend, providing a reactive and efficient user interface.
- **Component Library**: Shadcn-Svelte is used for the UI components, with additional custom components as needed.
- **State Management**: SvelteKit 5 stores are used for managing the application state.
- **Server-Side Rendering (SSR)**: SSR is used for initial page loads, with client-side rendering for subsequent navigation.
- **Authentication**: SSR-based authentication is implemented to protect sensitive routes and data.

### 2.3. Docker and Containerization

- **Development**: `docker-compose.dev.yml` is used to set up the development environment, including the backend, frontend, and database.
- **Production**: `docker-compose.yml` and `Dockerfile` are used to build and deploy the application in a production environment.
- **E2E Testing**: `docker-compose.e2e.yml` is used to set up the environment for end-to-end testing.

## 3. Code Style and Conventions

### 3.1. Python (Backend)

- **Style Guide**: Adhere to the PEP 8 style guide, with `ruff` used for linting and formatting.
- **Type Hinting**: All code should be fully type-hinted using `mypy` for static analysis.
- **Naming Conventions**:
  - **Modules**: `snake_case`
  - **Classes**: `PascalCase`
  - **Functions and Variables**: `snake_case`
- **Pydantic**: Pydantic is used for data validation and settings management. Schemas should be clearly defined and used for all API requests and responses.
- **SQLAlchemy**: Use SQLAlchemy Core for database queries, and the ORM for data manipulation.

### 3.2. Svelte (Frontend)

- **Style Guide**: Follow the official Svelte and SvelteKit style guides.
- **Component Naming**: `PascalCase` for all Svelte components.
- **File Naming**: `kebab-case` for all files other than Svelte components.
- **CSS**: Use Tailwind CSS for styling, with custom CSS as needed.

### 3.3. Git and Commit Messages

- **Commit Style**: Follow the Conventional Commits specification.
- **Branching**: Use feature branches for all new development, with pull requests for merging into the main branch.

## 4. Testing and Quality Assurance

### 4.1. Backend Testing

- **Unit Tests**: Use `pytest` for unit testing the backend services and utilities.
- **Integration Tests**: Test the integration between different services and the database.
- **E2E Tests**: Use Playwright for end-to-end testing of the API.

### 4.2. Frontend Testing

- **Unit Tests**: Use `vitest` for unit testing Svelte components and utilities.
- **E2E Tests**: Use Playwright for end-to-end testing of the user interface.

### 4.3. Debugging

- **Backend**: Use the provided launch configurations for debugging the backend in VS Code.
- **Frontend**: Use the browser's developer tools for debugging the frontend.

## 5. Development Workflow

### 5.1. Getting Started

1. **Clone the repository.**
2. **Set up the development environment**: `docker-compose -f docker-compose.dev.yml up -d`
3. **Install dependencies**:
   - Backend: `uv pip install -r requirements.txt`
   - Frontend: `pnpm install`
4. **Run the development servers**:
   - Backend: `uvicorn app.main:app --reload`
   - Frontend: `pnpm dev`

### 5.2. Tooling

- **`uv`**: Used for managing Python dependencies.
- **`pre-commit`**: Used for running checks before committing code.
- **`just`**: A command runner for automating common tasks.

### 5.3. API Documentation

- **Swagger UI**: Available at `/docs` on the backend server.
- **Redoc**: Available at `/redoc` on the backend server.

This document serves as a living guide for the Gemini Code-Assist agent. It should be updated as the project evolves to reflect the latest architectural decisions, coding conventions, and development workflows.
