# -*- coding: utf-8 -*-
# 腾讯云API签名v3实现示例
# 本代码基于腾讯云API签名v3文档实现: https://cloud.tencent.com/document/product/213/30654
# 请严格按照文档说明使用，不建议随意修改签名相关代码

import os
import hashlib
import hmac
import json
import sys
import time
import base64
from datetime import datetime
from PIL import Image
import io
if sys.version_info[0] <= 2:
    from httplib import HTTPSConnection
else:
    from http.client import HTTPSConnection


def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def idcard_ocr(image, card_side=None):
    """
    调用腾讯云身份证OCR接口
    
    Args:
        image: 图片文件路径（必需）
        card_side: 身份证正反面（可选），如果不提供则从文件名自动识别
                  FRONT为身份证有照片的一面（人像面），BACK为身份证有国徽的一面（国徽面）
        
    Returns:
        解析后的JSON响应(dict)
    """
    
    if not os.path.exists(image):
        raise FileNotFoundError(f"图片文件不存在: {image}")
    
    # 读取图片并编码为Base64
    with open(image, 'rb') as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # 检查Base64编码后的大小（不超过10MB）
    base64_size_mb = len(image_base64) / (1024 * 1024)
    
    if base64_size_mb > 10:
        print(f"警告: 图片Base64编码后大小为 {base64_size_mb:.2f}MB，超过10MB限制")
        print(f"正在压缩图片...")
        
        # 压缩图片
        img = Image.open(image)
        
        # 保存原始格式和模式
        original_format = img.format or 'PNG'
        
        # 如果是RGBA模式，转换为RGB（JPEG不支持透明度）
        if img.mode in ('RGBA', 'LA', 'P'):
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 尝试不同的质量级别进行压缩
        quality = 95
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            # 压缩图片到内存
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_data = output.getvalue()
            
            # 重新编码为Base64
            image_base64 = base64.b64encode(compressed_data).decode('utf-8')
            compressed_size_mb = len(image_base64) / (1024 * 1024)
            
            print(f"  尝试 {attempt + 1}: 质量={quality}, 大小={compressed_size_mb:.2f}MB")
            
            if compressed_size_mb <= 10:
                print(f"✓ 压缩成功: {base64_size_mb:.2f}MB -> {compressed_size_mb:.2f}MB")
                break
            
            # 降低质量继续压缩
            quality -= 10
            attempt += 1
            
            if quality < 10:
                # 如果质量已经很低，尝试缩小图片尺寸
                print(f"  质量已降至最低，尝试缩小图片尺寸...")
                width, height = img.size
                img = img.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
                quality = 85  # 重置质量
        
        if compressed_size_mb > 10:
            raise ValueError(f"无法将图片压缩到10MB以下。当前大小: {compressed_size_mb:.2f}MB")
        
        # 更新image_data为压缩后的数据（用于后续可能的保存）
        image_data = compressed_data
    
    # 从文件名提取卡片正反面信息
    if card_side is None:
        filename = os.path.basename(image).lower()
        # 检查文件名中是否包含"正面"、"front"等关键词
        if '正面' in filename or 'front' in filename or '人像' in filename:
            card_side = "FRONT"
        elif '反面' in filename or 'back' in filename or '国徽' in filename:
            card_side = "BACK"
        else:
            # 如果文件名中没有明确标识，设置为None
            card_side = None
    
    # 构建请求参数
    params = {
        "ImageBase64": image_base64
    }
    
    # 只有当card_side不为None时才添加到参数中
    if card_side is not None:
        params["CardSide"] = card_side
    
    # Config参数需要是JSON字符串格式
    config = {
        "CropIdCard": False,
        "CropPortrait": False
    }
    params["Config"] = json.dumps(config)
    
    payload = json.dumps(params)
    # 密钥信息从环境变量读取，需要提前在环境变量中设置 TENCENTCLOUD_SECRET_ID 和 TENCENTCLOUD_SECRET_KEY
    # 使用环境变量方式可以避免密钥硬编码在代码中，提高安全性
    # 生产环境建议使用更安全的密钥管理方案，如密钥管理系统(KMS)、容器密钥注入等
    # 请参见：https://cloud.tencent.com/document/product/1278/85305
    # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
    secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
    secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")
    token = ""

    service = "ocr"
    host = "ocr.tencentcloudapi.com"
    region = ""
    version = "2018-11-19"
    action = "IDCardOCR"
    endpoint = "https://ocr.tencentcloudapi.com"
    algorithm = "TC3-HMAC-SHA256"
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (ct, host, action.lower())
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (http_request_method + "\n" +
                         canonical_uri + "\n" +
                         canonical_querystring + "\n" +
                         canonical_headers + "\n" +
                         signed_headers + "\n" +
                         hashed_request_payload)

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (algorithm + "\n" +
                      str(timestamp) + "\n" +
                      credential_scope + "\n" +
                      hashed_canonical_request)

    # ************* 步骤 3：计算签名 *************
    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (algorithm + " " +
                     "Credential=" + secret_id + "/" + credential_scope + ", " +
                     "SignedHeaders=" + signed_headers + ", " +
                     "Signature=" + signature)

    # ************* 步骤 5：构造并发起请求 *************
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": timestamp,
        "X-TC-Version": version
    }
    if region:
        headers["X-TC-Region"] = region
    if token:
        headers["X-TC-Token"] = token

    try:
        req = HTTPSConnection(host)
        req.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
        resp = req.getresponse()
        response_data = resp.read()
        return json.loads(response_data.decode('utf-8'))
    except Exception as err:
        raise err

