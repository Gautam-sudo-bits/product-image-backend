"""
Update Frontend Operations Based on Test Results
Reads validation report and comments out failed operations
"""
import sys
import os
import re
from datetime import datetime

FRONTEND_OPERATIONS_FILE = r"E:\product-image-ui\src\assets\components\operations-data.js"
REPORT_FILE = "test_report.txt"

def parse_test_report(report_path):
    """
    Parse test report and extract PASS/FAIL statuses
    
    Returns:
        dict: {operation_id: 'PASS'/'FAIL'/'SKIP'}
    """
    if not os.path.exists(report_path):
        print(f"❌ Report file not found: {report_path}")
        return None
    
    results = {}
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find operation results
    # Looking for: [01] Operation Name ... STATUS: [PASS] or STATUS: [FAIL]
    pattern = r'\[(\d+)\].*?STATUS:\s*\[\s*(PASS|FAIL|SKIP)\s*\]'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for op_id_str, status in matches:
        op_id = int(op_id_str)
        results[op_id] = status.strip().upper()
    
    return results

def update_frontend_file(results):
    """
    Update frontend operations-data.js file
    Comment out operations marked as FAIL
    """
    if not os.path.exists(FRONTEND_OPERATIONS_FILE):
        print(f"❌ Frontend file not found: {FRONTEND_OPERATIONS_FILE}")
        print(f"   Please check the path is correct")
        return False
    
    # Read current file
    with open(FRONTEND_OPERATIONS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Backup original
    backup_path = FRONTEND_OPERATIONS_FILE + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Backup created: {backup_path}")
    
    # Process file
    updated_lines = []
    in_operation_block = False
    current_op_id = None
    block_lines = []
    
    for line in lines:
        # Detect start of operation block: { id: X,
        id_match = re.search(r'^\s*{\s*$', line) or re.search(r'id:\s*(\d+)', line)
        
        if id_match:
            in_operation_block = True
            # Try to extract ID from this line or next
            id_num_match = re.search(r'id:\s*(\d+)', line)
            if id_num_match:
                current_op_id = int(id_num_match.group(1))
            block_lines = [line]
        elif in_operation_block:
            block_lines.append(line)
            
            # Check if we found the id in this line
            if current_op_id is None:
                id_num_match = re.search(r'id:\s*(\d+)', line)
                if id_num_match:
                    current_op_id = int(id_num_match.group(1))
            
            # Detect end of block: },
            if re.search(r'^\s*},?\s*$', line):
                in_operation_block = False
                
                # Check if this operation should be commented out
                if current_op_id and results.get(current_op_id) == 'FAIL':
                    # Comment out the entire block
                    commented_block = ['  // FAILED - Auto-commented by test script\n']
                    commented_block += ['  // ' + l for l in block_lines]
                    updated_lines.extend(commented_block)
                    print(f"   ❌ Commented out operation {current_op_id}")
                else:
                    # Keep as-is
                    updated_lines.extend(block_lines)
                    if current_op_id:
                        status = results.get(current_op_id, 'UNKNOWN')
                        if status == 'PASS':
                            print(f"   ✅ Kept operation {current_op_id} (PASS)")
                
                # Reset
                current_op_id = None
                block_lines = []
        else:
            updated_lines.append(line)
    
    # Write updated file
    with open(FRONTEND_OPERATIONS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    print(f"\n✅ Frontend file updated: {FRONTEND_OPERATIONS_FILE}")
    return True

def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("🔄 AUTO-UPDATE FRONTEND OPERATIONS")
    print("=" * 80)
    
    # Check for custom report path
    report_path = sys.argv[1] if len(sys.argv) > 1 else REPORT_FILE
    
    print(f"📄 Reading report: {report_path}")
    
    # Parse report
    results = parse_test_report(report_path)
    if not results:
        print("❌ No valid results found in report")
        print("\nMake sure you've filled in PASS/FAIL for each operation")
        print("Expected format: STATUS: [PASS] or STATUS: [FAIL]")
        return
    
    # Summary
    print(f"\n📊 Parsed {len(results)} operations:")
    pass_count = sum(1 for v in results.values() if v == 'PASS')
    fail_count = sum(1 for v in results.values() if v == 'FAIL')
    skip_count = sum(1 for v in results.values() if v == 'SKIP')
    
    print(f"   ✅ PASS: {pass_count}")
    print(f"   ❌ FAIL: {fail_count}")
    print(f"   ⏭️  SKIP: {skip_count}")
    
    if fail_count == 0:
        print("\n🎉 All operations passed! No updates needed.")
        return
    
    # Confirm before updating
    print(f"\n⚠️  This will comment out {fail_count} failed operations in the frontend.")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Cancelled")
        return
    
    # Update frontend file
    print("\n🔄 Updating frontend file...")
    if update_frontend_file(results):
        print("\n" + "=" * 80)
        print("✅ UPDATE COMPLETE")
        print("=" * 80)
        print("\nFailed operations have been commented out in:")
        print(f"  {FRONTEND_OPERATIONS_FILE}")
        print("\nUsers will only see working operations in the dropdown.")
        print("\nTo restore, use the backup file created.")
        print("=" * 80 + "\n")
    else:
        print("\n❌ Update failed. Check error messages above.")

if __name__ == "__main__":
    main()