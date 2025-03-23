# SummarEase Database Models

This directory contains the SQLAlchemy models used in the SummarEase application.

## Models Overview

### User

The `User` model stores authentication information and manages credit allocation:

- Basic user information (email, password hash)
- Role-based access control
- Credit tracking for usage limits
- Usage statistics for analytics

### Summary

The `Summary` model tracks text summarization requests and results:

- Original text and generated summary storage
- Processing status and timestamps
- Performance metrics (processing time, token counts)
- Cost tracking per summary operation

### UsageStatistics

The `UsageStatistics` model aggregates system-wide metrics for analysis and billing:

- Hourly usage aggregation
- System performance metrics
- Cost tracking for AWS resources
- Capacity planning information

## Database Relationships

- A `User` can have many `Summary` records (one-to-many relationship)
- `UsageStatistics` records aggregate system-wide data (no direct relationships)

## Indexing Strategy

All models implement strategic indexing for:
- Frequently queried fields
- Foreign keys for relationships
- Timestamp fields for range queries

## Scaling Considerations

- Models are designed to support table partitioning for high-volume scenarios
- Large text fields are properly typed for efficient storage
- Connection pooling parameters are tuned for horizontal scaling