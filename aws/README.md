# AWS Deployment

Infrastructure and deployment scripts for AWS.

## Files

- `cloudformation-stack.yaml` - CloudFormation template for AWS resources
- `deploy.sh` - Deployment script
- `setup-ec2.sh` - EC2 instance setup script

## Usage

1. Configure AWS credentials
2. Run deployment:
   ```bash
   ./deploy.sh
   ```

## Resources

The CloudFormation stack creates:
- EC2 instances
- Security groups
- Load balancers
- Related networking resources

