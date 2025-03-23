# SummarEase Database Structure and AWS Cost Analysis

## Database Structure

SummarEase uses PostgreSQL as its primary database with a scalable design to support growing user bases and usage patterns.

### Models

1. **User Model**
   - Authentication information
   - Credit balance tracking
   - Usage statistics
   - Role-based access control

2. **Summary Model**
   - Original text and summary storage
   - Processing status tracking
   - Performance metrics (processing time, token counts)
   - Cost accounting per summary

3. **Usage Statistics Model**
   - Aggregated hourly usage data
   - System performance metrics
   - Cost tracking for billing and reporting
   - Capacity planning information

### Database Scaling Strategy

- **Connection Pooling**: Configured with optimal pool settings to efficiently handle multiple concurrent requests
- **Indexes**: Strategic indexes on frequently queried fields
- **Partitioning**: Tables designed to support partitioning for high-volume data
- **Read Replicas**: Architecture supports adding read replicas for scaled environments

## AWS Cost Estimation

### Monthly Cost Breakdown

| Service | Provider | Tier | Description | Cost (USD) |
|---------|----------|------|-------------|------------|
| EC2/Fargate backend | AWS | t3.micro | 2 vCPU, 1GB RAM | $20-30 |
| RDS PostgreSQL | AWS | db.t3.micro | 2 vCPU, 1GB RAM, 20GB storage | $15-25 |
| S3/Storage | AWS | Standard | Object storage for backups | $1-5 |
| Hugging Face API | Hugging Face | Free/Starter | Text summarization | $0-30 |
| Email (AWS SES) | AWS | Free/Starter | User notifications | <$5 |
| Redis (ElastiCache) | AWS | cache.t2.micro | Queue system | $15-20 |
| **Total** | | | | **$56-115** |

### Cost Optimization Strategies

1. **Auto-scaling**
   - Scale services based on actual demand
   - Use AWS Lambda for intermittent workloads
   - Implement serverless technologies where appropriate

2. **Reserved Instances**
   - Use reserved instances for predictable workloads
   - Purchase 1-year commitments for approximately 40% savings

3. **Performance Efficiency**
   - Cache frequently accessed data
   - Implement proper database indexes
   - Use compression for large text fields

4. **Monitoring and Optimization**
   - Track costs with AWS Cost Explorer
   - Set up CloudWatch alarms for unusual spending
   - Regularly review and optimize instance sizing

### Scalability Cost Projections

| Usage Level | Monthly Users | Monthly Summaries | Estimated Cost |
|-------------|---------------|-------------------|---------------|
| Startup | 100-500 | 1,000-5,000 | $56-115 |
| Growth | 500-5,000 | 5,000-50,000 | $115-350 |
| Scale | 5,000-50,000 | 50,000-500,000 | $350-1,200 |

#### Scaling Optimization Notes

- Transition from single instances to load-balanced environments as traffic increases
- Implement read replicas for database at the Growth stage
- Add caching layers and CDN for static content at the Scale stage
- Consider moving to a multi-region deployment for global scale

## Credit System and User Pricing

Our credit-based system allows flexible monetization:

1. **Free Tier**: 10 credits per month (~10 summaries)
2. **Basic Plan**: $9.99/month for 100 credits (~100 summaries)
3. **Professional Plan**: $39.99/month for 500 credits (~500 summaries)

## Cost Per Operation

Based on our infrastructure and Hugging Face API usage:

- Average summary cost: $0.02-0.05 per summary
- Database storage: ~$0.01 per 100 summaries
- Processing cost: ~$0.01-0.03 per summary

This pricing structure allows us to maintain profitability while offering competitive rates to users.