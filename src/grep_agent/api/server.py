"""
API服务模块 - 简化版本
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.models import AppConfig
from ..utils.logger import get_logger


def create_app(config: AppConfig) -> FastAPI:
    """
    创建FastAPI应用
    
    Args:
        config: 应用配置
        
    Returns:
        FastAPI: FastAPI应用实例
    """
    app = FastAPI(
        title="Grep搜索Agent API",
        description="智能化的grep搜索Agent系统API",
        version="0.1.0",
    )
    
    # CORS配置
    if config.api.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 健康检查端点
    @app.get("/api/v1/health")
    async def health_check():
        """健康检查"""
        from datetime import datetime
        return {
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
        }
    
    # TODO: 实现完整的API端点
    # - POST /api/v1/sessions - 创建搜索会话
    # - GET /api/v1/sessions/{session_id} - 获取会话状态
    # - GET /api/v1/sessions/{session_id}/result - 获取会话结果
    # - DELETE /api/v1/sessions/{session_id} - 取消会话
    # - GET /api/v1/sessions - 列出所有会话
    
    return app


def run_api_server(config: AppConfig):
    """
    运行API服务器
    
    Args:
        config: 应用配置
    """
    logger = get_logger()
    logger.info(f"启动API服务器: {config.api.host}:{config.api.port}")
    
    app = create_app(config)
    
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        log_level=config.system.log_level.lower(),
    )
