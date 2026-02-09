"""
API 客户端模块 - 封装 AI API 调用逻辑
使用 OpenAI Python SDK，支持 Poe API 等兼容接口
"""

import openai
from typing import Optional, Callable


class APIClient:
    """AI API 客户端，使用 OpenAI SDK"""
    
    def __init__(self, api_url: str, api_key: str, model: str = "claude-sonnet-4"):
        """
        初始化 API 客户端
        
        Args:
            api_url: API 基础地址 (base_url)
            api_key: API 密钥
            model: 模型名称
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = 120  # 超时时间（秒）
        
        # 创建 OpenAI 客户端
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_url,
            timeout=self.timeout
        )
    
    def test_connection(self) -> tuple[bool, str]:
        """
        测试 API 连接
        
        Returns:
            (是否成功, 消息)
        """
        try:
            # 发送一个简单的测试请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            
            if response.choices and len(response.choices) > 0:
                return True, "连接成功！"
            else:
                return False, "API 返回异常"
                
        except openai.AuthenticationError:
            return False, "API Key 无效"
        except openai.NotFoundError:
            return False, "API 地址或模型不正确"
        except openai.APITimeoutError:
            return False, "连接超时"
        except openai.APIConnectionError:
            return False, "无法连接到服务器"
        except Exception as e:
            return False, f"错误: {str(e)}"
    
    def generate_article(
        self, 
        title: str, 
        prompt_template: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> tuple[bool, str]:
        """
        根据标题生成文章
        
        Args:
            title: 文章标题
            prompt_template: 提示词模板，使用 {title} 作为占位符
            progress_callback: 进度回调函数
            
        Returns:
            (是否成功, 文章内容或错误信息)
        """
        try:
            # 替换模板中的标题占位符
            prompt = prompt_template.replace("{title}", title)
            
            if progress_callback:
                progress_callback("正在调用 API...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文章写作助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return True, content
            else:
                return False, "API 返回内容为空"
                
        except openai.AuthenticationError:
            return False, "API Key 无效"
        except openai.RateLimitError:
            return False, "API 请求频率超限，请稍后重试"
        except openai.APITimeoutError:
            return False, "请求超时，请稍后重试"
        except openai.APIConnectionError:
            return False, "网络连接失败"
        except Exception as e:
            return False, f"生成失败: {str(e)}"
