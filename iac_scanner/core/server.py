"""Server implementation for the IAC Scanner."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from iac_scanner.plugins import discover_plugins, get_plugin, get_all_plugins
from iac_scanner.core.llm import LLMClient


class ScanRequest(BaseModel):
    """Model for scan requests."""
    
    path: str = Field(..., description="Path to the IAC code to scan")
    tools: List[str] = Field(default_list=[], description="Tools to use for scanning")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the scan")


class ScanResponse(BaseModel):
    """Model for scan responses."""
    
    success: bool = Field(..., description="Whether the scan was successful")
    results: Dict[str, Any] = Field(..., description="Results of the scan")
    errors: Optional[Dict[str, str]] = Field(default=None, description="Errors encountered during scanning")


class ServerConfig(BaseModel):
    """Model for server configuration."""
    
    host: str = Field(default="localhost", description="Host to bind the server to")
    port: int = Field(default=8000, description="Port to bind the server to")
    log_level: str = Field(default="INFO", description="Logging level")
    llm_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the LLM")


class Server:
    """IAC Scanner server implementation."""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """Initialize the server.
        
        Args:
            config: Server configuration
        """
        self.config = config or ServerConfig()
        self.app = FastAPI(
            title="IAC Scanner",
            description="Master Control Program (MCP) Server for LLM-based IAC scanning",
            version="0.1.0",
        )
        self.llm_client = LLMClient(self.config.llm_config)
        
        # Set up logging
        logging_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(level=logging_level)
        self.logger = logging.getLogger("iac_scanner")
        
        # Discover plugins
        discover_plugins()
        
        # Set up routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up the API routes."""
        
        @self.app.get("/")
        async def root():
            return {"message": "IAC Scanner API"}
        
        @self.app.get("/plugins")
        async def list_plugins():
            plugins = get_all_plugins()
            result = {}
            
            for name, plugin_class in plugins.items():
                plugin = plugin_class()
                result[name] = await plugin.get_capabilities()
            
            return result
        
        @self.app.post("/scan", response_model=ScanResponse)
        async def scan(request: ScanRequest):
            path = Path(request.path)
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Path not found: {path}")
            
            # Determine which tools to use
            tools = request.tools or list(get_all_plugins().keys())
            
            # Run the scan with each tool
            results = {}
            errors = {}
            
            for tool_name in tools:
                plugin_class = get_plugin(tool_name)
                if not plugin_class:
                    errors[tool_name] = f"Plugin not found: {tool_name}"
                    continue
                
                try:
                    plugin = plugin_class(request.config.get(tool_name, {}))
                    if not await plugin.validate_config():
                        errors[tool_name] = "Invalid plugin configuration"
                        continue
                    
                    scan_result = await plugin.scan(path)
                    results[tool_name] = scan_result
                except Exception as e:
                    errors[tool_name] = str(e)
            
            # Process the results with the LLM if available
            processed_results = results
            if self.llm_client.is_available():
                try:
                    processed_results = await self.llm_client.process_scan_results(results)
                except Exception as e:
                    self.logger.error(f"Error processing results with LLM: {e}")
            
            return ScanResponse(
                success=len(errors) == 0,
                results=processed_results,
                errors=errors or None
            )
    
    def start(self):
        """Start the server."""
        import uvicorn
        
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
        ) 