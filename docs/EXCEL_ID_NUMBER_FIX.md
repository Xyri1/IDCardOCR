# Excel ID Number Display Fix

## Problem

When opening `id_card_results.csv` in Excel, the `id_num` column shows numbers in scientific notation or gets rounded:
- `441625200703085784` becomes `4.41625E+17`
- Last digits may be lost due to Excel's 15-digit precision limit

## Solutions

### Solution 1: Apostrophe Prefix (Automatic) ✅ IMPLEMENTED

The script now automatically adds an apostrophe (`'`) before ID numbers:

```python
# In main.py
id_num = resp_data.get('IdNum', '')
result['id_num'] = f"'{id_num}" if id_num else ''
```

**Pros:**
- Automatic, no user action needed
- Works in Excel, Google Sheets, LibreOffice
- Apostrophe is hidden in Excel (cleaner display)
- ID numbers display as text
- Standard Excel text formatting method

**Cons:**
- Apostrophe is technically part of the data
- Visible in formula bar and when editing cell

### Solution 2: Quote Prefix (Alternative)

Add `="` prefix and `"` suffix to force text format:

```python
result['id_num'] = f'="{id_num}"' if id_num else ''
```

Result in CSV: `="441625200703085784"`
Display in Excel: `441625200703085784` (as text)

### Solution 3: Import Wizard (Manual)

When opening the CSV in Excel:

1. **Don't double-click the CSV file**
2. Open Excel first
3. Go to **Data** → **From Text/CSV**
4. Select `id_card_results.csv`
5. In the import wizard:
   - Click "Transform Data"
   - Select the `id_num` column
   - Change type to "Text"
   - Click "Close & Load"

**Pros:**
- Clean data (no extra characters)
- Full control over formatting

**Cons:**
- Manual process each time
- Easy to forget

### Solution 4: Open in Google Sheets (Quick Fix)

Google Sheets handles long numbers better:

1. Upload CSV to Google Drive
2. Open with Google Sheets
3. ID numbers display correctly
4. Export to Excel if needed

### Solution 5: Format in Excel (After Opening)

If you already opened the file:

1. Select the `id_num` column
2. Right-click → **Format Cells**
3. Choose **Text** (not Number)
4. The numbers are already rounded - **this won't fix existing data**
5. **Close without saving**, reopen using Solution 1 or 3

## Current Implementation

The script now uses **Solution 1 (Apostrophe Prefix)** automatically.

### How to Use

Just run the script normally:
```bash
python main.py
```

The CSV will have ID numbers prefixed with an apostrophe, which makes Excel treat them as text.

### Viewing the ID Numbers

**In Excel:**
- Open the file normally
- ID numbers display correctly
- No scientific notation
- All digits preserved

**In Text Editor:**
- You'll see an apostrophe before each ID: `'441625200703085784`
- This is normal and expected

**In Excel:**
- The apostrophe is hidden in the cell display
- Visible only in the formula bar when cell is selected

**Copying from Excel:**
- When you copy a cell, the apostrophe is included
- To copy just the number: double-click cell, select text (without apostrophe), copy

## Alternative: Use Both Solutions

For maximum compatibility, you can use both tab prefix AND proper import:

1. Script adds tab prefix (prevents auto-conversion)
2. Use Import Wizard to clean up and set as text
3. Best of both worlds

## Technical Details

### Why Excel Converts to Number

- Excel auto-detects data types
- Long digit sequences are assumed to be numbers
- Numbers have 15-digit precision limit
- 18-digit ID numbers lose precision

### Why Tab Works

- Tab character signals "this is text, not a number"
- Excel respects the tab and doesn't convert
- Compatible with CSV format
- Widely supported

### Character Options

| Prefix | Excel Result | Compatibility | Clean? |
|--------|-------------|---------------|--------|
| `'` (apostrophe) | Text, prefix hidden | High | High |
| `\t` (tab) | Text, displays correctly | High | Medium |
| `="..."` | Text, formula result | Medium | Low |
| None + Import Wizard | Text | High | High |

## Recommendation

**For all use cases**: Use current implementation (apostrophe prefix) ✅

The apostrophe prefix is:
- Clean (hidden in Excel)
- Universal (works everywhere)
- Standard (Excel's recommended method)
- Simple (no special import needed)

## Testing the Fix

1. Run the script:
   ```bash
   python main.py
   ```

2. Open `id_card_results.csv` in Excel

3. Check the `id_num` column:
   - Should show full 18-digit numbers
   - Should be left-aligned (text format)
   - No scientific notation
   - No visible apostrophe in the cell

4. Click on a cell:
   - Formula bar shows apostrophe + number: `'441625200703085784`
   - This is correct and normal

## Using Different Prefix

Current implementation uses apostrophe (recommended).

If you prefer tab instead, edit `main.py` line 189:

```python
# Change from (current):
result['id_num'] = f"'{id_num}" if id_num else ''

# To (tab prefix):
result['id_num'] = f"\t{id_num}" if id_num else ''
```

Apostrophe is recommended as it's cleaner and more standard.

---

**Issue**: Excel converts ID numbers to scientific notation  
**Fix**: Apostrophe prefix added automatically  
**Status**: Resolved ✅

