"""
Tool implementations for LLM function calling.

This module provides the abstract Tool base class and concrete implementations
for product browsing, cart management, and recommendations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from .backend_client import BackendClient, BackendError

logger = logging.getLogger(__name__)


class Tool(ABC):
    """
    Abstract base class for LLM tools.
    
    Tools are functions that the LLM can invoke to perform structured operations
    like browsing products, managing cart, or getting recommendations.
    """
    
    def __init__(self, backend_client: BackendClient):
        """
        Initialize the tool with a backend client.
        
        Args:
            backend_client: Client for communicating with the backend API
        """
        self.backend_client = backend_client
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dictionary containing tool execution results or error information
        """
        pass
    
    @abstractmethod
    def get_definition(self) -> Dict[str, Any]:
        """
        Get the tool definition for LLM function calling.
        
        Returns:
            Dictionary containing tool name, description, and parameter schema
        """
        pass



class ProductBrowserTool(Tool):
    """
    Tool for browsing products and viewing product details.
    
    Supports two modes:
    - List all products (no product_id parameter)
    - Get specific product details (with product_id parameter)
    """
    
    async def execute(self, product_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute product browsing operation.
        
        Args:
            product_id: Optional product ID to get specific product details
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Dictionary with products list or product details, or error information
        """
        try:
            if product_id is not None:
                # Get specific product details
                logger.info(f"ProductBrowserTool: Fetching details for product {product_id}")
                product = await self.backend_client.get_product_details(product_id)
                
                # Format for LLM consumption
                result = {
                    "success": True,
                    "product": {
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "description": product.get("description"),
                        "price": product.get("price"),
                        "category": product.get("category"),
                        "image": product.get("image"),
                        "reviews": product.get("reviews", [])
                    }
                }
                
                # Add review summary if available
                reviews = product.get("reviews", [])
                if reviews:
                    avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews)
                    result["product"]["average_rating"] = round(avg_rating, 1)
                    result["product"]["review_count"] = len(reviews)
                
                return result
            else:
                # List all products
                logger.info("ProductBrowserTool: Fetching all products")
                products = await self.backend_client.get_products()
                
                # Format for LLM consumption
                return {
                    "success": True,
                    "products": [
                        {
                            "id": p.get("id"),
                            "name": p.get("name"),
                            "description": p.get("description"),
                            "price": p.get("price"),
                            "category": p.get("category"),
                            "image": p.get("image")
                        }
                        for p in products
                    ],
                    "total_count": len(products)
                }
        
        except BackendError as e:
            logger.error(f"ProductBrowserTool: Backend error - {e.message}")
            return {
                "success": False,
                **e.to_dict()
            }
        except Exception as e:
            logger.error(f"ProductBrowserTool: Unexpected error - {str(e)}")
            return {
                "success": False,
                "error": "Unexpected error while browsing products",
                "error_type": "unexpected_error",
                "details": str(e)
            }
    
    def get_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM function calling.
        
        Returns:
            Tool definition with name, description, and parameters
        """
        return {
            "name": "browse_products",
            "description": "Search and browse available products in the store. Use without product_id to list all products, or with product_id to get detailed information about a specific product including reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Optional product ID to get details for a specific product. Omit to list all products."
                    }
                }
            }
        }



class CartManagerTool(Tool):
    """
    Tool for managing shopping cart operations.
    
    Supports four actions:
    - view: Get all items in the cart
    - add: Add a product to the cart
    - update: Update quantity of a cart item
    - remove: Remove an item from the cart
    """
    
    async def execute(
        self,
        action: str,
        product_id: Optional[int] = None,
        quantity: Optional[int] = None,
        cart_item_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute cart management operation.
        
        Args:
            action: Cart operation to perform (view, add, update, remove)
            product_id: Product ID for add operations
            quantity: Quantity for add/update operations
            cart_item_id: Cart item ID for update/remove operations
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Dictionary with operation results or error information
        """
        try:
            if action == "view":
                logger.info("CartManagerTool: Viewing cart")
                cart_items = await self.backend_client.get_cart()
                
                # Calculate cart summary
                total_items = sum(item.get("quantity", 0) for item in cart_items)
                total_price = sum(
                    item.get("quantity", 0) * item.get("price", 0)
                    for item in cart_items
                )
                
                return {
                    "success": True,
                    "cart_items": [
                        {
                            "cart_item_id": item.get("id"),
                            "product_id": item.get("product_id"),
                            "product_name": item.get("name"),
                            "price": item.get("price"),
                            "quantity": item.get("quantity"),
                            "subtotal": item.get("quantity", 0) * item.get("price", 0)
                        }
                        for item in cart_items
                    ],
                    "total_items": total_items,
                    "total_price": round(total_price, 2)
                }
            
            elif action == "add":
                # Validate required parameters
                if product_id is None:
                    return {
                        "success": False,
                        "error": "Missing required parameter: product_id",
                        "error_type": "validation_error"
                    }
                if quantity is None:
                    return {
                        "success": False,
                        "error": "Missing required parameter: quantity",
                        "error_type": "validation_error"
                    }
                if quantity <= 0:
                    return {
                        "success": False,
                        "error": "Quantity must be greater than 0",
                        "error_type": "validation_error"
                    }
                
                logger.info(f"CartManagerTool: Adding product {product_id} (qty: {quantity}) to cart")
                result = await self.backend_client.add_to_cart(product_id, quantity)
                
                return {
                    "success": True,
                    "message": f"Added {quantity} item(s) to cart",
                    "cart_item_id": result.get("id")
                }
            
            elif action == "update":
                # Validate required parameters
                if cart_item_id is None:
                    return {
                        "success": False,
                        "error": "Missing required parameter: cart_item_id",
                        "error_type": "validation_error"
                    }
                if quantity is None:
                    return {
                        "success": False,
                        "error": "Missing required parameter: quantity",
                        "error_type": "validation_error"
                    }
                if quantity <= 0:
                    return {
                        "success": False,
                        "error": "Quantity must be greater than 0",
                        "error_type": "validation_error"
                    }
                
                logger.info(f"CartManagerTool: Updating cart item {cart_item_id} to quantity {quantity}")
                await self.backend_client.update_cart_item(cart_item_id, quantity)
                
                return {
                    "success": True,
                    "message": f"Updated cart item to quantity {quantity}"
                }
            
            elif action == "remove":
                # Validate required parameters
                if cart_item_id is None:
                    return {
                        "success": False,
                        "error": "Missing required parameter: cart_item_id",
                        "error_type": "validation_error"
                    }
                
                logger.info(f"CartManagerTool: Removing cart item {cart_item_id}")
                await self.backend_client.remove_cart_item(cart_item_id)
                
                return {
                    "success": True,
                    "message": "Item removed from cart"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Invalid action: {action}. Must be one of: view, add, update, remove",
                    "error_type": "validation_error"
                }
        
        except BackendError as e:
            logger.error(f"CartManagerTool: Backend error - {e.message}")
            return {
                "success": False,
                **e.to_dict()
            }
        except Exception as e:
            logger.error(f"CartManagerTool: Unexpected error - {str(e)}")
            return {
                "success": False,
                "error": "Unexpected error while managing cart",
                "error_type": "unexpected_error",
                "details": str(e)
            }
    
    def get_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM function calling.
        
        Returns:
            Tool definition with name, description, and parameters
        """
        return {
            "name": "manage_cart",
            "description": "View, add, update, or remove items from the shopping cart. Use 'view' to see cart contents, 'add' to add products, 'update' to change quantities, or 'remove' to delete items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["view", "add", "update", "remove"],
                        "description": "Cart operation to perform"
                    },
                    "product_id": {
                        "type": "integer",
                        "description": "Product ID for add operations (required for 'add' action)"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity for add/update operations (required for 'add' and 'update' actions)"
                    },
                    "cart_item_id": {
                        "type": "integer",
                        "description": "Cart item ID for update/remove operations (required for 'update' and 'remove' actions)"
                    }
                },
                "required": ["action"]
            }
        }



class RecommendationTool(Tool):
    """
    Tool for getting personalized product recommendations.
    
    Supports filtering by:
    - Category (matches name or description)
    - Price range (min/max inclusive)
    - Result limit
    """
    
    async def execute(
        self,
        category: Optional[str] = None,
        price_range: Optional[Dict[str, float]] = None,
        limit: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute product recommendation operation.
        
        Args:
            category: Optional category filter (matches name or description)
            price_range: Optional price range filter with 'min' and 'max' keys
            limit: Maximum number of recommendations to return (default: 5)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Dictionary with recommended products or error information
        """
        try:
            logger.info(f"RecommendationTool: Fetching recommendations (category={category}, price_range={price_range}, limit={limit})")
            
            # Fetch all products from backend
            products = await self.backend_client.get_products()
            
            # Apply category filtering
            if category:
                category_lower = category.lower()
                products = [
                    p for p in products
                    if (category_lower in p.get("name", "").lower() or
                        category_lower in p.get("description", "").lower())
                ]
                logger.debug(f"After category filter: {len(products)} products")
            
            # Apply price range filtering
            if price_range:
                min_price = price_range.get("min")
                max_price = price_range.get("max")
                
                if min_price is not None:
                    products = [p for p in products if p.get("price", 0) >= min_price]
                    logger.debug(f"After min price filter ({min_price}): {len(products)} products")
                
                if max_price is not None:
                    products = [p for p in products if p.get("price", 0) <= max_price]
                    logger.debug(f"After max price filter ({max_price}): {len(products)} products")
            
            # Apply result limit
            recommendations = products[:limit]
            
            logger.info(f"RecommendationTool: Returning {len(recommendations)} recommendations")
            
            return {
                "success": True,
                "recommendations": [
                    {
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "description": p.get("description"),
                        "price": p.get("price"),
                        "category": p.get("category"),
                        "image": p.get("image")
                    }
                    for p in recommendations
                ],
                "total_matches": len(products),
                "returned_count": len(recommendations),
                "filters_applied": {
                    "category": category,
                    "price_range": price_range,
                    "limit": limit
                }
            }
        
        except BackendError as e:
            logger.error(f"RecommendationTool: Backend error - {e.message}")
            return {
                "success": False,
                **e.to_dict()
            }
        except Exception as e:
            logger.error(f"RecommendationTool: Unexpected error - {str(e)}")
            return {
                "success": False,
                "error": "Unexpected error while getting recommendations",
                "error_type": "unexpected_error",
                "details": str(e)
            }
    
    def get_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM function calling.
        
        Returns:
            Tool definition with name, description, and parameters
        """
        return {
            "name": "get_recommendations",
            "description": "Get personalized product recommendations based on criteria. Filter by category, price range, or get general recommendations. Returns up to the specified limit of matching products.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional product category or type to filter by (matches name or description)"
                    },
                    "price_range": {
                        "type": "object",
                        "properties": {
                            "min": {
                                "type": "number",
                                "description": "Minimum price (inclusive)"
                            },
                            "max": {
                                "type": "number",
                                "description": "Maximum price (inclusive)"
                            }
                        },
                        "description": "Optional price range filter"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of recommendations to return (default: 5)",
                        "default": 5
                    }
                }
            }
        }



class ToolRegistry:
    """
    Registry for managing and executing LLM tools.
    
    Provides centralized access to all available tools and their definitions
    for LLM function calling.
    """
    
    def __init__(self, backend_client: BackendClient):
        """
        Initialize the tool registry with all available tools.
        
        Args:
            backend_client: Client for communicating with the backend API
        """
        self.backend_client = backend_client
        self._tools: Dict[str, Tool] = {}
        
        # Register all tools
        self._register_tool(ProductBrowserTool(backend_client))
        self._register_tool(CartManagerTool(backend_client))
        self._register_tool(RecommendationTool(backend_client))
        
        logger.info(f"ToolRegistry initialized with {len(self._tools)} tools")
    
    def _register_tool(self, tool: Tool):
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
        """
        tool_name = tool.get_definition()["name"]
        self._tools[tool_name] = tool
        logger.debug(f"Registered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)
    
    def get_all_tool_definitions(self) -> list[Dict[str, Any]]:
        """
        Get all tool definitions for LLM function calling.
        
        Returns:
            List of tool definition dictionaries
        """
        return [tool.get_definition() for tool in self._tools.values()]
    
    async def execute_tool(self, tool_name: str, **parameters) -> Dict[str, Any]:
        """
        Execute a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            **parameters: Tool-specific parameters
            
        Returns:
            Dictionary with tool execution results or error information
        """
        tool = self.get_tool(tool_name)
        
        if tool is None:
            logger.error(f"ToolRegistry: Tool not found: {tool_name}")
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "error_type": "tool_not_found"
            }
        
        logger.info(f"ToolRegistry: Executing tool {tool_name} with parameters: {parameters}")
        
        try:
            result = await tool.execute(**parameters)
            return result
        except Exception as e:
            logger.error(f"ToolRegistry: Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing tool {tool_name}",
                "error_type": "execution_error",
                "details": str(e)
            }
    
    def list_tools(self) -> list[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
