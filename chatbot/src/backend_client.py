"""
Backend API client for communicating with the Node.js e-commerce backend.

This module provides an async HTTP client for interacting with the backend REST API
endpoints for products, cart management, and reviews.
"""

import httpx
from typing import Optional, Callable, TypeVar, ParamSpec, Dict, Any
import logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class BackendError(Exception):
    """Base exception for backend client errors."""
    def __init__(self, message: str, error_type: str, details: Optional[str] = None):
        self.message = message
        self.error_type = error_type
        self.details = details
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to structured dictionary for tool responses."""
        result = {
            "error": self.message,
            "error_type": self.error_type
        }
        if self.details:
            result["details"] = self.details
        return result

P = ParamSpec('P')
T = TypeVar('T')


def retry_with_backoff(max_attempts: int = 3, backoff_multiplier: float = 1.5, initial_delay: float = 1.0):
    """
    Decorator that retries async functions with exponential backoff.
    
    Retries on connection errors and timeouts. Other HTTP errors are not retried.
    Converts exceptions to BackendError with structured error responses.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_multiplier: Multiplier for exponential backoff (default: 1.5)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except httpx.ConnectError as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: Connection error. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: Connection error - {str(e)}"
                        )
                        raise BackendError(
                            message="Unable to connect to backend service",
                            error_type="connection_error",
                            details=str(e)
                        )
                except httpx.TimeoutException as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: Timeout. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: Timeout after {max_attempts} attempts"
                        )
                        raise BackendError(
                            message="Backend service request timed out",
                            error_type="timeout_error",
                            details=f"Request timed out after {max_attempts} attempts"
                        )
                except httpx.HTTPStatusError as e:
                    # Don't retry HTTP status errors (404, 500, etc.)
                    status_code = e.response.status_code
                    
                    if status_code == 404:
                        logger.info(f"{func.__name__} returned 404: Resource not found")
                        raise BackendError(
                            message="Resource not found",
                            error_type="not_found",
                            details=f"The requested resource was not found (HTTP 404)"
                        )
                    elif status_code >= 500:
                        logger.error(f"{func.__name__} returned {status_code}: Server error - {str(e)}")
                        raise BackendError(
                            message="Backend service error",
                            error_type="server_error",
                            details=f"Backend returned HTTP {status_code}"
                        )
                    else:
                        # Other HTTP errors (4xx)
                        logger.error(f"{func.__name__} returned {status_code}: {str(e)}")
                        raise BackendError(
                            message=f"Backend request failed with status {status_code}",
                            error_type="http_error",
                            details=str(e)
                        )
                except Exception as e:
                    # Catch any other unexpected errors
                    logger.error(f"Unexpected error in {func.__name__}: {type(e).__name__} - {str(e)}")
                    raise BackendError(
                        message="Unexpected error communicating with backend",
                        error_type="unexpected_error",
                        details=f"{type(e).__name__}: {str(e)}"
                    )
        
        return wrapper
    return decorator


class BackendClient:
    """
    Async HTTP client for backend API communication.
    
    Provides methods for all backend API endpoints with timeout configuration
    and error handling.
    """
    
    def __init__(self, base_url: str, timeout: int = 10):
        """
        Initialize the backend client.
        
        Args:
            base_url: Base URL of the backend API (e.g., http://localhost:3001)
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"BackendClient initialized with base_url={self.base_url}, timeout={self.timeout}s")
    
    @retry_with_backoff(max_attempts=3, backoff_multiplier=1.5)
    async def get_products(self) -> list[dict]:
        """
        Get all products from the catalog.
        
        Returns:
            List of product dictionaries
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/products"
        logger.debug(f"Fetching products from {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Retrieved {len(data)} products")
            return data
    
    @retry_with_backoff(max_attempts=3, backoff_multiplier=1.5)
    async def get_product_details(self, product_id: int) -> dict:
        """
        Get detailed information about a specific product including reviews.
        
        Args:
            product_id: ID of the product to retrieve
            
        Returns:
            Product dictionary with reviews
            
        Raises:
            httpx.HTTPError: If the request fails or product not found
        """
        url = f"{self.base_url}/api/products/{product_id}"
        logger.debug(f"Fetching product details from {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Retrieved product {product_id}: {data.get('name', 'Unknown')}")
            return data

    @retry_with_backoff(max_attempts=3, backoff_multiplier=1.5)
    async def get_cart(self) -> list[dict]:
        """
        Get all items in the shopping cart with product details.
        
        Returns:
            List of cart item dictionaries with product information
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/cart"
        logger.debug(f"Fetching cart from {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Retrieved cart with {len(data)} items")
            return data
    
    @retry_with_backoff(max_attempts=3, backoff_multiplier=1.5)
    async def add_to_cart(self, product_id: int, quantity: int) -> dict:
        """
        Add a product to the shopping cart.
        
        Args:
            product_id: ID of the product to add
            quantity: Quantity to add
            
        Returns:
            Dictionary with success status and cart item ID
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/cart"
        payload = {"product_id": product_id, "quantity": quantity}
        logger.debug(f"Adding to cart: {payload}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Added product {product_id} (qty: {quantity}) to cart")
            return data
    
    @retry_with_backoff(max_attempts=3, backoff_multiplier=1.5)
    async def update_cart_item(self, cart_id: int, quantity: int) -> dict:
        """
        Update the quantity of a cart item.
        
        Args:
            cart_id: ID of the cart item to update
            quantity: New quantity
            
        Returns:
            Dictionary with success status
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/cart/{cart_id}"
        payload = {"quantity": quantity}
        logger.debug(f"Updating cart item {cart_id}: {payload}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Updated cart item {cart_id} to quantity {quantity}")
            return data
    
    @retry_with_backoff(max_attempts=3, backoff_multiplier=1.5)
    async def remove_cart_item(self, cart_id: int) -> dict:
        """
        Remove an item from the shopping cart.
        
        Args:
            cart_id: ID of the cart item to remove
            
        Returns:
            Dictionary with success status
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/cart/{cart_id}"
        logger.debug(f"Removing cart item {cart_id}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Removed cart item {cart_id}")
            return data
