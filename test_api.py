"""
API测试脚本
"""

import openai

def test_qwen3_api():
    print("测试Qwen3 API...")
    
    # 设置API配置
    openai.api_key = "dummy"
    openai.api_base = "http://10.10.4.83:9998/v1"
    
    try:
        response = openai.ChatCompletion.create(
            model="qwen3-instruct",
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ],
            max_tokens=10
        )
        print("✅ Qwen3 API调用成功")
        print(f"响应: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Qwen3 API调用失败: {e}")
        return False

def test_qwen25_api():
    print("\n测试Qwen2.5 API...")
    
    # 设置API配置
    openai.api_key = "dummy"
    openai.api_base = "http://10.10.2.71:8007/v1"
    
    try:
        response = openai.ChatCompletion.create(
            model="Qwen/Qwen2.5-72B-Instruct-Raw",
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ],
            max_tokens=10
        )
        print("✅ Qwen2.5 API调用成功")
        print(f"响应: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Qwen2.5 API调用失败: {e}")
        return False

if __name__ == "__main__":
    test_qwen3_api()
    test_qwen25_api() 