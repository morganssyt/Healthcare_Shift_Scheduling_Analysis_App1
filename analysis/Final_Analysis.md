# Final Analysis - Healthcare Shift Scheduling (5 weeks)

## Operational Context

**Period**: 5 weeks (February 3 - March 9, 2025)

**Daily shifts**:
- Morning: 07:00 - 14:00 (7 hours)
- Afternoon: 14:00 - 21:00 (7 hours)

**Staffing requirements**:
- Monday-Saturday: 2 employees morning + 2 employees afternoon
- Sunday: 1 employee morning only

**Available staff**:
- Francesco La Rosa (38h/week)
- Enzo La Gamba (38h/week)
- Thomas Ardissone (28h/week, part-time)
- Giacomo Rosso (38h/week)
- Daniele Ramella (38h/week)

**Contractual constraints**:
- Maximum 1 shift per day per employee
- Maximum 6 consecutive working days
- Thomas: maximum 28 hours/week

---

## Final Scenario Decision

### CHOSEN SCENARIO: +1 FULL-TIME EMPLOYEE

**Main rationale**: the base scenario leaves **5 Sundays uncovered** (92.3% coverage), making the plan operationally unusable. The scenario with an additional employee guarantees **100% complete coverage** of all required positions.

### Scenario Comparison

| Metric | Base Scenario | +1 Scenario |
|--------|---------------|-------------|
| Required hours (5 weeks) | 875h | 875h |
| Available hours | 900h | 1090h |
| Surplus/Deficit | +25h | +215h |
| Coverage % | 102.9% | 124.6% |
| Uncovered positions | 5 Sundays | 0 |
| Coverage rate | 92.3% | 100.0% |

**Conclusion**: the theoretical capacity of the base scenario is sufficient (+25h), but operational constraints (consecutive days, equitable distribution) make it impossible to cover all positions. The additional 190h surplus in the +1 scenario provides the necessary flexibility.

---

## Individual KPIs

### Per-Employee Metrics Summary

| Employee | Target (h/week) | Total Hours | Hours/Week | Deviation | Weekends Worked | Max Consecutive Days |
|----------|----------------|-------------|------------|-----------|-----------------|---------------------|
| Francesco La Rosa | 38h | 175h | 35.0h | **-3.0h** | 5 | 3 |
| Enzo La Gamba | 38h | 175h | 35.0h | **-3.0h** | 5 | 3 |
| Thomas Ardissone | 28h | 105h | 21.0h | **-7.0h** | 5 | 2 |
| Giacomo Rosso | 38h | 140h | 28.0h | **-10.0h** | 0 | 2 |
| Daniele Ramella | 38h | 140h | 28.0h | **-10.0h** | 5 | 2 |

### Detailed Analysis

**Hours worked**:
- All employees work **below** their contractual target
- Francesco and Enzo are the most utilized (35h/week, -8% from target)
- Thomas is underutilized by 25% (21h vs 28h target)
- Giacomo and Daniele are underutilized by 26% (28h vs 38h target)

**Weekend distribution**:
- **Critical imbalance**: 4 employees work all 5 weekends, Giacomo works none
- Theoretical fair average: 3 weekends each
- Impact: potential discontent and perception of inequity

**Consecutive days**:
- All employees easily comply with the constraint (max 3 actual days vs 6-day limit)
- Good distribution of rest days
- No burnout risk from excessive consecutive days

---

## Contract Compliance

### Regulatory Conformity

- **COMPLIANT**: No employee exceeds weekly contractual limit
- **COMPLIANT**: Thomas works within part-time limit (21h < 28h)
- **COMPLIANT**: Maximum consecutive days constraint (3 < 6)
- **COMPLIANT**: Maximum 1 shift/day per employee

- **ATTENTION**: Generalized underutilization indicates allocation inefficiency

### Contractual Considerations

The plan is **legally compliant** but has room for improvement in utilizing available capacity. The underutilization could be seen as:
- **Positive**: flexibility to cover absences/contingencies
- **Negative**: cost of the 6th employee not fully justified

---

## Residual Risks and Limitations

### Identified Operational Risks

1. **Weekend imbalance**:
   - Giacomo never works weekends -> possible perception of favoritism
   - The other 4 work every weekend -> possible burnout/fatigue
   - Impact: team morale, turnover

2. **Resource underutilization**:
   - 735h worked vs 900h available (base scenario)
   - Efficiency: 81.7% of capacity utilized
   - Impact: opportunity cost, justification for 6th employee

3. **Scheduler rigidity**:
   - Current algorithm does not optimize for equitable distribution
   - Does not consider individual preferences
   - Impact: technically valid but operationally rigid plan

4. **Single-plan dependency**:
   - No Plan B if the 6th employee is unavailable
   - Base scenario unusable (uncovered Sundays)
   - Impact: operational fragility

### Technical Limitations

- The greedy scheduler does not guarantee an optimal solution
- Does not consider "soft" constraints (preferences, weekend equity)
- Does not handle vacation requests or unavailability
- Fixed weekend distribution, not balanced

---

## Recommendations for Operations Manager

### Immediate Recommendations (implement now)

1. **Hire the 6th employee**: this is the only option to guarantee 100% complete coverage

2. **Communicate metrics to the team**:
   - Share hours and weekend distribution
   - Explain reasons for imbalance (if unavoidable)
   - Collect feedback on weekend preferences

3. **Monitor satisfaction**:
   - Focus on Giacomo (0 weekends) and the 4 who always work weekends
   - Evaluate more equitable weekend rotation in subsequent periods

### Medium-term Recommendations (next cycles)

4. **Improve the scheduling algorithm**:
   - Implement optimization with "soft" constraints (weekend equity)
   - Consider individual preferences where possible
   - Better balance the utilization of available hours

5. **Analyze actual staffing needs**:
   - Verify if the 6th employee is truly needed long-term
   - Evaluate if optimizing the base scheduler can cover Sundays
   - Consider flexible contracts (e.g., weekend-only)

6. **Create contingency plans**:
   - Develop backup scenario if 6th employee is unavailable
   - Identify possibilities for spot overtime vs. permanent hire

### Long-term Recommendations (strategic)

7. **Invest in workforce optimization**:
   - Professional healthcare scheduling tools
   - Integration with leave/permission system
   - Complete process automation

8. **Review contracts**:
   - Evaluate optimal full-time/part-time mix
   - Consider weekend-specific contracts (premium pay)
   - Contractual flexibility for peaks/valleys

---

## Executive Conclusions

### Summary

- **The plan works**: covers all required positions
- **Respects contracts**: no regulatory violations
- **Not optimal**: weekend imbalance and underutilization
- **Base scenario inadequate**: leaves 5 Sundays uncovered

### The Verdict

**Recommendation**: proceed with the +1 employee scenario, accepting current compromises, but with commitment to:
1. Improve weekend equity in future cycles
2. Optimize the algorithm to better utilize capacity
3. Monitor the sustainability of the 6th employee in the medium term

The scenario guarantees **operational continuity** and **regulatory compliance**, fundamental in healthcare settings, even if it presents margins for economic and equitable optimization.

---

## Generated Files for In-depth Analysis

**Data**:
- `output/schedule_final.csv` - Detailed shift schedule (125 assignments)
- `output/kpi_final.csv` - Individual metrics per employee

**Decision charts**:
- `figures/hours_vs_target.png` - Comparison of actual hours vs contractual target
- `figures/weekend_distribution.png` - Weekend distribution (highlights imbalance)
- `figures/calendar_heatmap.png` - Complete 5-week calendar view
- `figures/consecutive_days.png` - Verification of consecutive days constraint compliance

**Capacity reports** (from Day 1 and 2):
- `output/capacity_summary.csv` - Scenario comparison
- `output/coverage_base.csv` / `coverage_plus1.csv` - Position coverage
- `output/weekly_capacity_analysis.csv` - Weekly analysis

---

*Analysis generated February 3, 2026 for healthcare shift scheduling portfolio project.*
