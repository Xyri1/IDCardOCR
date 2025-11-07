# Bug Fix: Config Parameter Type Error

## Issue
When processing ID card images, the API returned an error:
```
InvalidParameter - The value type of parameter `Config` is not valid, input type should be `string`
```

## Root Cause
The Tencent Cloud IDCardOCR API requires the `Config` parameter to be a **JSON string**, not a nested object/dictionary.

### Incorrect Format (Before)
```python
params = {
    "ImageBase64": image_base64,
    "Config": {           # ❌ Wrong: Config as dictionary
        "Quality": True
    }
}
```

When serialized, this becomes:
```json
{
  "ImageBase64": "...",
  "Config": {              // ❌ Wrong: nested object
    "Quality": true
  }
}
```

### Correct Format (After)
```python
params = {
    "ImageBase64": image_base64
}

# Config needs to be a JSON string
config = {
    "CropIdCard": False,
    "CropPortrait": False
}
params["Config"] = json.dumps(config)  # ✓ Correct: Config as JSON string
```

When serialized, this becomes:
```json
{
  "ImageBase64": "...",
  "Config": "{\"CropIdCard\": false, \"CropPortrait\": false}"  // ✓ Correct: string
}
```

## Solution Applied

Updated `src/tencentcloud_idcard_ocr.py`:
- Removed the `Quality` parameter (not needed)
- Changed `Config` to be a JSON string using `json.dumps()`
- Added standard config options: `CropIdCard` and `CropPortrait` set to `False`

## Config Options

Available options in the Config JSON string:
- **`CropIdCard`**: Whether to crop and return the ID card image (default: false)
- **`CropPortrait`**: Whether to crop and return the portrait photo (default: false)

Both are set to `False` as we only need the OCR text data, not the cropped images.

## Testing

Verify the fix with:
```bash
python main.py
```

The error should no longer occur, and both front and back images should process successfully.

## References

- [Tencent Cloud IDCardOCR API Documentation](https://cloud.tencent.com/document/product/866/33524)
- Parameter format: Config parameter must be a JSON string, not an object

---

**Fixed**: November 7, 2025  
**Status**: Resolved ✓

