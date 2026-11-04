# Mathematical Model — benchmark-v1

## Scope
Deterministic, single-product, single-period, continuous-flow, three-echelon
supply chain: suppliers → warehouses → customers. All quantities are in units
and all monetary values are INR.

## Sets
- `I`: suppliers
- `K`: warehouses
- `J`: customers
- `A`: feasible supplier-to-warehouse arcs
- `B`: feasible warehouse-to-customer arcs

## Parameters
- `p_i`: supplier purchase price (INR/unit)
- `a_ik`: inbound transport cost (INR/unit)
- `b_kj`: outbound transport cost (INR/unit)
- `h_k`: warehouse handling cost (INR/unit)
- `s_i`: supplier capacity (units)
- `C_k`: warehouse throughput/storage capacity (units)
- `d_j`: customer demand (units)
- `U_ik`, `V_kj`: inbound and outbound route capacities (units)
- `l_ik`, `m_kj`: inbound and outbound lead times (hours)
- `e_ik`, `f_kj`: emissions factors (kg CO2e/unit)

## Decision variables
- `x_ik >= 0`: units shipped from supplier `i` to warehouse `k`
- `y_kj >= 0`: units shipped from warehouse `k` to customer `j`

## Objective
Minimise:
```
Z = Σ(i,k) (p_i + a_ik) x_ik
    + Σ(k,j) (b_kj + h_k) y_kj
```

## Constraints
Supplier capacity:
```
Σ(k:(i,k)∈A) x_ik <= s_i                         for each i
```
Warehouse flow conservation:
```
Σ(i:(i,k)∈A) x_ik = Σ(j:(k,j)∈B) y_kj           for each k
```
Warehouse capacity:
```
Σ(i:(i,k)∈A) x_ik <= C_k                       for each k
```
Demand fulfilment:
```
Σ(k:(k,j)∈B) y_kj = d_j                        for each j
```
Route capacities:
```
x_ik <= U_ik; y_kj <= V_kj
```
Delivery windows:
```
y_kj = 0 when m_kj > maximum_delivery_time_j
```
Non-negativity:
```
x_ik, y_kj >= 0
```

## Benchmark reference result
- Solver status: Optimal
- Objective: INR 22,260
- Procurement: INR 16,620
- Inbound transport: INR 2,040
- Outbound transport: INR 2,100
- Handling: INR 1,500
- Total demand: 420 units
- Outbound weighted average lead time: 14.047619 hours
- Estimated transport emissions: 1,288 kg CO2e

## Important modelling qualifications
1. The model is a one-period flow model; it does not model inventory carried
   between periods.
2. Warehouse capacity is modelled as throughput in this benchmark because
   all inbound flow is assumed to leave in the same period. A true peak
   storage constraint requires time-phased inventory variables.
3. Delivery windows are enforced by excluding routes that exceed a
   customer's maximum allowed outbound lead time. Inbound lead time is
   recorded but not included in the customer delivery promise in benchmark-v1.
4. Emissions factors are hypothetical benchmark inputs, not measured
   company-specific emission factors.
5. The benchmark is a synthetic teaching and software-validation dataset.
   It must not be represented as real company operational data.
6. The objective uses continuous shipment quantities. Integer packs,
   minimum order sizes and fixed vehicle costs require a MILP extension.
