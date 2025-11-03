"""
Model Context Protocol (MCP) - Agent Communication Module
=========================================================

This module provides a communication layer between agents using
the Model Context Protocol pattern.

Functions:
1. Message passing between agents
2. Message queuing and routing
3. Protocol standardization


"""

import logging
from collections import defaultdict
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Message queue storage (in-memory)
# In production, this could be Redis, RabbitMQ, or other message broker
message_queues = defaultdict(list)


def send_mcp_message(message):
    """
    Send a message from one agent to another using MCP.
    
    Message Format:
    {
        "sender": "AgentName",
        "receiver": "AgentName",
        "payload": {
            # Agent-specific data
        },
        "timestamp": "ISO-8601 timestamp",
        "message_id": "unique_id"
    }
    
    Args:
        message (dict): Message dictionary with sender, receiver, and payload
        
    Returns:
        bool: True if message sent successfully
    """
    try:
        # Validate message structure
        if not isinstance(message, dict):
            logger.error("Message must be a dictionary")
            return False
        
        required_fields = ["sender", "receiver", "payload"]
        for field in required_fields:
            if field not in message:
                logger.error(f"Message missing required field: {field}")
                return False
        
        # Add metadata
        message["timestamp"] = datetime.now().isoformat()
        message["message_id"] = f"{message['sender']}-{message['receiver']}-{datetime.now().timestamp()}"
        
        # Route message to receiver's queue
        receiver = message["receiver"]
        message_queues[receiver].append(message)
        
        logger.info(f"MCP Message sent: {message['sender']} → {message['receiver']}")
        logger.debug(f"Message ID: {message['message_id']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending MCP message: {str(e)}")
        return False


def receive_mcp_message(receiver_name):
    """
    Receive a message for a specific agent.
    
    Args:
        receiver_name (str): Name of the receiving agent
        
    Returns:
        dict: Message dictionary or None if no messages available
    """
    try:
        if receiver_name in message_queues and message_queues[receiver_name]:
            message = message_queues[receiver_name].pop(0)
            logger.info(f"MCP Message received by {receiver_name} from {message['sender']}")
            return message
        else:
            logger.debug(f"No messages in queue for {receiver_name}")
            return None
            
    except Exception as e:
        logger.error(f"Error receiving MCP message: {str(e)}")
        return None


def peek_mcp_message(receiver_name):
    """
    Check if there are messages for an agent without removing them.
    
    Args:
        receiver_name (str): Name of the receiving agent
        
    Returns:
        int: Number of messages in queue
    """
    return len(message_queues.get(receiver_name, []))


def clear_mcp_queue(receiver_name):
    """
    Clear all messages for a specific agent.
    
    Args:
        receiver_name (str): Name of the receiving agent
    """
    if receiver_name in message_queues:
        count = len(message_queues[receiver_name])
        message_queues[receiver_name].clear()
        logger.info(f"Cleared {count} messages from {receiver_name} queue")


def get_mcp_stats():
    """
    Get statistics about message queues.
    
    Returns:
        dict: Statistics about message queues
    """
    stats = {
        "total_queues": len(message_queues),
        "queues": {}
    }
    
    for agent, messages in message_queues.items():
        stats["queues"][agent] = {
            "message_count": len(messages),
            "latest_sender": messages[-1]["sender"] if messages else None
        }
    
    return stats


# Example Usage
def test_mcp():
    """
    Test the MCP communication system.
    """
    print("=" * 60)
    print("MODEL CONTEXT PROTOCOL (MCP) - Agent Communication")
    print("=" * 60)
    
    # Test 1: IngestionAgent → RetrievalAgent
    print("\nTest 1: IngestionAgent → RetrievalAgent")
    message1 = {
        "sender": "IngestionAgent",
        "receiver": "RetrievalAgent",
        "payload": {
            "chunks": ["chunk1", "chunk2", "chunk3"],
            "document_name": "test.pdf"
        }
    }
    send_mcp_message(message1)
    print(f"  ✓ Message sent")
    
    # Test 2: RetrievalAgent → LLMResponseAgent
    print("\nTest 2: RetrievalAgent → LLMResponseAgent")
    message2 = {
        "sender": "RetrievalAgent",
        "receiver": "LLMResponseAgent",
        "payload": {
            "query": "What is RAG?",
            "top_chunks": [("chunk1", "test.pdf"), ("chunk2", "test.pdf")]
        }
    }
    send_mcp_message(message2)
    print(f"  ✓ Message sent")
    
    # Test 3: Receive messages
    print("\nTest 3: Receiving messages")
    msg = receive_mcp_message("RetrievalAgent")
    if msg:
        print(f"  ✓ RetrievalAgent received message from {msg['sender']}")
        print(f"    Payload keys: {list(msg['payload'].keys())}")
    
    msg = receive_mcp_message("LLMResponseAgent")
    if msg:
        print(f"  ✓ LLMResponseAgent received message from {msg['sender']}")
        print(f"    Payload keys: {list(msg['payload'].keys())}")
    
    # Test 4: Stats
    print("\nTest 4: MCP Statistics")
    stats = get_mcp_stats()
    print(f"  Total queues: {stats['total_queues']}")
    for agent, info in stats['queues'].items():
        print(f"  {agent}: {info['message_count']} messages")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_mcp()
