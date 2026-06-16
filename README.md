# Ouroboros

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0) [![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com) [![SvelteKit](https://img.shields.io/badge/sveltekit-latest-orange.svg)](https://kit.svelte.dev)

![GitHub issues](https://img.shields.io/github/issues/unclesp1d3r/Ouroboros) ![GitHub last commit](https://img.shields.io/github/last-commit/unclesp1d3r/Ouroboros) ![Maintenance](https://img.shields.io/maintenance/yes/2025) [![wakatime](https://wakatime.com/badge/github/unclesp1d3r/Ouroboros.svg)](https://wakatime.com/badge/github/unclesp1d3r/Ouroboros)

**Project Ouroboros** is the experimental FastAPI + SvelteKit rewrite of CipherSwarm — a distributed password cracking orchestration system originally built in Ruby on Rails. This project represents a full-cycle rebuild of CipherSwarm from the inside out, preserving its core ideas while modernizing its architecture, scalability, and user experience.

---

## Purpose

Ouroboros exists as a cleanroom implementation and future foundation for CipherSwarm. It explores:

- Asynchronous task distribution and agent management
- Modern API design with FastAPI and Pydantic v2
- Real-time web UI built with SvelteKit and shadcn-svelte
- Containerized deployments with Docker and MinIO
- Keyspace-weighted scheduling, progress tracking, and result aggregation

---

## Architecture Overview

- **Backend:** FastAPI + SQLAlchemy 2.x (async) + PostgreSQL

- **Frontend:** SvelteKit + Tailwind + shadcn-svelte

- **Storage:** MinIO for file-backed resources

- **Cache:** Cashews (in-memory / Redis)

- **Messaging:** Server-Sent Events (SSE) for live updates

- **Testing:** Pytest + Playwright

---

## Status

Ouroboros is an active rewrite under development. Many components mirror CipherSwarm's design documents but are implemented idiomatically for FastAPI. Until the project stabilizes, this branch should be treated as **experimental**.

> "From its own code, it is reborn."

## Symbolism

The name **Ouroboros** represents the self-consuming, self-renewing nature of this rewrite—a system rebuilding itself from its legacy foundation, endlessly cycling toward improvement.

> "From its own code, it is reborn."
