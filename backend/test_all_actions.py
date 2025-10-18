"""Test script to verify all action types work correctly."""
import json
import sys
from pathlib import Path
from actions.action_executor import ActionExecutor

# Ensure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_action_types():
    """Test all action types used in the profile."""

    # Load the profile
    profile_path = Path('data/profiles/7f9efef3-25fc-43b8-810a-c1457553b589.json')
    with open(profile_path) as f:
        profile = json.load(f)

    executor = ActionExecutor()
    action_types = set()
    test_results = {}

    # Collect all button actions from all scenes
    for scene in profile.get('scenes', []):
        print(f"\n{'='*60}")
        print(f"Testing Scene: {scene.get('name', 'Unknown')}")
        print(f"{'='*60}")

        for page_idx, page in enumerate(scene.get('pages', []), 1):
            print(f"\n  Page {page_idx}: {page.get('name', 'Unknown')}")
            print(f"  {'-'*56}")

            for button in page.get('buttons', []):
                action = button.get('action')
                if not action:
                    continue

                action_type = action.get('type')
                action_types.add(action_type)

                # Test if action type is supported
                button_label = button.get('label', 'Unknown')
                print(f"    Button: {button_label:20s} | Type: {action_type:20s}", end=' ')

                if action_type not in executor.ACTION_CLASSES:
                    print("❌ UNSUPPORTED")
                    test_results[f"{scene['name']}/{page['name']}/{button_label}"] = {
                        'type': action_type,
                        'status': 'UNSUPPORTED',
                        'error': f'Action type {action_type} not in executor'
                    }
                else:
                    try:
                        # Create action instance to validate
                        action_class = executor.ACTION_CLASSES[action_type]
                        action_instance = action_class(action.get('config', {}))

                        if action_instance.validate():
                            print("✅ VALID")
                            test_results[f"{scene['name']}/{page['name']}/{button_label}"] = {
                                'type': action_type,
                                'status': 'VALID'
                            }
                        else:
                            print("⚠️  INVALID CONFIG")
                            test_results[f"{scene['name']}/{page['name']}/{button_label}"] = {
                                'type': action_type,
                                'status': 'INVALID',
                                'error': 'Validation failed'
                            }
                    except Exception as e:
                        print(f"❌ ERROR: {str(e)}")
                        test_results[f"{scene['name']}/{page['name']}/{button_label}"] = {
                            'type': action_type,
                            'status': 'ERROR',
                            'error': str(e)
                        }

    # Print summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total buttons tested: {len(test_results)}")
    print(f"Unique action types: {len(action_types)}")
    print(f"Action types used: {', '.join(sorted(action_types))}")

    valid = sum(1 for r in test_results.values() if r['status'] == 'VALID')
    invalid = sum(1 for r in test_results.values() if r['status'] == 'INVALID')
    unsupported = sum(1 for r in test_results.values() if r['status'] == 'UNSUPPORTED')
    errors = sum(1 for r in test_results.values() if r['status'] == 'ERROR')

    print(f"\nResults:")
    print(f"  ✅ Valid:       {valid}")
    print(f"  ⚠️  Invalid:     {invalid}")
    print(f"  ❌ Unsupported: {unsupported}")
    print(f"  ❌ Errors:      {errors}")

    # Show details of problematic actions
    problems = {k: v for k, v in test_results.items() if v['status'] != 'VALID'}
    if problems:
        print(f"\n{'='*60}")
        print("ISSUES FOUND")
        print(f"{'='*60}")
        for name, result in problems.items():
            print(f"\n{name}")
            print(f"  Type: {result['type']}")
            print(f"  Status: {result['status']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")

    return len(problems) == 0


if __name__ == '__main__':
    success = test_action_types()
    exit(0 if success else 1)
