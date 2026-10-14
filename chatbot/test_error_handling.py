#!/usr/bin/env python3
"""
Quick test script to verify error handling in BackendClient.

This script tests that the error handling properly converts various
HTTP errors into structured BackendError responses.
"""

import asyncio
import sys
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Add src to path
sys.path.insert(0, 'src')

from backend_client import BackendClient, BackendError


async def test_connection_error():
    """Test that connection errors are properly handled."""
    print("Testing connection error handling...")
    
    client = BackendClient("http://localhost:9999", timeout=1)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
        
        try:
            await client.get_products()
            print("❌ FAILED: Should have raised BackendError")
            return False
        except BackendError as e:
            if e.error_type == "connection_error":
                print(f"✓ Connection error handled correctly: {e.message}")
                print(f"  Error dict: {e.to_dict()}")
                return True
            else:
                print(f"❌ FAILED: Wrong error type: {e.error_type}")
                return False


async def test_timeout_error():
    """Test that timeout errors are properly handled."""
    print("\nTesting timeout error handling...")
    
    client = BackendClient("http://localhost:3001", timeout=1)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get.side_effect = httpx.TimeoutException("Request timed out")
        
        try:
            await client.get_products()
            print("❌ FAILED: Should have raised BackendError")
            return False
        except BackendError as e:
            if e.error_type == "timeout_error":
                print(f"✓ Timeout error handled correctly: {e.message}")
                print(f"  Error dict: {e.to_dict()}")
                return True
            else:
                print(f"❌ FAILED: Wrong error type: {e.error_type}")
                return False


async def test_404_error():
    """Test that 404 errors are properly handled."""
    print("\nTesting 404 error handling...")
    
    client = BackendClient("http://localhost:3001", timeout=10)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # Create a mock response with 404 status
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_instance.get.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        
        try:
            await client.get_product_details(999)
            print("❌ FAILED: Should have raised BackendError")
            return False
        except BackendError as e:
            if e.error_type == "not_found":
                print(f"✓ 404 error handled correctly: {e.message}")
                print(f"  Error dict: {e.to_dict()}")
                return True
            else:
                print(f"❌ FAILED: Wrong error type: {e.error_type}")
                return False


async def test_500_error():
    """Test that 500 errors are properly handled."""
    print("\nTesting 500 error handling...")
    
    client = BackendClient("http://localhost:3001", timeout=10)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # Create a mock response with 500 status
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_instance.get.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )
        
        try:
            await client.get_products()
            print("❌ FAILED: Should have raised BackendError")
            return False
        except BackendError as e:
            if e.error_type == "server_error":
                print(f"✓ 500 error handled correctly: {e.message}")
                print(f"  Error dict: {e.to_dict()}")
                return True
            else:
                print(f"❌ FAILED: Wrong error type: {e.error_type}")
                return False


async def test_successful_request():
    """Test that successful requests still work."""
    print("\nTesting successful request...")
    
    client = BackendClient("http://localhost:3001", timeout=10)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # Create a successful mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "Test Product"}]
        mock_instance.get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        try:
            result = await client.get_products()
            if result == [{"id": 1, "name": "Test Product"}]:
                print(f"✓ Successful request works correctly")
                return True
            else:
                print(f"❌ FAILED: Wrong result: {result}")
                return False
        except Exception as e:
            print(f"❌ FAILED: Unexpected error: {e}")
            return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing BackendClient Error Handling")
    print("=" * 60)
    
    # Run tests sequentially to avoid interleaved output
    results = []
    results.append(await test_connection_error())
    results.append(await test_timeout_error())
    results.append(await test_404_error())
    results.append(await test_500_error())
    results.append(await test_successful_request())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
