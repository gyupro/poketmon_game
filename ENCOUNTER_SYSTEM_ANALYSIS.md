# Pokemon Encounter System Analysis

## Issue Summary
The encounter system was not triggering wild Pokemon encounters when walking in tall grass.

## Root Cause
The issue was that **Pallet Town doesn't have wild Pokemon encounters** - this is by design. The encounter system only works in areas that have encounter tables defined.

## Areas with Wild Pokemon Encounters
The following areas have encounter tables:
- route_1 (12% base rate)
- viridian_forest (15% base rate)
- mt_moon (12% base rate)
- route_25 (10% base rate)
- cerulean_cave (15% base rate)
- safari_zone (20% base rate)
- victory_road (10% base rate)
- power_plant (12% base rate)
- seafoam_islands (10% base rate)
- faraway_island (5% base rate - Mew)

## How the Encounter System Works

1. **Tile Detection**: Only `TALL_GRASS` tiles trigger encounters
2. **Movement Requirement**: Player must move to a NEW tile position
3. **Step Tracking**: Consecutive steps in grass increase encounter chance
4. **Rate Calculation**: 
   - Base rate (10-20% depending on area)
   - Step bonus (up to +15%)
   - Time of day modifier (+10% morning, +20% night)
   - Chain bonus (up to +10%)
   - Maximum cap: 45%

## Solution
Players need to **leave Pallet Town and go to Route 1** (or other routes) to encounter wild Pokemon. This is consistent with the original Pokemon games where towns don't have wild encounters.

## Test Coverage
Created comprehensive tests in `/tests/test_encounters.py` that verify:
- Base encounter rates
- Step bonus mechanics
- Time of day modifiers
- Grass tile detection
- World integration

All tests are passing ✓