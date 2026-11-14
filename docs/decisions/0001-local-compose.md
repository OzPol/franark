# ADR-0001: Local service with a browser interface

Status: accepted for the local pilot. Template version: 0.1.0.

## Context

The first installation runs on Oz's computer and should start with a small
number of repeatable commands. It needs a UI, saved state, and a model API seam.

## Decision

Use Python, FastAPI, SQLite, and Docker Compose. Serve the app on localhost and
build Sphinx documentation as a second Compose service. Provide a Python setup
path for computers without Docker.

## Consequences

The application can move to an approved always-on host later. SQLite fits the
single-user pilot. Remote access, multiple users, a durable worker queue, and
database migrations require explicit follow-up work. A packaged executable can
be added after the workflow and update path stabilize.
