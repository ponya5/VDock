#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify all action types work correctly."""

import sys
import json
import os

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_pynput_import():
    """Test if pynput is available."""
    print("=" * 60)
    print("TEST 1: pynput Library Import")
    print("=" * 60)
    try:
        from pynput.keyboard import Controller, Key
        print("✓ SUCCESS: pynput imported successfully")
        print(f"  - Controller class available: {Controller is not None}")
        print(f"  - Key class available: {Key is not None}")
        return True
    except ImportError as e:
        print(f"✗ FAILED: pynput import failed - {e}")
        print("  Run: pip install pynput")
        return False

def test_action_imports():
    """Test if all action classes can be imported."""
    print("\n" + "=" * 60)
    print("TEST 2: Action Class Imports")
    print("=" * 60)
    
    actions_to_test = [
        ('URLAction', 'actions.url_action'),
        ('ProgramAction', 'actions.program_action'),
        ('CommandAction', 'actions.command_action'),
        ('HotkeyAction', 'actions.hotkey_action'),
        ('MultiAction', 'actions.multi_action'),
        ('MacroAction', 'actions.macro_action'),
        ('SystemAction', 'actions.system_action'),
        ('CrossPlatformAction', 'actions.cross_platform_action'),
    ]
    
    all_passed = True
    for class_name, module_name in actions_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            action_class = getattr(module, class_name)
            print(f"✓ {class_name:25s} - Imported successfully")
        except Exception as e:
            print(f"✗ {class_name:25s} - Failed: {e}")
            all_passed = False
    
    return all_passed

def test_action_executor():
    """Test if ActionExecutor can be instantiated."""
    print("\n" + "=" * 60)
    print("TEST 3: Action Executor")
    print("=" * 60)
    
    try:
        from actions.action_executor import ActionExecutor
        executor = ActionExecutor()
        print(f"✓ ActionExecutor instantiated successfully")
        print(f"  Registered action types: {list(executor.ACTION_CLASSES.keys())}")
        return True
    except Exception as e:
        print(f"✗ ActionExecutor failed: {e}")
        return False

def test_hotkey_action_validation():
    """Test HotkeyAction validation."""
    print("\n" + "=" * 60)
    print("TEST 4: HotkeyAction Validation")
    print("=" * 60)
    
    try:
        from actions.hotkey_action import HotkeyAction
        
        # Test valid config
        valid_config = {'keys': ['ctrl', 'c']}
        action = HotkeyAction(valid_config)
        is_valid = action.validate()
        print(f"✓ Valid config {'PASSED' if is_valid else 'FAILED'}: {valid_config}")
        
        # Test invalid config (no keys)
        invalid_config = {}
        action = HotkeyAction(invalid_config)
        is_invalid = not action.validate()
        print(f"✓ Invalid config correctly {'REJECTED' if is_invalid else 'ACCEPTED (BAD)'}: {invalid_config}")
        
        return is_valid and is_invalid
    except Exception as e:
        print(f"✗ HotkeyAction validation test failed: {e}")
        return False

def test_system_action_validation():
    """Test SystemAction validation."""
    print("\n" + "=" * 60)
    print("TEST 5: SystemAction Validation")
    print("=" * 60)
    
    try:
        from actions.system_action import SystemAction
        
        valid_actions = ['volume_up', 'volume_down', 'volume_mute', 
                        'media_play_pause', 'media_next', 'media_previous']
        
        all_valid = True
        for action_name in valid_actions:
            config = {'action': action_name}
            action = SystemAction(config)
            is_valid = action.validate()
            status = "✓" if is_valid else "✗"
            print(f"{status} {action_name:20s} - {'VALID' if is_valid else 'INVALID'}")
            all_valid = all_valid and is_valid
        
        return all_valid
    except Exception as e:
        print(f"✗ SystemAction validation test failed: {e}")
        return False

def test_profile_loading():
    """Test if test profile can be loaded."""
    print("\n" + "=" * 60)
    print("TEST 6: Test Profile Loading")
    print("=" * 60)
    
    try:
        with open('data/profiles/test-profile-actions.json', 'r') as f:
            profile = json.load(f)
        
        print(f"✓ Profile loaded: {profile['name']}")
        print(f"  - Profile ID: {profile['id']}")
        print(f"  - Scenes: {len(profile['scenes'])}")
        
        for scene in profile['scenes']:
            print(f"  - Scene: {scene['name']}")
            for page in scene.get('pages', []):
                print(f"    - Page: {page['name']} ({len(page.get('buttons', []))} buttons)")
                for button in page.get('buttons', []):
                    action_type = button.get('action', {}).get('type', 'none')
                    print(f"      - {button['label']:20s} [{action_type}]")
        
        return True
    except Exception as e:
        print(f"✗ Profile loading failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n")
    print("+" + "=" * 58 + "+")
    print("|" + " " * 10 + "VDOCK ACTION SYSTEM TEST SUITE" + " " * 17 + "|")
    print("+" + "=" * 58 + "+")
    print()
    
    tests = [
        test_pynput_import,
        test_action_imports,
        test_action_executor,
        test_hotkey_action_validation,
        test_system_action_validation,
        test_profile_loading,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n*** ALL TESTS PASSED! ***")
        print("\nNext steps:")
        print("1. Restart the backend server")
        print("2. Load the 'ACTION TEST PROFILE' in the UI")
        print("3. Test each button manually")
        return 0
    else:
        print(f"\n*** {total - passed} TEST(S) FAILED ***")
        print("\nPlease fix the issues above before proceeding.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

