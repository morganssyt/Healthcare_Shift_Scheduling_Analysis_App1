# Constraints and Assumptions

This document details the rules and parameters used by the scheduling algorithm.

## Shift Definitions

| Shift | Hours | Days |
|-------|-------|------|
| Morning | 7:00 - 14:00 (7h) | Mon-Sun |
| Afternoon | 14:00 - 21:00 (7h) | Mon-Sun |
| Night | 21:00 - 7:00 (10h counted as 7h for simplicity) | Configurable |

**Note:** All shifts are counted as 7 hours for scheduling purposes, regardless of actual duration.

## Coverage Requirements

### Monday to Saturday

| Shift | Minimum staff |
|-------|---------------|
| Morning | 2 (configurable: 1-5) |
| Afternoon | 2 (configurable: 1-5) |
| Night | 1 (if enabled) |

### Sunday

| Shift | Minimum staff |
|-------|---------------|
| Morning | 1 (configurable: 0-3) |
| Afternoon | 0 (configurable: 0-3) |
| Night | Same as weekdays if enabled |

Sunday coverage is intentionally lighter. Only employees marked as "can work Sunday" are eligible.

## Rest Rules

### After Night Shift
If an employee works a night shift:
- **Next day**: Mandatory rest (no shifts)
- **Day after**: Returns to work (typically afternoon)

This prevents fatigue accumulation and complies with labor regulations.

### Maximum Consecutive Days
- Default: 6 days maximum
- Configurable: 3-7 days
- After reaching the limit, the employee is excluded from scheduling until a rest day occurs

## Hour Limits

### Weekly Contracts

| Contract type | Weekly hours | 5-week total |
|---------------|--------------|--------------|
| Full-time (FT) | 38h | 190h |
| Part-time (PT) | 28h | 140h |
| Custom | 1-48h | Varies |

### Enforcement
- The scheduler tracks hours per week per employee
- An employee cannot be assigned a shift if it would exceed their weekly limit
- Target is to match contracted hours exactly (minimize deviation)

## Volunteer Fallback Behavior

When no eligible employee is available for a shift:

1. **If "Expert Volunteer" is enabled (default):**
   - The slot is assigned to "Volontario esperto" (Expert Volunteer)
   - This is tracked and reported in the summary
   - PDF/Excel exports highlight these slots

2. **If "Expert Volunteer" is disabled:**
   - The slot is marked as "SCOPERTO" (Uncovered)
   - This triggers a warning in the UI
   - Indicates a staffing problem that requires attention

## Randomness and Repeatability

### Randomness Parameter (0.0 - 1.0)

Controls how deterministic the scheduling is:

| Value | Behavior |
|-------|----------|
| 0.0 | Always picks the mathematically best candidate |
| 0.3 | Slight variation, mostly consistent (default) |
| 0.5 | Moderate variation, good for exploring alternatives |
| 1.0 | High variation, useful for manual comparison |

**Technical implementation:**
- Top-K candidates are selected (K = max(3, staff_size/2))
- Selection uses weighted random choice based on scores
- Temperature parameter scales with randomness value

### Seed

- If "Use fixed seed" is enabled: same inputs always produce same output
- If disabled: each generation uses a new random seed
- Seed value is displayed after generation for reference
- Useful for reproducing a specific schedule variant

## Scheduling Priority

Shifts are processed in this order:
1. Night shifts (ensures rest rule can be applied)
2. Morning shifts
3. Afternoon shifts

Within each category, days are processed chronologically (Monday → Sunday), with optional shuffling when randomness > 0.5.

## Fairness Scoring

When selecting a candidate, the algorithm scores based on:

| Factor | Weight | Goal |
|--------|--------|------|
| Total hours deficit | High | Balance overall workload |
| Weekly hours deficit | Medium-high | Balance within each week |
| Shift type count | Medium | Rotate morning/afternoon fairly |
| Sunday count | Medium | Distribute weekend work |
| Consecutive days | Penalty | Avoid burnout |

Lower score = better candidate. Top candidates are then subject to weighted random selection.

## Input Assumptions

The app assumes:
- Staff data is accurate (names, hours, availability flags)
- Start date is a Monday (auto-corrected if not)
- Planning horizon is fixed at 5 weeks
- All employees are available for the full period (no vacation handling)
- Night shift capability and Sunday availability are binary (yes/no)

## Output Guarantees

The algorithm guarantees:
- No hard constraint violations (hours, rest rules, availability)
- All shifts are assigned (either to staff, volunteer, or marked uncovered)
- Metrics are accurately calculated

The algorithm does NOT guarantee:
- Perfect fairness (heuristic approach)
- Optimal volunteer minimization
- Employee preferences (not implemented)
