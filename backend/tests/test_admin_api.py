"""
Tests for Admin Configuration API Endpoints

Tests all 4 admin endpoints:
- GET /admin/config - Get current configuration
- POST /admin/config/thresholds - Update signal thresholds
- POST /admin/config/weights - Update source weights
- POST /admin/config/windows - Update time windows
"""

import sys
from pathlib import Path
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.admin import (
    get_config, update_thresholds, update_weights, update_windows,
    get_pairs, get_sources, health,
    ThresholdUpdate, WeightUpdate, WindowsUpdate
)


async def test_get_config():
    """Test GET /admin/config endpoint."""
    print("\n✅ Testing: GET /admin/config")
    
    config = await get_config()
    
    assert "signal_thresholds" in config
    assert "source_weights" in config
    assert "time_windows" in config
    assert "confidence_threshold" in config
    
    assert "EUR/USD" in config["signal_thresholds"]
    assert config["signal_thresholds"]["EUR/USD"]["buy"] == 60
    assert config["signal_thresholds"]["EUR/USD"]["sell"] == 40
    
    print(f"   ✓ Config retrieved: {len(config)} sections")
    print(f"   ✓ Pairs: {list(config['signal_thresholds'].keys())}")
    print(f"   ✓ Sources: {list(config['source_weights'].keys())}")


async def test_update_thresholds():
    """Test POST /admin/config/thresholds endpoint."""
    print("\n✅ Testing: POST /admin/config/thresholds")
    
    # Valid update
    update = ThresholdUpdate(pair="EUR/USD", buy_threshold=70, sell_threshold=35)
    result = await update_thresholds(update)
    
    assert result["pair"] == "EUR/USD"
    assert result["thresholds"]["buy"] == 70
    assert result["thresholds"]["sell"] == 35
    assert "updated" in result["message"].lower()
    
    print(f"   ✓ Updated EUR/USD thresholds: BUY=70, SELL=35")
    
    # Verify update persisted
    config = await get_config()
    assert config["signal_thresholds"]["EUR/USD"]["buy"] == 70
    print(f"   ✓ Update persisted in configuration")
    
    # Reset
    reset = ThresholdUpdate(pair="EUR/USD", buy_threshold=60, sell_threshold=40)
    await update_thresholds(reset)
    print(f"   ✓ Reset EUR/USD to original values")


async def test_update_thresholds_invalid():
    """Test invalid threshold updates."""
    print("\n✅ Testing: POST /admin/config/thresholds (invalid)")
    
    # Invalid pair
    try:
        update = ThresholdUpdate(pair="XXX/YYY", buy_threshold=70, sell_threshold=35)
        await update_thresholds(update)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "not found" in str(e).lower()
        print(f"   ✓ Invalid pair rejected: {str(e)[:50]}...")
    
    # Invalid thresholds (buy <= sell)
    try:
        update = ThresholdUpdate(pair="EUR/USD", buy_threshold=30, sell_threshold=70)
        await update_thresholds(update)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "greater" in str(e).lower()
        print(f"   ✓ Invalid thresholds rejected: {str(e)[:50]}...")


async def test_update_weights():
    """Test POST /admin/config/weights endpoint."""
    print("\n✅ Testing: POST /admin/config/weights")
    
    # Valid update
    update = WeightUpdate(source="newsapi", weight=1.5)
    result = await update_weights(update)
    
    assert result["source"] == "newsapi"
    assert result["weight"] == 1.5
    assert "updated" in result["message"].lower()
    
    print(f"   ✓ Updated newsapi weight: 1.5")
    
    # Verify update persisted
    config = await get_config()
    assert config["source_weights"]["newsapi"] == 1.5
    print(f"   ✓ Update persisted in configuration")
    
    # Reset
    reset = WeightUpdate(source="newsapi", weight=1.0)
    await update_weights(reset)
    print(f"   ✓ Reset newsapi weight to original")


async def test_update_weights_invalid():
    """Test invalid weight updates."""
    print("\n✅ Testing: POST /admin/config/weights (invalid)")
    
    # Invalid source
    try:
        update = WeightUpdate(source="invalid_source", weight=1.0)
        await update_weights(update)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "not found" in str(e).lower()
        print(f"   ✓ Invalid source rejected: {str(e)[:50]}...")


async def test_update_windows():
    """Test POST /admin/config/windows endpoint."""
    print("\n✅ Testing: POST /admin/config/windows")
    
    # Valid update
    new_windows = [600, 1800, 7200, 28800]  # 10m, 30m, 2h, 8h
    update = WindowsUpdate(windows=new_windows)
    result = await update_windows(update)
    
    assert result["windows"] == new_windows
    assert "updated" in result["message"].lower()
    
    print(f"   ✓ Updated time windows: {new_windows}")
    
    # Verify update persisted
    config = await get_config()
    assert config["time_windows"] == new_windows
    print(f"   ✓ Update persisted in configuration")
    
    # Reset to original
    reset = WindowsUpdate(windows=[900, 3600, 14400])
    await update_windows(reset)
    print(f"   ✓ Reset windows to original [900, 3600, 14400]")


async def test_update_windows_invalid():
    """Test invalid window updates."""
    print("\n✅ Testing: POST /admin/config/windows (invalid)")
    
    # Windows out of order
    try:
        update = WindowsUpdate(windows=[14400, 3600, 900])  # Descending order
        await update_windows(update)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "ascending" in str(e).lower()
        print(f"   ✓ Out-of-order windows rejected: {str(e)[:50]}...")
    
    # Empty windows
    try:
        update = WindowsUpdate(windows=[])
        await update_windows(update)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "required" in str(e).lower()
        print(f"   ✓ Empty windows rejected: {str(e)[:50]}...")
    
    # Negative window
    try:
        update = WindowsUpdate(windows=[900, -1000])
        await update_windows(update)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "positive" in str(e).lower()
        print(f"   ✓ Negative window rejected: {str(e)[:50]}...")


async def test_get_pairs():
    """Test GET /admin/config/pairs endpoint."""
    print("\n✅ Testing: GET /admin/config/pairs")
    
    result = await get_pairs()
    
    assert "pairs" in result
    assert len(result["pairs"]) > 0
    assert "EUR/USD" in result["pairs"]
    
    print(f"   ✓ Retrieved {len(result['pairs'])} currency pairs: {result['pairs']}")


async def test_get_sources():
    """Test GET /admin/config/sources endpoint."""
    print("\n✅ Testing: GET /admin/config/sources")
    
    result = await get_sources()
    
    assert "sources" in result
    assert len(result["sources"]) > 0
    assert "newsapi" in result["sources"]
    
    print(f"   ✓ Retrieved {len(result['sources'])} sources: {result['sources']}")


async def test_health():
    """Test GET /admin/health endpoint."""
    print("\n✅ Testing: GET /admin/health")
    
    result = await health()
    
    assert result["status"] == "healthy"
    assert result["service"] == "admin-api"
    
    print(f"   ✓ Health check passed: {result}")


async def run_all_tests():
    """Run all admin API tests."""
    print("\n" + "="*70)
    print("🧪 PipPulse AI - Admin API Tests")
    print("="*70)
    
    tests = [
        test_get_config,
        test_get_pairs,
        test_get_sources,
        test_health,
        test_update_thresholds,
        test_update_thresholds_invalid,
        test_update_weights,
        test_update_weights_invalid,
        test_update_windows,
        test_update_windows_invalid,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"   ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("🎉 All admin API tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
