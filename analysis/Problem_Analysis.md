# Problem Analysis

## Operational Context

This project addresses staff scheduling for a healthcare/emergency services organization operating 7 days a week. The team consists of 5 employees with different contract types (full-time 38h/week, part-time 28h/week) who must cover morning and afternoon shifts daily, with optional night shifts on selected days.

The organization relies on a mix of permanent staff and external volunteers ("Expert Volunteers") to ensure full coverage. The goal is to minimize volunteer dependency while maintaining fair workload distribution among employees.

## Why Scheduling is Hard

Staff scheduling in healthcare is a classic constraint satisfaction problem. Several factors make it challenging:

**Hard constraints (must be satisfied):**
- Each person works at most one shift per day
- Weekly hours cannot exceed the contract limit
- Rest is mandatory after a night shift
- Only designated employees can work Sundays
- Only designated employees can work nights
- Minimum coverage must be met for each shift

**Soft constraints (should be optimized):**
- Fair distribution of morning vs. afternoon shifts
- Fair distribution of weekend work
- Balanced total hours across employees
- Limiting consecutive work days

Manual scheduling becomes impractical when:
- The planning horizon extends to 5 weeks
- Multiple constraint types interact
- Management wants to compare different staffing scenarios
- The schedule needs frequent regeneration

## What the Tool Outputs

The app produces a complete 5-week roster with:

1. **Calendar view**: Daily assignments by shift type (morning, afternoon, optional night)
2. **Coverage analysis**: Identifies shifts that require external volunteers
3. **Fairness metrics**: Hours worked, shift type distribution, weekend count per person
4. **Scenario comparison**: Side-by-side view of different staffing configurations

**Primary users:**
- Operations managers planning monthly rosters
- HR evaluating the impact of hiring decisions
- Team leads checking workload balance

## Scenario Simulation

A key feature is the ability to simulate hiring scenarios:

| Scenario | Description |
|----------|-------------|
| A - Current staff | Baseline with existing 5 employees |
| B - Add part-timer (28h) | What if we hire a part-time employee? |
| C - Add full-timer (38h) | What if we hire a full-time employee? |

The app generates all scenarios simultaneously and highlights which one minimizes volunteer dependency. This supports data-driven hiring decisions.

## Algorithm Approach

The scheduler uses a **greedy heuristic with weighted randomization**:

1. For each shift slot (in priority order: night → morning → afternoon)
2. Find all eligible candidates (respecting hard constraints)
3. Score candidates based on:
   - Hours deficit (who has worked less gets priority)
   - Shift type balance (who has fewer morning shifts gets priority for mornings)
   - Weekend balance (who has fewer Sundays gets priority)
4. Select from top-K candidates using weighted random choice (controlled by randomness parameter)

This approach:
- Runs in milliseconds (no optimization solver needed)
- Produces reasonable schedules that respect all constraints
- Allows variation when regenerating (useful for manual fine-tuning)

## Limitations

**This is a heuristic, not an optimal solver.**

The algorithm does not guarantee the mathematically optimal solution. For small teams (5-8 people) and 5-week horizons, the greedy approach produces good results, but:

- It may not find a valid schedule even when one exists (rare edge cases)
- Fairness metrics may not be perfectly optimal
- Complex constraint combinations may require manual adjustment

For organizations needing proven optimal solutions, a constraint programming (CP) or mixed-integer programming (MIP) approach would be more appropriate, at the cost of longer computation time and more complex implementation.

**Practical note:** In real-world use, "good enough" schedules with manual tweaks often outperform theoretically optimal ones that ignore soft human factors (personal preferences, informal agreements, etc.).

## Future Improvements

Potential enhancements not currently implemented:
- Employee preference input (preferred days off, shift preferences)
- Vacation and sick leave handling
- Multi-location support
- Historical data analysis for demand forecasting
- Integration with HR systems
