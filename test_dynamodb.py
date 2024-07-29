from moto import mock_aws
import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
import logging

class URLModel(Model):
    class Meta:
        table_name = 'urls'
        region = 'us-east-1'
    short_url = UnicodeAttribute(hash_key=True)
    original_url = UnicodeAttribute()

@mock_aws
def test_dynamodb_operations():
    # Set up the mock DynamoDB
    print("Setting up mock DynamoDB...")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='urls',
        KeySchema=[
            {
                'AttributeName': 'short_url',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'short_url',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists (only call once)
    table.meta.client.get_waiter('table_exists').wait(TableName='urls')

    # Ensure the table is active
    table.reload()
    assert table.table_status == 'ACTIVE'
    print("Mock table is active.")

    # Print boto3 region
    print(f"boto3 region: {dynamodb.meta.client.meta.region_name}")

    # Print URLModel region
    print(f"URLModel region: {URLModel.Meta.region}")

    try:
        # Your test code goes here
        short_url = 'test123'
        original_url = "https://example.com"
        url_model = URLModel(short_url=short_url, original_url=original_url)

        # Save the item to DynamoDB
        url_model.save()
        print("Item saved successfully.")

        # Retrieve the item from DynamoDB
        retrieved_item = URLModel.get(short_url)
        print(f"Retrieved item: {retrieved_item.short_url} -> {retrieved_item.original_url}")

        # Ensure that the item saved matches the item retrieved
        assert retrieved_item.short_url == short_url
        assert retrieved_item.original_url == original_url
        print("Item retrieved matches the item saved.")

        # Scan items in the table
        items = list(URLModel.scan())
        print(f"Scanned items: {items}")
        assert len(items) > 0, "Scan should return at least one item."

        # Delete the item
        retrieved_item.delete()
        print("Item deleted successfully.")

        # Ensure the item is deleted
        try:
            URLModel.get(short_url)
            assert False, "Item should have been deleted."
        except URLModel.DoesNotExist:
            print("Item deletion confirmed.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    test_dynamodb_operations()