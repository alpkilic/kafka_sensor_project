# monitor_partitions.py
import json
import time
from kafka import KafkaConsumer

def monitor_partition(partition_id):
    consumer = KafkaConsumer(
        'sensor-data',
        bootstrap_servers='localhost:29092',
        auto_offset_reset='latest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    # Assign specific partition
    from kafka import TopicPartition
    tp = TopicPartition('sensor-data', partition_id)
    consumer.assign([tp])
    
    print(f"🔍 Monitoring Partition {partition_id}")
    
    for message in consumer:
        data = message.value
        print(f"Partition {partition_id}: {data['type']} - {data['sensor_id']} - {data['value']}")

# Run: python monitor_partitions.py