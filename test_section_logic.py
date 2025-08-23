#!/usr/bin/env python3
"""
Test script for the new contiguous section creation logic
"""

# Mock QTreeWidgetItem for testing
class MockItem:
    def __init__(self, name):
        self.name = name
        self.index = None
    
    def text(self, col):
        return self.name

# Mock the staff list methods
class MockStaffList:
    def __init__(self, items):
        self.items = items
        for i, item in enumerate(items):
            item.index = i
    
    def indexOfTopLevelItem(self, item):
        return item.index

# Copy the logic methods we implemented
def is_selection_contiguous(selected_items, staff_list):
    """Check if the selected items form a contiguous group in the staff list"""
    if not selected_items:
        return False
    
    # Get indices of selected items
    indices = []
    for item in selected_items:
        index = staff_list.indexOfTopLevelItem(item)
        indices.append(index)
    
    # Sort indices
    indices.sort()
    
    # Check if indices are consecutive
    for i in range(len(indices) - 1):
        if indices[i+1] - indices[i] != 1:
            return False
    
    return True

def get_contiguous_groups(selected_items, staff_list):
    """Split selected items into contiguous groups"""
    if not selected_items:
        return []
    
    # Get indices of selected items
    item_indices = []
    for item in selected_items:
        index = staff_list.indexOfTopLevelItem(item)
        item_indices.append((index, item))
    
    # Sort by index
    item_indices.sort(key=lambda x: x[0])
    
    # Group contiguous items
    groups = []
    current_group = [item_indices[0]]
    
    for i in range(1, len(item_indices)):
        current_index, current_item = item_indices[i]
        prev_index, prev_item = item_indices[i-1]
        
        if current_index - prev_index == 1:
            # Contiguous, add to current group
            current_group.append(item_indices[i])
        else:
            # Not contiguous, start new group
            groups.append([item[1] for item in current_group])  # Extract items only
            current_group = [item_indices[i]]
    
    # Add the last group
    groups.append([item[1] for item in current_group])
    
    return groups

def test_contiguous_logic():
    """Test the contiguous selection logic"""
    print("Testing contiguous section creation logic...\n")
    
    # Create mock items
    items = [
        MockItem("Violin I"), 
        MockItem("Violin II"), 
        MockItem("Viola"), 
        MockItem("Cello"), 
        MockItem("Piano"), 
        MockItem("Flute"), 
        MockItem("Oboe")
    ]
    staff_list = MockStaffList(items)
    
    # Test Case 1: Contiguous selection (0, 1, 2)
    print("Test Case 1: Contiguous selection [0, 1, 2]")
    selection = [items[0], items[1], items[2]]
    is_contiguous = is_selection_contiguous(selection, staff_list)
    groups = get_contiguous_groups(selection, staff_list)
    print(f"  Selected: {[item.name for item in selection]}")
    print(f"  Is contiguous: {is_contiguous}")
    print(f"  Groups: {[[item.name for item in group] for group in groups]}")
    print(f"  Expected: True, 1 group")
    print(f"  ✓ PASS\n" if is_contiguous and len(groups) == 1 else "  ✗ FAIL\n")
    
    # Test Case 2: Non-contiguous selection (0, 2, 4)
    print("Test Case 2: Non-contiguous selection [0, 2, 4]")
    selection = [items[0], items[2], items[4]]
    is_contiguous = is_selection_contiguous(selection, staff_list)
    groups = get_contiguous_groups(selection, staff_list)
    print(f"  Selected: {[item.name for item in selection]}")
    print(f"  Is contiguous: {is_contiguous}")
    print(f"  Groups: {[[item.name for item in group] for group in groups]}")
    print(f"  Expected: False, 3 groups")
    print(f"  ✓ PASS\n" if not is_contiguous and len(groups) == 3 else "  ✗ FAIL\n")
    
    # Test Case 3: Two contiguous groups (0,1) and (3,4,5)
    print("Test Case 3: Two contiguous groups [0, 1, 3, 4, 5]")
    selection = [items[0], items[1], items[3], items[4], items[5]]
    is_contiguous = is_selection_contiguous(selection, staff_list)
    groups = get_contiguous_groups(selection, staff_list)
    print(f"  Selected: {[item.name for item in selection]}")
    print(f"  Is contiguous: {is_contiguous}")
    print(f"  Groups: {[[item.name for item in group] for group in groups]}")
    print(f"  Expected: False, 2 groups")
    print(f"  ✓ PASS\n" if not is_contiguous and len(groups) == 2 else "  ✗ FAIL\n")
    
    # Test Case 4: Single item selection
    print("Test Case 4: Single item selection [2]")
    selection = [items[2]]
    is_contiguous = is_selection_contiguous(selection, staff_list)
    groups = get_contiguous_groups(selection, staff_list)
    print(f"  Selected: {[item.name for item in selection]}")
    print(f"  Is contiguous: {is_contiguous}")
    print(f"  Groups: {[[item.name for item in group] for group in groups]}")
    print(f"  Expected: True, 1 group")
    print(f"  ✓ PASS\n" if is_contiguous and len(groups) == 1 else "  ✗ FAIL\n")
    
    # Test Case 5: Empty selection
    print("Test Case 5: Empty selection []")
    selection = []
    is_contiguous = is_selection_contiguous(selection, staff_list)
    groups = get_contiguous_groups(selection, staff_list)
    print(f"  Selected: {[item.name for item in selection]}")
    print(f"  Is contiguous: {is_contiguous}")
    print(f"  Groups: {[[item.name for item in group] for group in groups]}")
    print(f"  Expected: False, 0 groups")
    print(f"  ✓ PASS\n" if not is_contiguous and len(groups) == 0 else "  ✗ FAIL\n")

if __name__ == "__main__":
    test_contiguous_logic() 