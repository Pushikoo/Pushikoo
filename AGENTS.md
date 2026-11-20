# AGENTS.md

## Guide

For development, see [README.md](README.md).
If there are API modification and build-related operations, the above content will be very important.

## Compatibility

The project is in production, so changes must preserve compatibility.
The interface must evolve incrementally, and new capabilities must provide default implementations.
Changes to persisted data formats require a migration.

## Notes

1. Before modifying a code file, read it again to ensure that it is up to date. The file may be manually modified by the user.
1. Never create an alembic version file manually, use `alembic revision` instead, unless user specifies.
1. Don't create tests automatically.
