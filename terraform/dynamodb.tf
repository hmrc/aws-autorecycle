resource "aws_dynamodb_table" "mongo_recycle_in_progress" {
  name         = "mongo_recycle_in_progress"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "replicaset_name"

  attribute {
    name = "replicaset_name"
    type = "S"
  }

  tags = {
    Name        = "mongo_recycle_in_progress"
    Environment = var.environment
  }
}
