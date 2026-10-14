"""
Basic verification test for tool implementations.

This script verifies that all tools are properly implemented and can be instantiated.
"""

import asyncio
import sys
from src.tools import (
    Tool,
    ProductBrowserTool,
    CartManagerTool,
    RecommendationTool,
    ToolRegistry
)
from src.backend_client import BackendClient


async def test_tool_definitions():
    """Test that all tools provide valid definitions."""
    print("Testing tool definitions...")
    
    # Create a backend client (won't actually connect for this test)
    backend_client = BackendClient(base_url="http://localhost:3001", timeout=10)
    
    # Test ProductBrowserTool
    product_tool = ProductBrowserTool(backend_client)
    product_def = product_tool.get_definition()
    assert product_def["name"] == "browse_products"
    assert "description" in product_def
    assert "parameters" in product_def
    print("✓ ProductBrowserTool definition valid")
    
    # Test CartManagerTool
    cart_tool = CartManagerTool(backend_client)
    cart_def = cart_tool.get_definition()
    assert cart_def["name"] == "manage_cart"
    assert "description" in cart_def
    assert "parameters" in cart_def
    assert "action" in cart_def["parameters"]["properties"]
    print("✓ CartManagerTool definition valid")
    
    # Test RecommendationTool
    rec_tool = RecommendationTool(backend_client)
    rec_def = rec_tool.get_definition()
    assert rec_def["name"] == "get_recommendations"
    assert "description" in rec_def
    assert "parameters" in rec_def
    print("✓ RecommendationTool definition valid")
    
    print("\nAll tool definitions are valid!")


async def test_tool_registry():
    """Test that ToolRegistry properly registers and manages tools."""
    print("\nTesting ToolRegistry...")
    
    backend_client = BackendClient(base_url="http://localhost:3001", timeout=10)
    registry = ToolRegistry(backend_client)
    
    # Test tool listing
    tool_names = registry.list_tools()
    assert "browse_products" in tool_names
    assert "manage_cart" in tool_names
    assert "get_recommendations" in tool_names
    print(f"✓ Registry contains {len(tool_names)} tools: {tool_names}")
    
    # Test tool retrieval
    product_tool = registry.get_tool("browse_products")
    assert product_tool is not None
    assert isinstance(product_tool, ProductBrowserTool)
    print("✓ Tool retrieval works")
    
    # Test getting all definitions
    all_defs = registry.get_all_tool_definitions()
    assert len(all_defs) == 3
    assert all("name" in d for d in all_defs)
    print("✓ All tool definitions retrieved")
    
    # Test invalid tool
    invalid_tool = registry.get_tool("nonexistent_tool")
    assert invalid_tool is None
    print("✓ Invalid tool returns None")
    
    print("\nToolRegistry tests passed!")


async def main():
    """Run all tests."""
    try:
        await test_tool_definitions()
        await test_tool_registry()
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("="*50)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
